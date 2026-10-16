'use strict';

// Independent criterion checker. Run from an upstream checkout with Node 24.
const assert = require('node:assert/strict');
const { Readable } = require('node:stream');
const { ReadableStream } = require('node:stream/web');
const { File } = require('node:buffer');
const csv = require(process.cwd() + '/index.js');
global.ReadableStream = ReadableStream;
global.File = File;

function configure(delimiter = ',', extra = {}) {
    csv.fieldDelimiter(delimiter).supportQuotedField(true)
        .formatValueByType(false).trimHeaderFieldWhiteSpace(false)
        .indexHeader(0).ignoreColumnIndexes([]).parseSubArray('*', '|')
        .mapRows(row => row);
    if (extra.typed) csv.formatValueByType(true).trimHeaderFieldWhiteSpace(true)
        .ignoreColumnIndexes([2]).indexHeader(1)
        .mapRows((row, index) => index === 1 ? null : { ...row, index });
    if (extra.unquoted) csv.supportQuotedField(false);
}

function web(chunks, binary) {
    return new ReadableStream({ start(controller) {
        for (const chunk of chunks) controller.enqueue(binary ? Buffer.from(chunk) : chunk);
        controller.close();
    } });
}

async function parse(adapter, chunks) {
    if (adapter === 'node-text') return csv.getJsonFromStreamAsync(Readable.from(chunks));
    if (adapter === 'web-text' || adapter === 'web-bytes') {
        return csv.browser.getJsonFromStreamAsync(web(chunks, adapter === 'web-bytes'));
    }
    const file = new File([], 'criterion.csv');
    Object.defineProperty(file, 'stream', { value: () => web(chunks, false) });
    const received = [];
    let completed = 0;
    let all;
    const errors = [];
    await csv.browser.getJsonFromFileStreamingAsyncWithCallback(file, {
        chunkSize: 2,
        onChunk(rows, processed, total) {
            received.push(...rows);
            assert.equal(processed, received.length);
            if (total !== null) assert.equal(total, received.length);
        },
        onComplete(rows) { completed++; all = rows; },
        onError(error) { errors.push(error.message); },
    });
    assert.deepEqual(errors, []);
    assert.equal(completed, 1);
    assert.deepEqual(all, received);
    return received;
}

const quote = value => '"' + value.replaceAll('"', '""') + '"';
const values = ['', '"', '""', 'a,b;c', 'a\nb', 'a\rb', 'a\r\nb', '\n', '\r\n', ' ends '];
const cases = [];
for (const delimiter of [',', ';', '\t']) {
    for (const ending of ['\n', '\r\n', '\r']) {
        for (const terminated of [true, false]) {
            const headers = ['id', 'note'];
            const rows = values.map((value, index) => [String(index), value]);
            cases.push({
                name: JSON.stringify({ delimiter, ending, terminated }), delimiter,
                text: [headers, ...rows].map(row => row.map(quote).join(delimiter)).join(ending) + (terminated ? ending : ''),
                expected: rows.map(row => ({ id: row[0], note: row[1] })),
            });
        }
    }
}
cases.push({
    name: 'typed-mapped-filtered-ignored-subarrays-header-offset', delimiter: ';', typed: true,
    text: 'preamble\n' + [
        [' id ', 'active', 'skip', 'items', 'note'],
        ['01', 'TRUE', 'omit', '*1|2.5|false*', 'a;\nb"c'],
        ['8', 'false', 'omit', '*3*', 'filtered'],
        ['-2', 'false', 'omit', '*x|y*', 'last\r\nrow'],
    ].map(row => row.map(quote).join(';')).join('\n'),
    expected: [
        { id: '01', active: true, items: [1, 2.5, false], note: 'a;\nb"c', index: 0 },
        { id: -2, active: false, items: ['x', 'y'], note: 'last\r\nrow', index: 2 },
    ],
});
cases.push({ name: 'unquoted-control', delimiter: ',', unquoted: true,
    text: 'id,note\n1,hello\n2,world', expected: [{ id: '1', note: 'hello' }, { id: '2', note: 'world' }] });
cases.push({ name: 'unicode-decoded-text', delimiter: ',', text: 'id,note\n1,"éλ😀\nend"',
    expected: [{ id: '1', note: 'éλ😀\nend' }], unicode: true });

function partitions(text) {
    const result = [[text], text.split(''), ['', text, '']];
    for (let i = 1; i < text.length; i++) result.push([text.slice(0, i), text.slice(i)]);
    result.push(text.split('').flatMap(char => ['', char]));
    return result;
}

(async () => {
    let total = 0;
    let failures = 0;
    const examples = [];
    for (const entry of cases) {
        const adapters = ['node-text', 'web-text', 'callback-text', ...(entry.unicode ? [] : ['web-bytes'])];
        for (const adapter of adapters) {
            for (const chunks of partitions(entry.text)) {
                total++;
                configure(entry.delimiter, entry);
                try {
                    assert.deepEqual(await parse(adapter, chunks), entry.expected);
                } catch (error) {
                    failures++;
                    if (examples.length < 4) examples.push({ case: entry.name, adapter,
                        chunks: chunks.length, firstChunkLength: chunks[0].length,
                        error: error.message.split('\n')[0] });
                }
            }
        }
    }
    console.log(JSON.stringify({ node: process.version, cases: cases.length, total, failures, examples }));

    // Probe an adjacent pre-existing boundary separately from the quoted-record claim.
    configure();
    csv.indexHeader(1);
    const text = 'preamble\r\n"id",note\r\n1,ok\r\n';
    const unsplit = await parse('node-text', [text]);
    const splitBetweenRecordCRLF = await parse('node-text', ['preamble\r', '\n"id",note\r\n1,ok\r\n']);
    console.log(JSON.stringify({ observation: 'CRLF record separator before a nonzero header index',
        unsplit, splitBetweenRecordCRLF }));
    process.exitCode = failures ? 1 : 0;
})().catch(error => { console.error(error); process.exitCode = 2; });
