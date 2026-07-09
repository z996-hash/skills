#!/usr/bin/env python3
"""Safely remove disposable conda attempt environments created by this workflow."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path


SAFE_ATTEMPT_RE = re.compile(r"^repro-[a-z0-9][a-z0-9-]*-try[0-9]+$")


def conda_envs() -> list[str]:
    exe = shutil.which("conda")
    if not exe:
        raise SystemExit("conda not found")
    proc = subprocess.run(
        [exe, "env", "list", "--json"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        raise SystemExit(proc.stderr.strip() or proc.stdout.strip())
    payload = json.loads(proc.stdout)
    names = []
    for env_path in payload.get("envs", []):
        names.append(Path(env_path).name)
    return names


def remove_env(name: str) -> dict[str, object]:
    exe = shutil.which("conda")
    assert exe
    proc = subprocess.run(
        [exe, "env", "remove", "-y", "-n", name],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return {"name": name, "returncode": proc.returncode, "stdout_tail": proc.stdout[-2000:], "stderr_tail": proc.stderr[-2000:]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix", required=True, help="Repository env prefix, for example repro-pointflowrenderer")
    parser.add_argument("--yes", action="store_true", help="Actually remove environments. Default is dry-run.")
    parser.add_argument("--keep", action="append", default=[], help="Environment name to keep. Can be repeated.")
    args = parser.parse_args()

    prefix = args.prefix.rstrip("-")
    if not re.match(r"^repro-[a-z0-9][a-z0-9-]*$", prefix):
        raise SystemExit("Unsafe prefix. Expected pattern like repro-project-name.")

    existing = conda_envs()
    targets = [
        name
        for name in existing
        if name.startswith(prefix + "-try") and SAFE_ATTEMPT_RE.match(name) and name not in set(args.keep)
    ]

    result = {"dry_run": not args.yes, "targets": targets, "removed": []}
    if args.yes:
        for name in targets:
            result["removed"].append(remove_env(name))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
