# Boltons: preserve braces in format-field item lookups

Claim: `infer_positional_format_args` preserves literal braces inside dictionary
keys, numbers only anonymous replacement fields, and gives `tokenize_format_str`
the correct field names.

- Upstream: https://github.com/mahmoud/boltons
- Baseline: `4e5faa3d7e4008d89e0d8bf1ea87b6d9a061a16d`
- Candidate: `835936b0f21dac309132a7ab7f01b0a2a86e233c`
- Branch: `nightly/2026-10-14-format-item-braces`
- Candidate checkout: `.work/checkouts/mahmoud-boltons` in the experiment workspace.
- Definition: https://docs.python.org/3/library/string.html#format-string-syntax
- Duplicate-work sources: upstream issues, pull requests, and current default branch.

For example, `{[{}]} {}` with arguments `({'{}': 'value'}, 'tail')` must convert
to `{0[{}]} {1}` and still produce `value tail`. Named and explicitly numbered
fields must preserve their keys as well. Check nested item lookups, conversion
flags, nested width fields, escaped literal braces and literal square brackets.
Existing behavior on ordinary supported format strings must remain compatible.

The acceptance criteria were stated before production edits in the live trial.
This written package was assembled afterwards, when the operator requested the
V3R1T4S review protocol. It is not a claim of file-based preregistration before
the initial experiment. Later runs must save their criteria before editing.

## Reproduce

Use the official `python:3.12-slim` or `python:3.14-slim` image. Execute all
downloaded code through the workspace's `python3 night.py run` helper, with the
checkout passed through `--checkout` and a bounded `--timeout`.

Create virtualenvs under `/work`, because `/tmp` does not permit execution in
this container. Dependencies and tests must run inside the same disposable check.
The relevant existing acceptance command is `tox -e py312` or `tox -e py314`.

Reviewers should derive their own checks from the claim and Python's formatting
definition before reading the author's implementation or tests. Use saved source
and the exact commits above. No upstream messages, pull requests or publication
are part of review.
