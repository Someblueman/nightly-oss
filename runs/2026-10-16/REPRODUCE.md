# Reproduce the quoted-stream regression

Baseline: `ad47fe16eef8d7644cca0087db91ff5766235d3b` from
[iuccio/csvToJson](https://github.com/iuccio/csvToJson).
Candidate: `31e6cda09bb69d462c3ab9d66fa4157b430c1b8d` in the public
[Someblueman/csvToJson](https://github.com/Someblueman/csvToJson) fork.

Use a dedicated checkout of the results repository and its documented Docker
setup. Begin one bounded helper session on an unused date. From its root:

```sh
git clone --no-checkout https://github.com/Someblueman/csvToJson.git .work/checkouts/csv-proof-before
git -C .work/checkouts/csv-proof-before checkout --detach ad47fe16eef8d7644cca0087db91ff5766235d3b
git -C .work/checkouts/csv-proof-before show 31e6cda09bb69d462c3ab9d66fa4157b430c1b8d:test/stream-chunks.spec.js > .work/checkouts/csv-proof-before/test/stream-chunks.spec.js

git clone --no-checkout https://github.com/Someblueman/csvToJson.git .work/checkouts/csv-proof-after
git -C .work/checkouts/csv-proof-after checkout --detach 31e6cda09bb69d462c3ab9d66fa4157b430c1b8d

docker pull node@sha256:14078204b6bb268c107ceff6d3c43f45a888105e5c2b18b14c32b3409d93a1b0
```

Run this once for each checkout, replacing `before` with `after` for the candidate:

```sh
python3 night.py run --checkout .work/checkouts/csv-proof-before \
  --image node@sha256:14078204b6bb268c107ceff6d3c43f45a888105e5c2b18b14c32b3409d93a1b0 \
  --timeout 240 -- sh -c \
  'set -e; export npm_config_cache=/work/.npm-cache; node --version; npm ci --no-audit --no-fund; npm test -- --runInBand test/stream-chunks.spec.js'
```

Expected baseline: 15 failed and 3 passed. Expected candidate: all 18 passed.
The baseline's valid split inputs enter its quote-error path; a pre-existing
missing error-class import makes the reported exception a `ReferenceError`.
The candidate parses those valid records successfully instead of reaching that
error path. The captured [before](evidence/before.log) and [after](evidence/after.log)
outputs preserve the actual observations.

The full acceptance commands are recorded in
[suite-node24.json](evidence/suite-node24.json) and
[suite-node22.json](evidence/suite-node22.json). Both run `npm ci`, `npm run lint`,
the complete Jest suite and `npm run docs:api` within the disposable container.
No downloaded code needs to run on the host.

To replay the independent reproduction, copy
[reproduce-checker.cjs](reviews/reproduce-checker.cjs) into each checkout's root.
Use the same `night.py run` invocation but replace the shell command with
`node reproduce-checker.cjs .`. It needs no installed dependencies. Expected
totals are 303 failures out of 606 on baseline and zero failures on the candidate;
the [review](reviews/reproduce.json) describes the finite input corpus and limits.

The separate [criterion checker](reviews/criterion-check.cjs) can be copied into
each checkout and run with `node criterion-check.cjs` under the same helper and
image. Expected baseline: 5,337 failures out of 9,349; candidate: zero failures.
It also prints an adjacent CRLF/header-offset observation that fails identically
on both revisions and is not included in the quoted-record acceptance total.
The [criterion verdict](reviews/criterion.json) explains the scope, checker
corrections and original retained failure logs. Neither independent checker
requires installed dependencies.
