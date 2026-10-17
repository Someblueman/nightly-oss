'use strict';

// Independent criterion review: explicit outputs plus every zero, one and two
// cut partition of each input. Run only with the trusted night.py container.
const assert = require('node:assert/strict');
const { Readable } = require('node:stream');
const { ReadableStream } = require('node:stream/web');
const { File } = require('node:buffer');
const csv = require('./');
global.ReadableStream = ReadableStream;
global.File = File;

const scenarios = [];
for (const separator of ['\r\n', '\r', '\n']) {
    for (const preamble of [[], ['p'], ['p', '']]) {
        for (const ending of ['', '\r', '\n', '\r\n']) {
            scenarios.push({
                name: `records-${JSON.stringify([separator, preamble, ending])}`,
                text: [...preamble, 'h,v', '1,x', '2,y'].join(separator) + ending,
                header: preamble.length,
                expected: [{ h: '1', v: 'x' }, { h: '2', v: 'y' }],
            });
        }
    }
}
scenarios.push(
    {
        name: 'mixed-endings-and-blank-preamble',
        text: 'p\r\n\rh,v\n1,x\r2,y\r\n', header: 2,
        expected: [{ h: '1', v: 'x' }, { h: '2', v: 'y' }],
    },
    {
        name: 'quoted-newlines-escaped-quotes-and-final-cr',
        text: 'p\r\n"h","v"\r\n"1","a\r\nb\rc\nd"\r\n"2","say ""x"""\r', header: 1,
        expected: [{ h: '1', v: 'a\r\nb\rc\nd' }, { h: '2', v: 'say "x"' }],
    },
    {
        name: 'empty-quoted-values',
        text: 'p\r\nh,v\r\n1,""\r\n2,""', header: 1,
        expected: [{ h: '1', v: '' }, { h: '2', v: '' }],
    },
    {
        name: 'plain-parser-mode',
        text: 'p\r\nh,v\r\n1,x\r\n2,y\r', header: 1, quoted: false,
        expected: [{ h: '1', v: 'x' }, { h: '2', v: 'y' }],
    },
    {
        name: 'conversion-mapping-filtering-ignore-and-blank-data',
        text: 'p\r\n h ,ignored,ok\r\n1,x,true\r\n\r\n2,y,false\r\n3,z,true\r', header: 1,
        typed: true, trim: true, ignored: [1],
        mapper: (row, index) => index === 1 ? null : { ...row, index },
        expected: [{ h: 1, ok: true, index: 0 }, { h: 3, ok: true, index: 2 }],
    },
    {
        name: 'semicolon-and-subarray',
        text: 'p\r\nh;v\r\n1;*2|3*\r\n2;*4|5*\r', header: 1,
        delimiter: ';', typed: true, subarray: true,
        expected: [{ h: 1, v: [2, 3] }, { h: 2, v: [4, 5] }],
    },
    { name: 'header-only-final-cr', text: 'h,v\r', header: 0, expected: [] },
    { name: 'blank-only-cr', text: '\r', header: 0, expected: [] },
    { name: 'empty-input', text: '', header: 0, expected: [] },
);

function configure(scenario) {
    csv.fieldDelimiter(scenario.delimiter || ',')
        .supportQuotedField(scenario.quoted !== false)
        .formatValueByType(!!scenario.typed)
        .trimHeaderFieldWhiteSpace(!!scenario.trim)
        .indexHeader(scenario.header)
        .ignoreColumnIndexes(scenario.ignored || [])
        .parseSubArray(scenario.subarray ? '*' : '', '|')
        .mapRows(scenario.mapper || (row => row));
}

function* partitions(text) {
    yield { kind: 'unsplit', chunks: [text] };
    for (let first = 0; first <= text.length; first++) {
        for (let second = first; second <= text.length; second++) {
            yield {
                kind: `cuts-${first}-${second}`,
                chunks: [text.slice(0, first), text.slice(first, second), text.slice(second)],
            };
        }
    }
    yield { kind: 'characters', chunks: Array.from(text) };
    yield { kind: 'characters-with-empty-chunks', chunks: Array.from(text).flatMap(c => [c, '', '']) };
}

function web(chunks) {
    return new ReadableStream({
        start(controller) {
            for (const chunk of chunks) controller.enqueue(Buffer.from(chunk));
            controller.close();
        },
    });
}

const apis = {
    'node-strings': chunks => csv.getJsonFromStreamAsync(Readable.from(chunks)),
    'node-ascii-buffers': chunks => csv.getJsonFromStreamAsync(Readable.from(chunks.map(c => Buffer.from(c)))),
    'web-ascii-bytes': chunks => csv.browser.getJsonFromStreamAsync(web(chunks)),
    'streamed-file-callbacks': async chunks => {
        const file = new File(chunks, 'criterion.csv', { type: 'text/csv' });
        Object.defineProperty(file, 'stream', { value: () => web(chunks) });
        const rows = [];
        let completions = 0;
        await csv.browser.getJsonFromFileStreamingAsyncWithCallback(file, {
            chunkSize: 2,
            onChunk: chunk => rows.push(...chunk),
            onComplete: all => {
                completions++;
                assert.deepStrictEqual(all, rows);
            },
        });
        assert.equal(completions, 1);
        return rows;
    },
};

async function main() {
    const counts = Object.fromEntries(Object.keys(apis).map(name => [name, { checks: 0, failures: 0 }]));
    const examples = [];
    const affected = new Set();
    for (const scenario of scenarios) {
        for (const { kind, chunks } of partitions(scenario.text)) {
            for (const [name, parse] of Object.entries(apis)) {
                configure(scenario);
                counts[name].checks++;
                try {
                    assert.deepStrictEqual(await parse(chunks), scenario.expected);
                } catch (error) {
                    counts[name].failures++;
                    affected.add(scenario.name);
                    if (examples.length < 12) examples.push({ scenario: scenario.name, api: name, kind, message: error.message });
                }
            }
        }
    }
    const failures = Object.values(counts).reduce((sum, count) => sum + count.failures, 0);
    console.log(JSON.stringify({ node: process.version, scenarios: scenarios.length, counts, affected: [...affected], examples }, null, 2));
    console.log(failures ? `CRITERION: FAIL (${failures} mismatches)` : 'CRITERION: PASS');
    process.exitCode = failures ? 1 : 0;
}

main().catch(error => { console.error(error); process.exitCode = 1; });
