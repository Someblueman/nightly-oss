'use strict';

// Derived only from claim.md and baseline public API documentation, before
// inspecting candidate production code or tests. Run from the package root.
const assert = require('node:assert/strict');
const path = require('node:path');
const { Readable } = require('node:stream');

const fixtures = [
  { name: 'offset-one', header: 1, text: 'preamble\r\nid,note\r\n1,ok\r\n', rows: [{ id: '1', note: 'ok' }] },
  { name: 'two-blank-preamble-records', header: 2, text: '\r\n\r\nid,note\r\n2,ok\r\n', rows: [{ id: '2', note: 'ok' }] },
  { name: 'default-header', text: 'id,note\r\n3,ok\r\n4,last\r\n', rows: [{ id: '3', note: 'ok' }, { id: '4', note: 'last' }] },
  { name: 'mixed-preamble-records', header: 3, text: '\r\npreface\r\n\r\nid,note\r\n5,blank\r\n', rows: [{ id: '5', note: 'blank' }] },
  { name: 'standalone-separators', header: 1, text: 'preamble\rid,note\n6,mix\r7,last\r', rows: [{ id: '6', note: 'mix' }, { id: '7', note: 'last' }] },
  { name: 'embedded-newlines-and-escaped-quotes', header: 1, text: 'preamble\r\nid,note\r\n8,"first\r\nsecond""quoted""\rthird\nfourth"\r\n', rows: [{ id: '8', note: 'first\r\nsecond"quoted"\rthird\nfourth' }] },
  { name: 'final-cr', text: 'id,note\r\n10,end\r', rows: [{ id: '10', note: 'end' }] },
  { name: 'quoted-eof', header: 1, text: 'preamble\r\nid,note\r\n11,"end"', rows: [{ id: '11', note: 'end' }] },
  { name: 'header-only', header: 1, text: 'preamble\r\nid,note\r\n', rows: [] },
  { name: 'format-and-map', header: 1, transform: true, text: 'preamble\r\nid,active,note\r\n12,true,keep\r\n13,false,drop\r\n', rows: [{ n: 12, active: true }] },
  { name: 'quotes-disabled', header: 1, quotes: false, text: 'preamble\r\nid,note\r\n14,plain\r\n', rows: [{ id: '14', note: 'plain' }] },
];

function freshApi(mode, fixture) {
  const packageRoot = process.cwd() + path.sep;
  for (const key of Object.keys(require.cache)) {
    if (key.startsWith(packageRoot)) delete require.cache[key];
  }
  const packageApi = require(path.join(process.cwd(), 'index.js'));
  const api = mode.startsWith('node-') ? packageApi : packageApi.browser;
  api.fieldDelimiter(',').supportQuotedField(fixture.quotes !== false);
  if (fixture.header !== undefined) api.indexHeader(fixture.header);
  if (fixture.transform) {
    api.formatValueByType().mapRows(row => row.active ? { n: row.id, active: row.active } : null);
  }
  return api;
}

function webStream(chunks) {
  return new ReadableStream({
    start(controller) {
      for (const chunk of chunks) controller.enqueue(new TextEncoder().encode(chunk));
      controller.close();
    },
  });
}

async function parse(mode, fixture, chunks) {
  const api = freshApi(mode, fixture);
  if (mode === 'node-text') return api.getJsonFromStreamAsync(Readable.from(chunks));
  if (mode === 'node-bytes') return api.getJsonFromStreamAsync(Readable.from(chunks.map(chunk => Buffer.from(chunk))));
  if (mode === 'web-bytes') return api.getJsonFromStreamAsync(webStream(chunks));
  class ChunkedFile extends File {
    stream() { return webStream(chunks); }
  }
  const file = new ChunkedFile([fixture.text], 'fixture.csv', { type: 'text/csv' });
  let complete;
  let callbackError;
  const callbackRows = [];
  await api.getJsonFromFileStreamingAsyncWithCallback(file, {
    chunkSize: 1,
    onChunk(rows) { callbackRows.push(...rows); },
    onComplete(rows) { complete = rows; },
    onError(error) { callbackError = error; },
  });
  if (callbackError) throw callbackError;
  assert.deepStrictEqual(complete, fixture.rows, 'onComplete result');
  assert.deepStrictEqual(callbackRows, fixture.rows, 'concatenated onChunk results');
  return complete;
}

function* deliveries(text) {
  yield ['unsplit', [text]];
  for (let cut = 1; cut < text.length; cut++) yield [`cut-${cut}`, [text.slice(0, cut), text.slice(cut)]];
  yield ['every-character', Array.from(text)];
  yield ['every-character-with-empty-chunks', Array.from(text).flatMap(char => [char, '', ''])];
}

(async () => {
  console.log(JSON.stringify({ node: process.version, checker: 'independent-public-api-split-matrix-v1', modes: ['node-text', 'node-bytes', 'web-bytes', 'file-callback'], realBrowser: false }));
  let total = 0;
  let failed = 0;
  let unsplitFailed = 0;
  const failureSamples = [];
  for (const fixture of fixtures) {
    for (const mode of ['node-text', 'node-bytes', 'web-bytes', 'file-callback']) {
      let groupTotal = 0;
      let groupFailed = 0;
      for (const [delivery, chunks] of deliveries(fixture.text)) {
        total++;
        groupTotal++;
        try {
          const rows = await parse(mode, fixture, chunks);
          assert.deepStrictEqual(rows, fixture.rows);
        } catch (error) {
          failed++;
          groupFailed++;
          if (delivery === 'unsplit') unsplitFailed++;
          if (failureSamples.length < 24) failureSamples.push({ fixture: fixture.name, mode, delivery, chunks, message: error.message });
        }
      }
      console.log(JSON.stringify({ fixture: fixture.name, mode, total: groupTotal, failed: groupFailed }));
    }
  }
  console.log(JSON.stringify({ total, passed: total - failed, failed, unsplitFailed, failureSamples }));
  process.exitCode = failed ? 1 : 0;
})().catch(error => { console.error(error); process.exitCode = 2; });
