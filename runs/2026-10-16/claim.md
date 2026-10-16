# Claim: quoted CSV records survive stream chunk boundaries

Recorded before production edits on 2026-10-16, after the unchanged baseline's
177 tests, lint and API documentation generation passed.

Project: https://github.com/iuccio/csvToJson
Baseline: `ad47fe16eef8d7644cca0087db91ff5766235d3b`.
Kind: localized bug fix to existing stream parsing APIs.

With quoted-field support enabled, splitting a valid quoted CSV record across
string chunks must not change its parsed rows or cause a spurious quote error.
This includes boundaries within a quoted value, within doubled quote escapes,
and around embedded line breaks. Node's public streaming API and the browser
ReadableStream API share this behavior, including streamed callback results.

Concrete example: chunks `name,note\nAlice,"hel` and `lo"\n` must parse to
`[{ name: "Alice", note: "hello" }]`, just as the unsplit input does. Include a
quoted header and a multiline field in the regression corpus. Preserve existing
delimiters, row mapping, value conversion and public API signatures.

Acceptance:

1. Add focused public-API regression tests. Run the same command and immutable
   Node image against baseline production code plus these tests and the candidate.
   The quoted-chunk regression must fail before and pass after.
2. Run the full existing Jest suite (including TypeScript cases), ESLint and API
   documentation generation on Node 24. Repeat full acceptance on Node 22, which
   is in upstream CI, if the official image is available within the budget.
3. Obtain three fresh independent reviewers for reproduction, duplicate work and
   policy, and exact claim/compatibility. All must pass the exact candidate commit.

This claim concerns CSV quote state across already decoded text chunks. It does
not claim to repair decoding when a multibyte UTF-8 character is split between
binary chunks, all malformed CSV diagnostics, or every parser edge case. No
performance improvement is claimed.

All project execution uses `night.py run`. The focused container command is:

```sh
set -e
export npm_config_cache=/work/.npm-cache
node --version
npm ci --no-audit --no-fund
npm test -- --runInBand test/stream-chunks.spec.js
```
