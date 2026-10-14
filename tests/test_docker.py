"""Opt-in checks against a real Docker engine and an already-pulled Python image."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


@unittest.skipUnless(os.environ.get("NIGHTLY_DOCKER_TESTS") == "1", "enable real Docker checks explicitly")
class DockerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        project = Path(__file__).resolve().parents[1]
        (project / ".work").mkdir(exist_ok=True)
        cls.temporary = tempfile.TemporaryDirectory(dir=project / ".work")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.root = Path(cls.temporary.name)
        shutil.copy2(project / "night.py", cls.root / "night.py")
        cls.checkout = cls.root / ".work/checkouts/fixture"
        cls.checkout.mkdir(parents=True)
        (cls.checkout / "source.txt").write_text("original\n")
        (cls.root / "host-only.txt").write_text("not mounted\n")
        (cls.checkout / "outside").symlink_to(cls.root / "host-only.txt")
        subprocess.run(["git", "init", "-q", str(cls.checkout)], check=True)
        subprocess.run(["git", "-C", str(cls.checkout), "add", "."], check=True)
        subprocess.run([
            "git", "-C", str(cls.checkout), "-c", "core.hooksPath=/dev/null",
            "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
            "commit", "-qm", "container fixture",
        ], check=True)
        subprocess.run([sys.executable, str(cls.root / "night.py"), "begin", "--minutes", "5"],
                       check=True, capture_output=True, timeout=10)

    def run_check(self, code, timeout=30):
        result = subprocess.run([
            sys.executable, str(self.root / "night.py"), "run", "--checkout", str(self.checkout),
            "--image", "python:3.12-slim", "--timeout", str(timeout), "--", "python", "-c", code,
        ], env={**os.environ, "NIGHTLY_HOST_SENTINEL": "must-not-enter-container"},
            capture_output=True, text=True, timeout=timeout + 45)
        self.assertTrue(result.stdout, result.stderr)
        record = json.loads(result.stdout)
        self.assertNotIn("cleanup_error", record)
        containers = subprocess.check_output([
            "docker", "ps", "-aq", "--filter", f"name=^/{record['container_name']}$"
        ], timeout=10)
        self.assertEqual(containers.strip(), b"")
        return result, record

    def test_source_and_credentials_are_isolated(self):
        result, record = self.run_check("""
import os
from pathlib import Path
assert not Path('.git').exists()
assert not Path('/var/run/docker.sock').exists()
assert 'NIGHTLY_HOST_SENTINEL' not in os.environ
assert os.statvfs('/').f_flag & os.ST_RDONLY
assert not Path('outside').exists()
assert Path('source.txt').read_text() == 'original\\n'
Path('source.txt').write_text('changed in container\\n')
try:
    Path('/root/nightly-write-probe').write_text('should fail')
except OSError:
    pass
else:
    raise AssertionError('container root filesystem was writable')
print('isolation checks passed')
""")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(record["exit_code"], 0)
        self.assertEqual((self.checkout / "source.txt").read_text(), "original\n")
        retained = self.root / record["evidence"] / "source/source.txt"
        self.assertEqual(retained.read_text(), "original\n")
        self.assertTrue(record["image"]["id"].startswith("sha256:"))

    def test_failing_command_preserves_failure(self):
        result, record = self.run_check("raise SystemExit(7)")
        self.assertEqual(result.returncode, 7)
        self.assertEqual(record["exit_code"], 7)

    def test_timeout_stops_container(self):
        result, record = self.run_check("import time; print('started', flush=True); time.sleep(60)", 5)
        self.assertEqual(result.returncode, 124)
        self.assertEqual(record["exit_code"], 124)
        self.assertLess(record["elapsed_seconds"], 20)
        log = (self.root / record["evidence"] / "output.log").read_text()
        self.assertIn("started", log)


if __name__ == "__main__":
    unittest.main()
