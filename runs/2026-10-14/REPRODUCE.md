# Reproduce the independent before/after check

Use a fresh clone of `Someblueman/nightly-oss` with Python 3.10+, Git and Docker.
From its root, start the bounded local session:

```sh
python3 night.py begin
```

The following host-side wrapper fetches the public source and official image,
reads the independent checker, selects source revisions with Git, and passes the
checker to the trusted container helper. All
Boltons execution happens inside Docker. The baseline is expected to exit 1; the
candidate is expected to exit 0. Each helper result points to its captured output.

```sh
python3 - <<'PY'
from pathlib import Path
import subprocess
import sys

checkout = '.work/checkouts/boltons-reproduce'
code = Path('runs/2026-10-14/reviews/reproduce.py').read_text()
image = 'python@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1'
subprocess.run(['git', 'clone', 'https://github.com/Someblueman/boltons.git', checkout],
               check=True, timeout=60)
subprocess.run(['docker', 'pull', image], check=True, timeout=120)
for revision, expected in [
    ('4e5faa3d7e4008d89e0d8bf1ea87b6d9a061a16d', 1),
    ('835936b0f21dac309132a7ab7f01b0a2a86e233c', 0),
]:
    subprocess.run(['git', '-C', checkout, '-c', 'core.hooksPath=/dev/null',
                    'switch', '--detach', revision], check=True, timeout=15)
    result = subprocess.run([sys.executable, 'night.py', 'run', '--checkout', checkout,
                             '--image', image, '--timeout', '60', '--',
                             'python', '-c', code], timeout=90)
    if result.returncode != expected:
        raise SystemExit('Unexpected check result; inspect the captured output')
PY
python3 night.py end
```

Compare the captured JSON with [the saved baseline output](evidence/independent-before.log)
and [candidate output](evidence/independent-after.log): 76 cases, 20 baseline
failures, zero candidate failures, and zero oracle errors. A nonzero baseline exit
alone is not proof: confirm it is the recorded behavioral failures, not a setup error.

The project's broader acceptance commands and their actual output are retained in
[result.json](result.json). This reproduction demonstrates the specific claim;
it does not claim to exercise the full supported OS/interpreter matrix.
