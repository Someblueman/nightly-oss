# Nightly OSS

Each night: pick an open source project, make one useful improvement, demonstrate
it, and publish the code and evidence. Return to promising work on later nights.

Inspired by [V3R1T4S](https://github.com/elder-plinius/V3R1T4S) and its emphasis on
results that someone else can check. This is an independent software experiment.

## The experiment

- **When:** every night at 02:00 Europe/London, with a 90-minute working budget.
- **Where:** public forks under [Someblueman](https://github.com/Someblueman).
- **Evidence:** dated reports in [runs](runs/README.md), linking exact upstream and
  result commits, reproduction commands, and relevant measurements.
- **Continuation:** resume when a previous report names a concrete next experiment;
  otherwise choose randomly among eligible projects. Explore a new project at
  least every third working night. Retire a lead after two nights without new evidence.
- **Publication:** push verified changes to our forks and reports here. Upstream
  pull requests, issues, messages, releases, and package publication are separate decisions.

A passing test suite alone does not establish an improvement. Bug fixes need a
reproducer that fails before and passes after. Performance changes need repeated
measurements on the same inputs and environment, with unchanged results. Features
need a usable before/after demonstration and project-appropriate acceptance checks.

No change is a valid outcome. Failed experiments and blocked runs get honest reports;
unfinished code stays local. There is no quota for commits or claimed wins.

## How it runs

A Codex scheduled task reads [RUN_PROMPT.txt](RUN_PROMPT.txt), which loads the
operating rules, environment recipe and previous run reports. It assumes no prior
conversation context. The current scheduler resumes this thread; the on-disk
protocol is also sufficient to start from a fresh session. The desktop app and
computer must remain running; Docker
must be available. The schedule is configured in Codex, not installed by this repository.

The file-based run protocol follows [V3R1T4S](https://github.com/elder-plinius/V3R1T4S/blob/9b1d444eb864a1475e092047d49612a7410a7c5a/kit/RUN.md):
save the claim, work on it, preserve proof, and ask three fresh reviewers to check
reproduction, duplicate work and the exact acceptance criterion. All three must
pass the same candidate commit. [check_run.py](check_run.py) checks the saved
records before publication; [EVIDENCE.md](EVIDENCE.md) describes its scope and format.
Review time is included in the existing 90-minute budget. Unreviewed or rejected
candidates stay local with a concrete next step.

`night.py` records the working deadline and runs build/test commands in disposable
Docker containers. Only a copy of the selected source files is mounted: no host
home directory, Git metadata, Docker socket, or GitHub credentials. Containers have
resource limits, run as the invoking user's numeric UID/GID, and have outbound
networking for dependencies. They are not a network
isolation boundary. Publishing happens on the host after inspection.

The helper enforces the remaining deadline for build/test commands and refuses
commands after expiry. The agent is instructed to stop the overall run within
90 minutes; the helper does **not** forcibly terminate the Codex conversation or
cap model tokens. Runs use the current Codex setup and its normal usage allowance.

## Local use

Requires Python 3.10+, Git, GitHub CLI, and a running Docker engine. No Python packages
are required. Use a dedicated checkout of this repository.

```sh
python3 -m unittest discover -s tests -v
python3 night.py begin
python3 night.py status
```

Clone a selected public project into `.work/checkouts/OWNER-REPO` using its public
HTTPS URL. Pull an appropriate official language image, then execute its checks:

```sh
docker pull python:3.12-slim
python3 night.py run --checkout .work/checkouts/OWNER-REPO \
  --image python:3.12-slim --timeout 600 -- python -m unittest discover
python3 night.py end
```

Containers have a writable `/work` and a restricted `/tmp`. For a Python project
using tox, create the virtualenv and caches under `/work` and install dependencies
inside each disposable check:

```sh
python3 night.py run --checkout .work/checkouts/OWNER-REPO \
  --image python:3.12-slim --timeout 600 -- sh -c \
  'python -m venv /work/.trial-venv &&
   /work/.trial-venv/bin/python -m pip --disable-pip-version-check install tox tox-uv &&
   UV_CACHE_DIR=/work/.trial-uv-cache /work/.trial-venv/bin/tox -e py312'
```

Choose the project's documented command and compatible image. `/tmp` cannot
execute virtualenv scripts. This recipe leaves host packages and settings alone.

To verify the container boundary itself after pulling that image:

```sh
NIGHTLY_DOCKER_TESTS=1 python3 -m unittest discover -s tests -v
```

These opt-in checks exercise source/credential isolation, failure propagation,
and container cleanup after a real command timeout. They do not count as an
improvement to a third-party project.

Each check retains the source snapshot, combined output, image ID/digests, source
fingerprint, command, and exit status beneath `.work/evidence/`. The helper includes
tracked and non-ignored untracked files, excludes Git metadata, and does not copy
submodules. Execution uses a separate temporary copy, discarded afterwards; the
retained input snapshot stays unchanged. Have checks print measurements and other
required evidence to stdout/stderr. Choose projects whose checks can run in this environment.

Follow [the operating instructions](AGENTS.md) for selection, proof, publication,
and resuming earlier work. Keep private machine details and raw agent transcripts
out of the public repository.

