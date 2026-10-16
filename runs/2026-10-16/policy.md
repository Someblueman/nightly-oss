# Contribution policy: iuccio/csvToJson

Checked 2026-10-16T01:03:52.004881+00:00 against upstream `ad47fe16eef8d7644cca0087db91ff5766235d3b`.

- [CONTRIBUTING.md](https://github.com/iuccio/csvToJson/blob/ad47fe16eef8d7644cca0087db91ff5766235d3b/CONTRIBUTING.md) welcomes focused bug fixes, asks for tests and standard-style formatting, and advises prior discussion for large changes. This run is restricted to a small existing-API fix. It links the project Code of Conduct and general GitHub/contribution guides. No maintainer contact is needed to start a focused fix.
- [README](https://github.com/iuccio/csvToJson/blob/ad47fe16eef8d7644cca0087db91ff5766235d3b/README.md) documents Node/browser APIs and npm tests. [package.json](https://github.com/iuccio/csvToJson/blob/ad47fe16eef8d7644cca0087db91ff5766235d3b/package.json) defines Jest tests and a separate ESLint command; despite the contribution guide saying tests include lint, run both actual scripts. The [CI workflow](https://github.com/iuccio/csvToJson/blob/ad47fe16eef8d7644cca0087db91ff5766235d3b/.github/workflows/ci-cd.yml) checks Node 20/22/24/25, lint, tests and API docs. Local acceptance will use Node 24 and a second supported Node version when feasible. No release/package/deployment commands are authorized.
- [PR template](https://github.com/iuccio/csvToJson/blob/ad47fe16eef8d7644cca0087db91ff5766235d3b/.github/PULL_REQUEST_TEMPLATE.md) requests an issue reference and proposed changes. Issue templates request expected/actual behavior and reproduction. Future upstream submissions must use these templates and recheck current policies; no upstream PR is authorized now. No mandatory changelog or special bug-fix commit format was found. Release-marker guidance applies to master releases, which are outside scope.
- [SECURITY.md](https://github.com/iuccio/csvToJson/blob/ad47fe16eef8d7644cca0087db91ff5766235d3b/SECURITY.md) describes dependencies, supported releases and vulnerability reporting. Do not contact maintainers during this run. [Code of Conduct](https://github.com/iuccio/csvToJson/blob/ad47fe16eef8d7644cca0087db91ff5766235d3b/CODE_OF_CONDUCT.md) governs conduct; no agreement or personal attestation is made on the operator's behalf.
- [MIT LICENSE](https://github.com/iuccio/csvToJson/blob/ad47fe16eef8d7644cca0087db91ff5766235d3b/LICENSE) permits modified public forks with attribution retained. Full tree inspection found no AGENTS, separate AI/automation policy, CLA or DCO requirement. The public owner default repository https://api.github.com/repos/iuccio/.github returned HTTP 404. No explicit AI acceptance is claimed.

Decision: eligible for a focused fix, isolated verification and public fork publication subject to evidence and independent review. No human-only prerequisite identified for this workflow.

Independent policy refresh: the fresh [duplicate-work reviewer](reviews/novelty.json)
checked current upstream at 2026-10-16T01:14:21Z, confirmed the same revision, read
the policies and linked guidance independently, and found no blocker to this
focused fix or authorized public-fork publication. The candidate preserves MIT
attribution and follows adjacent source conventions; ESLint, all 195 tests and
API docs passed on Node 22 and 24. Node 20/25 and remote CI were not checked.
No mandatory changelog, CLA, DCO, special sign-off or AI disclosure was found.
The project still requires normal maintainer review for any future upstream PR;
that submission also needs separate operator authorization and a fresh policy
check. No upstream contact or agreement was made.
