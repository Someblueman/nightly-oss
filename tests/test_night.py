from datetime import timedelta
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("night", Path(__file__).parents[1] / "night.py")
night = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(night)


class NightTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.root_patch = patch.object(night, "ROOT", self.root)
        self.root_patch.start()
        (self.root / ".work").mkdir()

    def tearDown(self):
        self.root_patch.stop()
        self.temporary.cleanup()

    def test_repeated_begin_preserves_deadline(self):
        first = night.begin(1)
        self.assertEqual(night.begin(90), first)
        first["closed"] = True
        night.write_json(self.root / ".work/session.json", first)
        self.assertEqual(night.begin(90), first)
        self.assertEqual(night.remaining(first), 0)

    def test_expiry_cannot_renew_same_day(self):
        session = night.begin(1)
        session["deadline"] = (night.now() - timedelta(seconds=1)).isoformat()
        night.write_json(self.root / ".work/session.json", session)
        self.assertEqual(night.remaining(session), 0)
        self.assertEqual(night.begin(90), session)

    def test_next_day_gets_new_budget(self):
        session = night.begin(1)
        session["date"] = "2000-01-01"
        session["deadline"] = "2000-01-01T00:01:00+00:00"
        night.write_json(self.root / ".work/session.json", session)
        new = night.begin(90)
        self.assertNotEqual(session["date"], new["date"])
        self.assertGreater(night.remaining(new), 5300)

    def make_checkout(self):
        checkout = self.root / ".work/checkouts/example"
        checkout.mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(checkout)], check=True)
        (checkout / "source.txt").write_text("original\n")
        (checkout / "deleted.txt").write_text("deleted\n")
        (checkout / ".gitignore").write_text("ignored-secret.txt\n")
        subprocess.run(["git", "-C", str(checkout), "add", "."], check=True)
        subprocess.run([
            "git", "-C", str(checkout), "-c", "core.hooksPath=/dev/null",
            "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
            "commit", "-qm", "fixture",
        ], check=True)
        return checkout

    def test_snapshot_captures_patch_without_git_or_ignored_files(self):
        checkout = self.make_checkout()
        (checkout / "source.txt").write_text("modified\n")
        (checkout / "deleted.txt").unlink()
        (checkout / "new.txt").write_text("new\n")
        (checkout / "ignored-secret.txt").write_text("not for container\n")
        output = self.root / "snapshot"
        base, digest = night.snapshot(checkout, output)
        self.assertEqual(len(base), 40)
        self.assertEqual(len(digest), 64)
        self.assertEqual((output / "source.txt").read_text(), "modified\n")
        self.assertTrue((output / "new.txt").exists())
        for excluded in (".git", "deleted.txt", "ignored-secret.txt"):
            self.assertFalse((output / excluded).exists())
        (output / "source.txt").write_text("container modification\n")
        self.assertEqual((checkout / "source.txt").read_text(), "modified\n")

    def test_symlink_is_copied_without_reading_host_target(self):
        checkout = self.make_checkout()
        private = self.root / "private.txt"
        private.write_text("host only\n")
        (checkout / "link").symlink_to(private)
        output = self.root / "snapshot"
        night.snapshot(checkout, output)
        self.assertTrue((output / "link").is_symlink())
        self.assertEqual((output / "link").readlink(), private)

    def test_snapshot_rejects_unrelated_checkout(self):
        with self.assertRaisesRegex(ValueError, "inside .work/checkouts"):
            night.snapshot(self.root, self.root / "snapshot")

    def test_expired_check_refuses_before_docker(self):
        session = night.begin(1)
        session["closed"] = True
        night.write_json(self.root / ".work/session.json", session)
        from argparse import Namespace
        with self.assertRaisesRegex(ValueError, "budget exhausted"):
            night.check(Namespace())

    def test_cli_lifecycle_and_budget_validation(self):
        import shutil
        shutil.copy2(Path(__file__).parents[1] / "night.py", self.root / "night.py")
        def call(*arguments):
            return subprocess.run(
                [sys.executable, str(self.root / "night.py"), *arguments],
                capture_output=True, text=True, timeout=10,
            )
        self.assertNotEqual(call("begin", "--minutes", "91").returncode, 0)
        first = call("begin", "--minutes", "1")
        self.assertEqual(first.returncode, 0, first.stderr)
        deadline = json.loads(first.stdout)["deadline"]
        self.assertEqual(json.loads(call("begin").stdout)["deadline"], deadline)
        self.assertTrue(json.loads(call("end").stdout)["closed"])
        self.assertEqual(json.loads(call("status").stdout)["seconds_remaining"], 0)


if __name__ == "__main__":
    unittest.main()
