# Contribution policy: huandu/xstrings

Checked at 2026-10-15T01:03:33.043624+00:00 against upstream `96b69c7949060424ce4778947e3e32112cb7e3d5`.

- [CONTRIBUTING.md](https://github.com/huandu/xstrings/blob/96b69c7949060424ce4778947e3e32112cb7e3d5/CONTRIBUTING.md) welcomes bug fixes and requires formatting plus all tests passing. New functions must first be discussed in an issue; this run is restricted to a bug fix within an existing API.
- [README.md](https://github.com/huandu/xstrings/blob/96b69c7949060424ce4778947e3e32112cb7e3d5/README.md) links that guide and the API documentation. README/API-list changes are required for new APIs, which are outside this run's chosen scope.
- [CI workflow](https://github.com/huandu/xstrings/blob/96b69c7949060424ce4778947e3e32112cb7e3d5/.github/workflows/go.yml) runs all tests with coverage on Go 1.17. The module declares Go 1.12. Preserve language compatibility and test with the CI toolchain if available, plus a current official Go image. Coverage upload requires a secret and is not part of local acceptance.
- [LICENSE](https://github.com/huandu/xstrings/blob/96b69c7949060424ce4778947e3e32112cb7e3d5/LICENSE) is MIT; preserve existing attribution.
- Full repository tree: no AGENTS, separate AI policy, PR/issue template, security policy, CLA or DCO requirement found. The owner's public `.github` repository returned 404. No explicit AI acceptance is claimed.
- No mandatory maintainer contact was found for bug fixes to existing functions. No upstream message or PR is authorized. Any later PR must recheck the current policy and use only project details, relevant validation and required disclosures.

Decision: eligible for isolated bug-fix work and public fork publication, subject to the required tests and independent review. No human-only prerequisite identified for starting this work.

Independent prepublication recheck: the [duplicate-work/policy reviewer](reviews/novelty.json)
checked current upstream between 2026-10-15 01:09:17 and 01:12:39 UTC. The upstream
revision was unchanged. The reviewer examined all 72 returned issue/PR records,
all 20 PR file lists and relevant patches/discussions, plus current contribution
documents and owner defaults. No equivalent Squeeze fix or additional publication
restriction was found. Related issue #65 concerns byte preservation in
Translate/Delete, not this function. This is a bounded duplicate-work check.

The exact candidate `ac5ce55dcb3810dc8a5d2a1cd22219e0ef972756` preserves attribution,
adds no API or dependency, and passes formatting plus the full test suite on the
upstream CI's Go 1.17 toolchain and Go 1.26. The recorded race, vet and independent
checks also pass. Remote CI and the token-backed coverage upload were not run.

**Needs you:** no intervention is required for authorized fork publication.
Any future upstream PR needs separate operator authorization and another current
policy check. No agreement, attestation or maintainer contact was made.
