# Contribution policy: iuccio/csvToJson

Checked 2026-10-17T00:59:07.903758+00:00 against current upstream `ad47fe16eef8d7644cca0087db91ff5766235d3b`. The resumed
fork base is `31e6cda09bb69d462c3ab9d66fa4157b430c1b8d`, whose prior changes touch
only production stream parsing and its focused tests. Policy files are unchanged.

- [CONTRIBUTING.md](https://github.com/iuccio/csvToJson/blob/ad47fe16eef8d7644cca0087db91ff5766235d3b/CONTRIBUTING.md) welcomes focused fixes with tests;
  prior issue discussion is advised for large changes, not required for this
  localized existing-API repair. No maintainer contact is needed to begin.
- [README](https://github.com/iuccio/csvToJson/blob/ad47fe16eef8d7644cca0087db91ff5766235d3b/README.md), [package.json](https://github.com/iuccio/csvToJson/blob/ad47fe16eef8d7644cca0087db91ff5766235d3b/package.json),
  [ESLint configuration](https://github.com/iuccio/csvToJson/blob/ad47fe16eef8d7644cca0087db91ff5766235d3b/eslint.config.js) and
  [CI workflow](https://github.com/iuccio/csvToJson/blob/ad47fe16eef8d7644cca0087db91ff5766235d3b/.github/workflows/ci-cd.yml) define actual checks: npm ci,
  ESLint, Jest (including TypeScript cases), and API docs. CI uses Node 20/22/24/25.
  Run full local acceptance on Node 24 and 22; record the untested matrix entries.
  The contribution guide mentions [StandardJS](https://standardjs.com/) and says
  npm test includes lint, while current scripts separate Jest and ESLint. Follow
  adjacent source conventions and the actual lint configuration; do not claim
  literal StandardJS conformance. No dependency/toolchain change is needed.
- [PR template](https://github.com/iuccio/csvToJson/blob/ad47fe16eef8d7644cca0087db91ff5766235d3b/.github/PULL_REQUEST_TEMPLATE.md) contains an issue
  reference and proposed changes. [Bug](https://github.com/iuccio/csvToJson/blob/ad47fe16eef8d7644cca0087db91ff5766235d3b/.github/ISSUE_TEMPLATE/bug_report.md)
  and [feature](https://github.com/iuccio/csvToJson/blob/ad47fe16eef8d7644cca0087db91ff5766235d3b/.github/ISSUE_TEMPLATE/feature_request.md) templates request
  descriptions/reproduction. No requirement for an issue before this small fix,
  mandatory changelog, special sign-off or release commit marker applies here.
  The guide links [concise imperative commit guidance](https://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html),
  [general contribution advice](https://opensource.guide/how-to-contribute/) and
  [GitHub PR guidance](https://docs.github.com/en/pull-requests/reference/pull-requests),
  which were refreshed. Master-only release and package workflows are outside scope.
- [SECURITY.md](https://github.com/iuccio/csvToJson/blob/ad47fe16eef8d7644cca0087db91ff5766235d3b/SECURITY.md) discusses dependency reporting and supported
  versions; this is a parsing correction, not a security disclosure. No report or
  other upstream contact is authorized. [Code of Conduct](https://github.com/iuccio/csvToJson/blob/ad47fe16eef8d7644cca0087db91ff5766235d3b/CODE_OF_CONDUCT.md)
  was read; no agreement or personal attestation is accepted for the operator.
- [MIT LICENSE](https://github.com/iuccio/csvToJson/blob/ad47fe16eef8d7644cca0087db91ff5766235d3b/LICENSE) permits modification and distribution with
  copyright and permission notices retained. Preserve existing attribution.
- The complete upstream tree has no AGENTS.md, separate AI/automation policy,
  CLA or DCO. The owner-default lookup at https://api.github.com/repos/iuccio/.github
  returned HTTP 404. No explicit AI ban, disclosure rule or special human-review
  prerequisite was found; no explicit AI acceptance is claimed.

Decision before implementation: eligible for this focused repair, isolated tests
and authorized public-fork publication, subject to proof and three fresh reviews.

**Needs you:** none identified for this fork workflow. Any future upstream PR
requires separate authorization, a fresh policy check, truthful use of its template,
and normal maintainer review. No current CLA/DCO or AI disclosure prerequisite was
found. Never include Nightly OSS run material in an upstream contribution.

Independent refresh: the [fresh policy reviewer](reviews/novelty.json) checked
current upstream between 01:02:45 and 01:04:38 UTC, confirmed the same revision,
and found no duplicate fix or unresolved fork-publication restriction. It also
read [CHANGELOG.md](https://github.com/iuccio/csvToJson/blob/ad47fe16eef8d7644cca0087db91ff5766235d3b/CHANGELOG.md):
the file records notable changes using Keep a Changelog and SemVer conventions.
An Unreleased/Fixed note would be appropriate preparation for a future upstream
contribution, but no checked text explicitly makes it a prerequisite to every PR
or this fork publication. This is a recommendation, not an additional approval
gate. The actual full tests, lint and API docs passed on Node 22 and 24.
