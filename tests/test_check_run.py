import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import check_run


class EvidenceGateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "2026-10-14"
        self.root.mkdir()
        self.root.with_suffix(".md").write_text("A bounded experiment.\n")
        (self.root / "claim.md").write_text("The same regression fails before and passes after.\n")
        self.result = {
            "status": "verified", "summary": "Fixed one bug", "kind": "bug",
            "upstream": "example/library", "baseline_commit": "a" * 40,
            "candidate_commit": "b" * 40, "candidate_source_sha256": "d" * 64,
            "claim": "claim.md", "publication": None,
            "checks": {
                "before": self.evidence("before", 1, "a" * 40, "c" * 64),
                "after": self.evidence("after", 0, "b" * 40, "d" * 64),
                "acceptance": [self.evidence("suite", 0, "a" * 40, "d" * 64)],
            },
        }
        for role in ("reproduce", "novelty", "criterion"):
            self.write("reviews/" + role + ".json", {
                "role": role, "context": "fresh agent", "candidate_commit": "b" * 40,
                "pass": True, "summary": "Observed result", "evidence": ["Independent check output"],
                "confirmed_scope": "The focused behavior works.",
            })
        self.save()

    def write(self, name, data):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data))

    def save(self):
        self.write("result.json", self.result)

    def evidence(self, name, exit_code, commit, fingerprint):
        self.write(name + ".json", {
            "command": ["python", "-m", "pytest"], "exit_code": exit_code,
            "upstream_or_head_commit": commit, "source_sha256": fingerprint,
            "image": {"id": "sha256:" + "e" * 64},
        })
        output = b"actual captured output\n"
        (self.root / (name + ".log")).write_bytes(output)
        return {"record": name + ".json", "output": name + ".log",
                "output_sha256": hashlib.sha256(output).hexdigest()}

    def change_record(self, name, key, value):
        data = json.loads((self.root / name).read_text())
        data[key] = value
        self.write(name, data)

    def test_complete_record_and_publication(self):
        self.assertEqual(check_run.check(self.root, publish=True), "verified")
        self.result["publication"] = {
            "repository": "Someblueman/library", "parent": "example/library",
            "commit": "b" * 40, "remote_commit": "b" * 40, "branch": "nightly/test",
        }
        self.save()
        self.assertEqual(check_run.check(self.root), "verified")
        self.result["publication"]["remote_commit"] = "f" * 40
        self.save()
        with self.assertRaisesRegex(ValueError, "Remote commit"):
            check_run.check(self.root)

    def test_missing_rejecting_and_stale_review(self):
        path = self.root / "reviews/reproduce.json"
        original = json.loads(path.read_text())
        for key, value in (("pass", False), ("candidate_commit", "f" * 40),
                           ("context", "main agent"), ("evidence", [])):
            with self.subTest(key=key):
                data = {**original, key: value}
                self.write("reviews/reproduce.json", data)
                with self.assertRaises(ValueError):
                    check_run.check(self.root, publish=True)
        path.unlink()
        with self.assertRaisesRegex(ValueError, "Missing artifact"):
            check_run.check(self.root)

    def test_inconsistent_or_failed_checks(self):
        original = json.loads((self.root / "after.json").read_text())
        for key, value in (("command", ["different"]), ("exit_code", 1),
                           ("source_sha256", "f" * 64), ("upstream_or_head_commit", "f" * 40),
                           ("image", {"id": "sha256:" + "f" * 64}),
                           ("cleanup_error", "container still running")):
            with self.subTest(key=key):
                self.write("after.json", {**original, key: value})
                with self.assertRaises(ValueError):
                    check_run.check(self.root)
        self.write("after.json", original)
        self.change_record("suite.json", "source_sha256", "f" * 64)
        with self.assertRaisesRegex(ValueError, "another source"):
            check_run.check(self.root)

    def test_baseline_cannot_be_passing_or_timed_out_for_bug(self):
        for exit_code in (0, 124, 126, 137):
            self.change_record("before.json", "exit_code", exit_code)
            with self.assertRaisesRegex(ValueError, "regression failure"):
                check_run.check(self.root)

    def test_changed_output_and_escaping_path_are_rejected(self):
        (self.root / "after.log").write_text("edited output")
        with self.assertRaisesRegex(ValueError, "hash differs"):
            check_run.check(self.root)
        outside = self.root.parent / "outside.md"
        outside.write_text("outside")
        (self.root / "escape.md").symlink_to(outside)
        for name in ("../outside.md", str(outside), "escape.md"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                check_run.artifact(self.root, name)

    def test_negative_and_unreviewed_reports_cannot_publish_code(self):
        for status in ("blocked", "no_improvement", "promising"):
            self.result = {"status": status, "summary": "Reason and next step in report"}
            self.save()
            self.assertEqual(check_run.check(self.root), status)
            with self.assertRaisesRegex(ValueError, "Only verified"):
                check_run.check(self.root, publish=True)


if __name__ == "__main__":
    unittest.main()
