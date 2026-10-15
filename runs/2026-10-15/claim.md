# Claim: Squeeze preserves the bytes it does not remove

Recorded before production edits at 2026-10-15T01:05:59.462641+00:00.

Upstream: https://github.com/huandu/xstrings
Baseline: `96b69c7949060424ce4778947e3e32112cb7e3d5`.
Kind: bug in existing public API; no new API or dependency.

`Squeeze(str, pattern)` removes adjacent repeated runes selected by its pattern.
Every retained input segment should keep its original bytes, including invalid
UTF-8. A pattern that selects none of the input must leave the input byte-for-byte
unchanged. Preserve the existing rune comparison and pattern matching behavior;
this claim does not redefine which invalid bytes decode to `utf8.RuneError`.

Concrete examples (Go string literals):

- `Squeeze("aa\xff", "a")` must produce `"a\xff"`.
- `Squeeze("aa\xff\xfe", "z")` must produce the unchanged input.
- `Squeeze("bb\xff\xff", "a")` must produce the unchanged input.
- Valid Unicode, literal U+FFFD, NUL, empty inputs, empty patterns and matching
  repeated runes must retain their established behavior.

Acceptance:

1. Add focused regression cases to the existing Squeeze tests. Run the identical
   command on baseline production code and the candidate in the same Go image;
   the new byte-preservation cases must fail before and pass after.
2. Run all existing tests with the race detector and coverage on Go 1.26, plus
   `go vet ./...` and a formatting check. Run all tests with the CI Go 1.17 image
   when available. Preserve the Go 1.12 language/API compatibility declared by go.mod.
3. Obtain three fresh independent reviews for reproduction, duplicates/policy,
   and exact claim/compatibility. All must pass the candidate commit before publishing.

Checks run through `night.py run` with GOCACHE, GOPATH and GOTMPDIR under `/work`.
The focused container command is:

```sh
export GOCACHE=/work/.gocache GOPATH=/work/.gopath GOTMPDIR=/work/.gotmp
mkdir -p "$GOTMPDIR"
go version
go test -count=1 -run '^TestSqueeze$' -v ./...
```

No performance improvement or universal correctness is claimed.
