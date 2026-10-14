#!/usr/bin/env python3
"""Record a nightly deadline and run source checks in bounded Docker containers."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent


def now() -> datetime:
    return datetime.now(timezone.utc)


def write_json(path: Path, value: dict) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def read_session() -> dict:
    path = ROOT / ".work/session.json"
    if not path.exists():
        raise ValueError("No session. Run 'python3 night.py begin' first.")
    return json.loads(path.read_text())


def remaining(session: dict) -> float:
    if session["closed"]:
        return 0
    return max(0, (datetime.fromisoformat(session["deadline"]) - now()).total_seconds())


def begin(minutes: int) -> dict:
    current = now()
    today = current.astimezone(ZoneInfo("Europe/London")).date().isoformat()
    path = ROOT / ".work/session.json"
    if path.exists():
        previous = read_session()
        if previous["date"] == today or remaining(previous) > 0:
            return previous  # Never renew an active or already-used daily budget.
    session = {
        "date": today,
        "started": current.isoformat(),
        "deadline": (current + timedelta(minutes=minutes)).isoformat(),
        "closed": False,
    }
    write_json(path, session)
    return session


def snapshot(checkout: Path, destination: Path) -> tuple[str, str]:
    """Copy source, preserving symlinks without following them on the host."""
    checkout = checkout.resolve()
    allowed = (ROOT / ".work/checkouts").resolve()
    if not checkout.is_relative_to(allowed) or checkout == allowed:
        raise ValueError("Checkout must be inside .work/checkouts/.")
    top = subprocess.check_output(
        ["git", "-C", str(checkout), "rev-parse", "--show-toplevel"], timeout=10
    ).decode().strip()
    if Path(top).resolve() != checkout:
        raise ValueError("Checkout must be the selected repository's root.")
    base = subprocess.check_output(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"], timeout=10
    ).decode().strip()
    names = subprocess.check_output(
        ["git", "-C", str(checkout), "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        timeout=10,
    ).split(b"\0")
    digest = hashlib.sha256()
    destination.mkdir()
    for name in sorted(set(names) - {b""}):
        relative = Path(os.fsdecode(name))
        if relative.is_absolute() or ".." in relative.parts or ".git" in relative.parts:
            raise ValueError("Unsafe source path in Git index.")
        source = checkout / relative
        if not source.parent.resolve().is_relative_to(checkout):
            raise ValueError("Source parent escapes checkout.")
        if not os.path.lexists(source):
            continue  # A tracked file deleted by the patch.
        if not source.is_symlink() and source.is_dir():
            raise ValueError("Submodules are unsupported; choose another project.")
        target = destination / relative
        if any((destination / parent).is_symlink() for parent in relative.parents):
            raise ValueError("Source paths traverse a symlink.")
        target.parent.mkdir(parents=True, exist_ok=True)
        digest.update(name + b"\0")
        if source.is_symlink():
            link = os.readlink(source)
            target.symlink_to(link)
            digest.update(b"link\0" + os.fsencode(link) + b"\0")
        else:
            shutil.copy2(source, target)
            digest.update(str(source.stat().st_mode & 0o777).encode() + b"\0")
            digest.update(hashlib.sha256(target.read_bytes()).digest())
    return base, digest.hexdigest()


def check(args: argparse.Namespace) -> int:
    session = read_session()
    if remaining(session) <= 20:
        raise ValueError("Session closed or budget exhausted. Do not restart it today.")
    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise ValueError("Supply a container command after --.")
    image = json.loads(subprocess.check_output(
        ["docker", "image", "inspect", args.image, "--format",
         '{"id":{{json .Id}},"digests":{{json .RepoDigests}}}'],
        timeout=10,
    ))
    check_id = uuid.uuid4().hex[:12]
    evidence = ROOT / ".work/evidence" / session["date"] / check_id
    evidence.mkdir(parents=True)
    source = evidence / "source"
    base, fingerprint = snapshot(Path(args.checkout), source)
    name = "nightly-oss-" + check_id
    record = {
        "started": now().isoformat(), "upstream_or_head_commit": base,
        "source_sha256": fingerprint, "image": image, "command": command,
        "exit_code": None,
    }
    # Docker Desktop can mount /private/tmp without access to macOS Documents.
    # Keep the retained input unchanged even when the container edits its copy.
    with tempfile.TemporaryDirectory(prefix="nightly-oss-", dir="/tmp") as directory:
        runtime = Path(directory).resolve() / "source"
        shutil.copytree(source, runtime, symlinks=True)
        seconds = min(args.timeout, remaining(session) - 15)
        if seconds <= 0:
            raise ValueError("Budget expired during preparation.")
        docker = [
            "docker", "run", "--rm", "--name", name, "--pull", "never",
            "--init", "--user", f"{os.getuid()}:{os.getgid()}",
            "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
            "--pids-limit", "256", "--cpus", "2", "--memory", "4g", "--read-only",
            "--tmpfs", "/tmp:rw,nosuid,size=1g",
            "--mount", f"type=bind,src={runtime},dst=/work",
            "--workdir", "/work", image["id"], *command,
        ]
        record["timeout_seconds"] = seconds
        write_json(evidence / "result.json", record)
        started = time.monotonic()
        try:
            with (evidence / "output.log").open("wb") as log:
                result = subprocess.run(docker, stdout=log, stderr=subprocess.STDOUT, timeout=seconds)
            code = result.returncode
        except subprocess.TimeoutExpired:
            code = 124
        except KeyboardInterrupt:
            code = 130
        finally:
            # Killing the Docker client alone does not stop its container.
            try:
                cleanup = subprocess.run(
                    ["docker", "rm", "-f", name], capture_output=True, timeout=10
                )
                if cleanup.returncode and b"No such container" not in cleanup.stderr:
                    record["cleanup_error"] = cleanup.stderr.decode(errors="replace")
            except subprocess.TimeoutExpired:
                record["cleanup_error"] = "Docker cleanup timed out; inspect the named container."
            record["container_name"] = name
            record["elapsed_seconds"] = round(time.monotonic() - started, 3)
    record["exit_code"] = code
    write_json(evidence / "result.json", record)
    print(json.dumps({"evidence": str(evidence.relative_to(ROOT)), **record}, indent=2))
    return code if code else int("cleanup_error" in record)


def bounded_minutes(value: str) -> int:
    number = int(value)
    if not 1 <= number <= 90:
        raise argparse.ArgumentTypeError("minutes must be between 1 and 90")
    return number


def bounded_seconds(value: str) -> int:
    number = int(value)
    if not 1 <= number <= 5400:
        raise argparse.ArgumentTypeError("timeout must be between 1 and 5400 seconds")
    return number


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    start = commands.add_parser("begin", help="start or read today's fixed budget")
    start.add_argument("--minutes", type=bounded_minutes, default=90)
    commands.add_parser("status", help="show the deadline and remaining seconds")
    commands.add_parser("end", help="close the session without renewing its budget")
    run = commands.add_parser("run", help="run a check on a disposable source copy")
    run.add_argument("--checkout", required=True)
    run.add_argument("--image", required=True, help="an already-pulled official language image")
    run.add_argument("--timeout", type=bounded_seconds, default=600)
    run.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    work = ROOT / ".work"
    work.mkdir(exist_ok=True)
    try:
        with (work / "lock").open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise ValueError("Another helper command is active; do not overlap checks.") from None
            if args.action == "run":
                return check(args)
            session = begin(args.minutes) if args.action == "begin" else read_session()
            if args.action == "end":
                session["closed"] = True
                write_json(work / "session.json", session)
            print(json.dumps({**session, "seconds_remaining": int(remaining(session))}, indent=2))
            return 0
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print(f"night.py: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
