# Setup validation — 2026-10-14

This records controller validation, not an improvement to an open source project.

The complete suite passed with real Docker execution enabled:

```sh
docker pull python:3.12-slim
NIGHTLY_DOCKER_TESTS=1 python3 -m unittest discover -s tests -v
```

Eleven tests cover the fixed daily deadline, expired/closed-session refusal,
source copying, real CLI lifecycle, and three Docker checks:

- The container cannot see Git metadata, the host-only fixture, the Docker socket,
  or the host environment sentinel. Its root filesystem is read-only. Writes to
  its execution copy leave both the checkout and retained input unchanged.
- A command exiting with status 7 is recorded and returned as status 7.
- A sleeping command times out with status 124; its container is removed.

Environment: macOS host, Linux arm64 container, Docker Engine 29.7.2,
Python 3.12.15 container image:

`python@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1`

Python compilation and Git whitespace checks also passed. GitHub discovery and
the authenticated publication account were checked.

The [first live trial](runs/2026-10-14.md) selected Boltons, demonstrated a real
regression before and after a fix, passed its complete suite on Python 3.12 and
3.14, obtained three fresh independent reviews, and published the verified commit
to a public fork with remote equality confirmed. The scheduled 02:00 invocation
has not itself fired yet.

During that trial the operator requested the V3R1T4S-style file entry point,
independent reviewers and record gate. The added gate's checks and the existing
controller unit tests pass: 14 tests, with the three opt-in Docker boundary tests
skipped in this subsequent unit run. The Docker boundary was unchanged; the
project's real checks and independent reproductions exercised it throughout the
trial. The original 11-test Docker-enabled setup result above remains separate.
