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
the authenticated publication account were checked. The overnight project-selection,
improvement, and fork-publication loop has not yet completed its first real run.
