# Claim: CRLF record boundaries preserve streamed header indexing

Recorded before production edits on 2026-10-17 after the resumed baseline's
195 tests, lint and API documentation generation passed in Node 24.

Project: https://github.com/iuccio/csvToJson
Current upstream: `ad47fe16eef8d7644cca0087db91ff5766235d3b`.
Experiment baseline: published fork commit
`31e6cda09bb69d462c3ab9d66fa4157b430c1b8d`, including the preceding quoted-record fix.
Kind: localized bug fix to existing streaming APIs.

For valid CSV using CRLF record separators, splitting between CR and LF must
not add a record or alter the configured header index or parsed rows. A CRLF
pair outside quoted fields is one record separator, whether delivered in one
chunk or two. Empty chunks between the pair must not change the result. Real
blank records before the header must still count as records, matching unsplit
input. Standalone CR and LF separators, including a final CR at end of stream,
must continue to work. Embedded CR/LF inside quoted values must remain data.

Concrete example: with `indexHeader(1)`, chunks `preamble\r` and
`\nid,note\r\n1,ok\r\n` must return `[{ id: "1", note: "ok" }]`, equal to
the unsplit input. Cover Node streams, browser ReadableStream and streamed-file
callbacks through their public APIs. Preserve exported API signatures, normal
row mapping and conversions, and the preceding quoted-record behavior.

Acceptance:

1. The same focused public-API regressions fail against baseline production
   code and pass against the candidate using the same immutable Node image and
   command. Include unsplit controls, nonzero and default header indices, blank
   preamble records, empty chunks, mixed quoted content and EOF cases.
2. Full existing Jest suite, ESLint and API docs pass on Node 24 and Node 22.
   This includes the preceding quote-boundary regressions. Record untested
   Node versions and distinguish Node Web APIs from an actual browser engine.
3. Three fresh independent reviewers pass the exact candidate commit for
   reproduction, duplicate work/current policy, and claim/compatibility.

The claim concerns record-separator handling across decoded string or ASCII
byte chunks. It does not establish split multibyte decoding, all malformed CSV
diagnostics, universal CSV conformance, callback timing guarantees or performance.

Focused container command, executed only through `night.py run`:

```sh
set -e
export npm_config_cache=/work/.npm-cache
node --version
npm ci --no-audit --no-fund
npm test -- --runInBand test/stream-line-endings.spec.js
```
