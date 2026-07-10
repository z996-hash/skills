#!/usr/bin/env python3
"""Safely remove a final-named reproduction conda environment before rebuilding it."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Optional


SAFE_ENV_RE = re.compile(r"^repro-[a-z0-9][a-z0-9-]*$")
PROTECTED_NAMES = {"base", "root"}


def run_conda(args: list[str]) -> subprocess.CompletedProcess:
    exe = shutil.which("conda")
    if not exe:
        raise SystemExit("conda not found")
    return subprocess.run(
        [exe, *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def conda_envs() -> dict[str, str]:
    proc = run_conda(["env", "list", "--json"])
    if proc.returncode != 0:
        raise SystemExit(proc.stderr.strip() or proc.stdout.strip())
    payload = json.loads(proc.stdout)
    envs = {}
    for env_path in payload.get("envs", []):
        envs[Path(env_path).name] = env_path
    return envs


def marker_path(env_path: str) -> Path:
    return Path(env_path) / "conda-meta" / "dl-repro-env.json"


def read_marker(env_path: str) -> Optional[dict[str, Any]]:
    path = marker_path(env_path)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def remove_env(name: str) -> dict[str, object]:
    proc = run_conda(["env", "remove", "-y", "-n", name])
    return {
        "name": name,
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-2000:],
        "stderr_tail": proc.stderr[-2000:],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-name", required=True, help="Final environment name, for example repro-canonicalvae.")
    parser.add_argument("--yes", action="store_true", help="Actually remove the environment. Default is dry-run.")
    parser.add_argument(
        "--allow-unmarked",
        action="store_true",
        help="Allow removing a matching repro-* environment even when no dl-repro-env marker is present.",
    )
    args = parser.parse_args()

    name = args.env_name.strip()
    if name in PROTECTED_NAMES or not SAFE_ENV_RE.match(name):
        raise SystemExit("Unsafe environment name. Expected a final name like repro-project-name.")

    envs = conda_envs()
    env_path = envs.get(name)
    if not env_path:
        print(json.dumps({"exists": False, "env_name": name, "dry_run": not args.yes}, indent=2, ensure_ascii=False))
        return 0

    marker = read_marker(env_path)
    if marker is None and not args.allow_unmarked:
        raise SystemExit(
            f"Refusing to remove unmarked environment {name}. "
            "Pass --allow-unmarked only after confirming it is safe to reset."
        )

    result: dict[str, Any] = {
        "exists": True,
        "env_name": name,
        "env_path": env_path,
        "marker": marker,
        "dry_run": not args.yes,
        "removed": None,
    }
    if args.yes:
        result["removed"] = remove_env(name)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
