#!/usr/bin/env python3
"""Mark a conda environment as managed by dl-repro-env."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SAFE_ENV_RE = re.compile(r"^repro-[a-z0-9][a-z0-9-]*$")


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
    return {Path(path).name: path for path in payload.get("envs", [])}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-name", required=True)
    parser.add_argument("--repo", help="Repository path or URL.")
    parser.add_argument("--commit", help="Repository commit hash.")
    parser.add_argument("--plan", type=Path, help="Optional repro_env_plan.json path to summarize in the marker.")
    args = parser.parse_args()

    env_name = args.env_name.strip()
    if not SAFE_ENV_RE.match(env_name):
        raise SystemExit("Unsafe environment name. Expected a name like repro-project-name.")

    envs = conda_envs()
    env_path = envs.get(env_name)
    if not env_path:
        raise SystemExit(f"Environment not found: {env_name}")

    marker_dir = Path(env_path) / "conda-meta"
    marker_dir.mkdir(parents=True, exist_ok=True)
    marker_path = marker_dir / "dl-repro-env.json"

    marker: dict[str, Any] = {
        "tool": "dl-repro-env",
        "env_name": env_name,
        "env_path": env_path,
        "repo": args.repo,
        "commit": args.commit,
        "created_or_updated_at": datetime.now(timezone.utc).isoformat(),
    }
    if args.plan and args.plan.exists():
        try:
            plan = json.loads(args.plan.read_text(encoding="utf-8"))
            marker["plan_summary"] = {
                "python_version": plan.get("python_version"),
                "frameworks": plan.get("frameworks"),
                "reported_cuda_runtime": plan.get("reported_cuda_runtime"),
                "chosen_pytorch_cuda_build": plan.get("chosen_pytorch_cuda_build"),
            }
        except Exception as exc:
            marker["plan_summary_error"] = repr(exc)

    marker_path.write_text(json.dumps(marker, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"marker": str(marker_path), "env_name": env_name}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
