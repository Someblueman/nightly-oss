# Reproduce streamed CRLF header indexing

Project: [iuccio/csvToJson](https://github.com/iuccio/csvToJson).
Baseline: published fork commit `31e6cda09bb69d462c3ab9d66fa4157b430c1b8d`,
which already includes the preceding quoted-record repair.
Candidate: [`e80bf7bb2f0716c5077e733a1eff89b1c63e7694`](https://github.com/Someblueman/csvToJson/commit/e80bf7bb2f0716c5077e733a1eff89b1c63e7694)
in the verified public fork.
This experiment measures the incremental CRLF correction against that baseline;
current upstream is `ad47fe16eef8d7644cca0087db91ff5766235d3b`.

Use a dedicated checkout of the results repository and its documented Docker
setup. Start one bounded helper session on an unused
date. From the results repository root:

```sh
git clone --no-checkout https://github.com/Someblueman/csvToJson.git .work/checkouts/crlf-before
git -C .work/checkouts/crlf-before checkout --detach 31e6cda09bb69d462c3ab9d66fa4157b430c1b8d
git -C .work/checkouts/crlf-before show e80bf7bb2f0716c5077e733a1eff89b1c63e7694:test/stream-line-endings.spec.js > .work/checkouts/crlf-before/test/stream-line-endings.spec.js

git clone --no-checkout https://github.com/Someblueman/csvToJson.git .work/checkouts/crlf-after
git -C .work/checkouts/crlf-after checkout --detach e80bf7bb2f0716c5077e733a1eff89b1c63e7694

docker pull node@sha256:14078204b6bb268c107ceff6d3c43f45a888105e5c2b18b14c32b3409d93a1b0
```

Run once per checkout, replacing `before` with `after` for the candidate:

```sh
python3 night.py run --checkout .work/checkouts/crlf-before \
  --image node@sha256:14078204b6bb268c107ceff6d3c43f45a888105e5c2b18b14c32b3409d93a1b0 \
  --timeout 240 -- sh -c \
  'set -e; export npm_config_cache=/work/.npm-cache; node --version; npm ci --no-audit --no-fund; npm test -- --runInBand test/stream-line-endings.spec.js'
```

Expected baseline: 18 failed and 12 passed. Expected candidate: 30 passed. The
[baseline log](evidence/before.log) shows expected rows replaced by an empty
array or incorrect header mapping only after stream partitioning; its Node and
browser unsplit controls pass. [Candidate output](evidence/after.log) preserves
the same assertions and fixtures. Callback cases assert row and completion results.

The unchanged full acceptance command, recorded in
[Node 24](evidence/suite-node24.json) and [Node 22](evidence/suite-node22.json), is:

```sh
set -e
export npm_config_cache=/work/.npm-cache
node --version
npm ci --no-audit --no-fund
npm run lint
npm test -- --runInBand
npm run docs:api
```

Run through `night.py run --timeout 360 -- sh -c COMMAND` with the appropriate
image and candidate checkout. Node 22's immutable image is
`node@sha256:0e5f906573693feaa1e21057ebdcfdb5bd5021f050b2dc7c9deceb629c7da2a8`.
Both full checks passed all 225 tests. Node 20/25, real browser engines and remote
CI are outside the local evidence. No downloaded project code executes on the host.

Independent checkers need no dependency installation. Copy the selected checker
to each checkout's root, then use the same helper/image with the indicated command:

| Checker | Container command | Baseline | Candidate |
|---|---|---|---|
| [Reproduction](reproduce-check.cjs) | `node reproduce-check.cjs` | 96 failures / 1,428 checks | 1,428 passed |
| [Criterion](evidence/criterion-check.cjs) | `node criterion-check.cjs` | 1,736 failures / 32,956 checks | 32,956 passed |

The reproduction checker derives its expected rows from eleven explicit examples;
all 44 unsplit fixture/API controls pass on baseline. The criterion checker uses
45 inputs and every one/two-cut partition, plus character and empty chunks, for
8,239 input/partition cases per API across four public API modes. These finite
corpora support the recorded behavior, not universal CSV correctness.
