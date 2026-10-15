# Reproduce the retained-byte regression

The baseline is upstream `96b69c7949060424ce4778947e3e32112cb7e3d5`.
The candidate is `ac5ce55dcb3810dc8a5d2a1cd22219e0ef972756` in
[Someblueman/xstrings](https://github.com/Someblueman/xstrings).
The focused regression must fail on baseline production code and pass on the
candidate. No external service or dependency is needed by the Go module.

Use a dedicated checkout of this results repository and its documented Docker
environment. Start a new bounded helper session only if that date has not already
been used. From the results repository root, prepare two source checkouts:

```sh
git clone --no-checkout https://github.com/Someblueman/xstrings.git .work/checkouts/xstrings-proof-before
git -C .work/checkouts/xstrings-proof-before checkout --detach 96b69c7949060424ce4778947e3e32112cb7e3d5
git -C .work/checkouts/xstrings-proof-before show ac5ce55dcb3810dc8a5d2a1cd22219e0ef972756:translate_test.go > .work/checkouts/xstrings-proof-before/translate_test.go

git clone --no-checkout https://github.com/Someblueman/xstrings.git .work/checkouts/xstrings-proof-after
git -C .work/checkouts/xstrings-proof-after checkout --detach ac5ce55dcb3810dc8a5d2a1cd22219e0ef972756

docker pull golang@sha256:d9c68c2c51161e12fd77e4c6320687c9cd86e1af1e3ad6e6cd63ff970641453c
```

Run this once for each checkout, substituting `before` or `after` in its path:

```sh
python3 night.py run --checkout .work/checkouts/xstrings-proof-before \
  --image golang@sha256:d9c68c2c51161e12fd77e4c6320687c9cd86e1af1e3ad6e6cd63ff970641453c \
  --timeout 240 -- sh -c \
  'export GOCACHE=/work/.gocache GOPATH=/work/.gopath GOTMPDIR=/work/.gotmp; mkdir -p "$GOTMPDIR"; go version; go test -count=1 -run '\''^TestSqueeze$'\'' -v ./...'
```

The recorded environment was Linux arm64, Go 1.26.9. The baseline table stops at
its first failure; map iteration means the first displayed failing case can vary.
The saved [before](evidence/before.json) and [after](evidence/after.json) records
contain the exact original command, image ID, source fingerprint and exit status.
The baseline check's test file differs from the candidate test file only in
formatting; the added regression cases are the same.

For the separate independent reproduction, copy
[reproduce_test.go](reviews/reproduce_test.go) into each checkout as
`independent_reproduce_test.go`, then use the command array in
[reproduce-before.json](reviews/reproduce-before.json). It selects only
`TestIndependentSqueeze*`. The baseline produced 118,652 oracle mismatches out of
185,646 comparisons; the candidate produced zero. These finite comparisons are
evidence for the stated behavior, not a claim of universal correctness.

The full acceptance commands are saved in
[suite-go126.json](evidence/suite-go126.json) and
[suite-go117.json](evidence/suite-go117.json). They run the existing suite, coverage,
vet, and (on Go 1.26) the race detector and changed-file formatting check. All
project execution remains inside disposable containers through `night.py run`.
