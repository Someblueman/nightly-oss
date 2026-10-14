#!/usr/bin/env python3
"""Check saved evidence and independent verdicts; never execute project code."""

import argparse
import hashlib
import json
from pathlib import Path
import re


def require(condition, message):
    if not condition:
        raise ValueError(message)


def artifact(folder, name):
    require(isinstance(name, str) and name, "Missing artifact path")
    relative = Path(name)
    require(not relative.is_absolute() and ".." not in relative.parts,
            "Artifact path must stay inside the run folder")
    path = (folder / relative).resolve()
    require(path.is_relative_to(folder) and path.is_file(),
            "Missing artifact or artifact escapes the run folder: " + name)
    return path


def read_json(folder, name):
    value = json.loads(artifact(folder, name).read_text())
    require(isinstance(value, dict), "Expected a JSON object: " + name)
    return value


def check_evidence(folder, reference):
    require(isinstance(reference, dict), "Invalid check reference")
    record = read_json(folder, reference.get("record"))
    output = artifact(folder, reference.get("output"))
    require(hashlib.sha256(output.read_bytes()).hexdigest() == reference.get("output_sha256"),
            "Check output hash differs: " + reference["output"])
    command = record.get("command")
    require(isinstance(command, list) and command
            and all(isinstance(part, str) for part in command), "Missing exact command")
    require(type(record.get("exit_code")) is int, "Missing command exit code")
    require(not record.get("cleanup_error"), "Container cleanup failed")
    require(re.fullmatch(r"[0-9a-f]{64}", record.get("source_sha256", "")),
            "Missing source fingerprint")
    require(isinstance(record.get("image"), dict)
            and re.fullmatch(r"sha256:[0-9a-f]{64}", record["image"].get("id", "")),
            "Missing immutable image ID")
    return record


def check(folder, publish=False):
    folder = Path(folder).resolve()
    report = folder.with_suffix(".md")
    require(report.is_file() and report.read_text().strip(), "Missing dated report")
    result = read_json(folder, "result.json")
    status = result.get("status")
    require(status in {"verified", "promising", "no_improvement", "blocked"}, "Invalid status")
    require(isinstance(result.get("summary"), str) and result["summary"].strip(), "Missing summary")
    if status != "verified":
        require(not publish, "Only verified improvements may publish project code")
        require(not result.get("publication"), "Unverified result claims code publication")
        return status

    require(result.get("kind") in {"bug", "feature", "performance"}, "Invalid improvement kind")
    require(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", result.get("upstream", "")),
            "Missing upstream repository")
    for key in ("baseline_commit", "candidate_commit"):
        require(re.fullmatch(r"[0-9a-f]{40}", result.get(key, "")), "Missing exact " + key)
    require(result["baseline_commit"] != result["candidate_commit"], "Candidate equals baseline")
    require(artifact(folder, result.get("claim")).read_text().strip(), "Empty claim")
    checks = result.get("checks", {})
    require(isinstance(checks, dict), "Missing checks")
    before = check_evidence(folder, checks.get("before"))
    after = check_evidence(folder, checks.get("after"))
    require(before["command"] == after["command"], "Before/after commands differ")
    require(before["image"]["id"] == after["image"]["id"], "Before/after images differ")
    require(before.get("upstream_or_head_commit") == result["baseline_commit"], "Wrong baseline commit")
    require(after.get("upstream_or_head_commit") == result["candidate_commit"], "Wrong candidate commit")
    require(before["source_sha256"] != after["source_sha256"], "Before/after sources are identical")
    require(after["source_sha256"] == result.get("candidate_source_sha256"), "Wrong candidate source")
    if result["kind"] == "performance":
        require(before["exit_code"] == 0, "Performance baseline failed")
    else:
        require(0 < before["exit_code"] < 124, "Baseline must show a bounded regression failure")
    require(after["exit_code"] == 0, "Changed check failed")
    acceptance = checks.get("acceptance")
    require(isinstance(acceptance, list) and acceptance, "Missing existing acceptance checks")
    for reference in acceptance:
        record = check_evidence(folder, reference)
        require(record["exit_code"] == 0, "Acceptance check failed")
        require(record["source_sha256"] == after["source_sha256"], "Acceptance checked another source")

    for role in ("reproduce", "novelty", "criterion"):
        review = read_json(folder, "reviews/" + role + ".json")
        require(review.get("role") == role and review.get("context") == "fresh agent",
                "Missing fresh reviewer declaration: " + role)
        require(review.get("candidate_commit") == result["candidate_commit"], "Review is for another commit: " + role)
        require(review.get("pass") is True, "Reviewer did not pass: " + role)
        require(isinstance(review.get("summary"), str) and review["summary"].strip(), "Missing review summary")
        evidence = review.get("evidence")
        require(isinstance(evidence, list) and evidence
                and all(isinstance(item, str) and item.strip() for item in evidence), "Missing review evidence")
        if role == "criterion":
            require(isinstance(review.get("confirmed_scope"), str)
                    and review["confirmed_scope"].strip(), "Missing confirmed scope")

    publication = result.get("publication")
    if publication is not None:
        require(isinstance(publication, dict), "Invalid publication record")
        require(re.fullmatch(r"Someblueman/[A-Za-z0-9_.-]+", publication.get("repository", "")),
                "Publication must name the authorized account")
        require(publication.get("parent") == result.get("upstream") and result.get("upstream"),
                "Fork parent differs from upstream")
        require(publication.get("commit") == publication.get("remote_commit") == result["candidate_commit"],
                "Remote commit differs from verified candidate")
        require(isinstance(publication.get("branch"), str) and publication["branch"].startswith("nightly/"),
                "Missing nightly publication branch")
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", help="dated run folder, e.g. runs/2026-10-14")
    parser.add_argument("--publish", action="store_true", help="require a verified improvement")
    args = parser.parse_args()
    try:
        status = check(args.run, args.publish)
    except (ValueError, OSError, TypeError) as error:
        print("CHECK_RUN: FAIL - " + str(error))
        return 1
    print("CHECK_RUN: PASS (" + status + ")")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
