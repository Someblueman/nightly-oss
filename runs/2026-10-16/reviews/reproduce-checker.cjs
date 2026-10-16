'use strict';

// Derived from claim.md and the baseline public README/API docs before reading
// candidate production code or candidate tests. Run from the project root.
const assert = require('node:assert/strict');
const { Readable } = require('node:stream');
const path = require('node:path');

const cases = [
    {
        name: 'literal-claim',
        text: 'name,note\nAlice,"hello"\n',
        expected: [{ name: 'Alice', note: 'hello' }]
    },
    {
        name: 'doubled-quotes-and-delimiter',
        text: 'name,note\nAda,"He said ""yes"", then left"\nBob,"ok"\n',
        expected: [
            { name: 'Ada', note: 'He said "yes", then left' },
            { name: 'Bob', note: 'ok' }
        ]
    },
    {
        name: 'quoted-header-multiline-crlf',
        text: '"person,name",note\r\n"Mary, Sue","red\r\nblue and ""green"""\r\nJoe,""\r\n',
        expected: [
            { 'person,name': 'Mary, Sue', note: 'red\r\nblue and "green"' },
            { 'person,name': 'Joe', note: '' }
        ]
    },
    {
        name: 'configured-conversion-mapping-eof',
        text: 'id;active;note\n1;true;"a ""quote""\nnext"\n2;false;"tail"',
        delimiter: ';',
        convert: true,
        map: (row, index) => ({ ...row, rowNumber: index }),
        expected: [
            { id: 1, active: true, note: 'a "quote"\nnext', rowNumber: 0 },
            { id: 2, active: false, note: 'tail', rowNumber: 1 }
        ]
    }
];

function freshApi(browser, item) {
    const root = process.cwd() + path.sep;
    for (const name of Object.keys(require.cache)) {
        if (name.startsWith(root)) delete require.cache[name];
    }
    const convert = require(process.cwd());
    let api = browser ? convert.browser : convert;
    api = api.fieldDelimiter(item.delimiter || ',').supportQuotedField(true);
    if (item.convert) api = api.formatValueByType();
    if (item.map) api = api.mapRows(item.map);
    return api;
}

function webStream(chunks) {
    return new ReadableStream({
        start(controller) {
            for (const chunk of chunks) controller.enqueue(chunk);
            controller.close();
        }
    });
}

async function check(mode, item, chunks) {
    const api = freshApi(mode !== 'node', item);
    if (mode === 'node') {
        assert.deepEqual(await api.getJsonFromStreamAsync(Readable.from(chunks)), item.expected);
    } else if (mode === 'web') {
        assert.deepEqual(await api.getJsonFromStreamAsync(webStream(chunks)), item.expected);
    } else {
        const file = new File([item.text], 'review.csv', { type: 'text/csv' });
        file.stream = () => webStream(chunks.map(chunk => new TextEncoder().encode(chunk)));
        const collected = [];
        let completed;
        let reportedError;
        await api.getJsonFromFileStreamingAsyncWithCallback(file, {
            chunkSize: 1,
            onChunk: rows => collected.push(...rows),
            onComplete: rows => { completed = rows; },
            onError: error => { reportedError = error; }
        });
        assert.equal(reportedError, undefined);
        assert.deepEqual(collected, item.expected);
        assert.deepEqual(completed, item.expected);
    }
}

async function main() {
    console.log('Independent quoted-stream checker; Node ' + process.version);
    let total = 0;
    let failures = 0;
    for (const item of cases) {
        const partitions = [['unsplit', [item.text]]];
        for (let split = 1; split < item.text.length; split++) {
            partitions.push(['split-' + split, [item.text.slice(0, split), item.text.slice(split)]]);
        }
        partitions.push(['single-character', Array.from(item.text)]);
        for (const mode of ['node', 'web', 'callback']) {
            let groupFailures = 0;
            const examples = [];
            for (const [label, chunks] of partitions) {
                total++;
                try {
                    await check(mode, item, chunks);
                } catch (error) {
                    failures++;
                    groupFailures++;
                    if (examples.length < 3) examples.push({ partition: label, error: error.message });
                }
            }
            console.log(JSON.stringify({ case: item.name, mode, tested: partitions.length,
                passed: partitions.length - groupFailures, failed: groupFailures, examples }));
        }
    }
    console.log(JSON.stringify({ total, passed: total - failures, failed: failures }));
    process.exitCode = failures ? 1 : 0;
}

main().catch(error => { console.error(error); process.exitCode = 1; });
