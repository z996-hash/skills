#!/usr/bin/env python3
"""Collect local system information for deep learning reproduction."""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def run_command(args: list[str], timeout: int = 20) -> dict[str, Any]:
    exe = shutil.which(args[0])
    if exe is None:
        return {"available": False, "args": args, "returncode": None, "stdout": "", "stderr": "not found"}
    try:
        proc = subprocess.run(
            [exe, *args[1:]],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        return {
            "available": True,
            "args": [exe, *args[1:]],
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except Exception as exc:  # pragma: no cover - defensive runtime collection
        return {"available": True, "args": [exe, *args[1:]], "returncode": None, "stdout": "", "stderr": repr(exc)}


def parse_nvidia_smi(text: str) -> dict[str, Any]:
    info: dict[str, Any] = {}
    match = re.search(r"CUDA Version:\s*([0-9.]+)", text)
    if match:
        info["reported_cuda_runtime"] = match.group(1)
    match = re.search(r"Driver Version:\s*([0-9.]+)", text)
    if match:
        info["driver_version"] = match.group(1)
    return info


def collect_gpu_query() -> list[dict[str, str]]:
    result = run_command(
        [
            "nvidia-smi",
            "--query-gpu=name,memory.total,driver_version",
            "--format=csv,noheader",
        ]
    )
    if not result["available"] or result["returncode"] != 0:
        return []
    gpus = []
    for line in result["stdout"].splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) >= 3:
            gpus.append({"name": parts[0], "memory_total": parts[1], "driver_version": parts[2]})
    return gpus


def collect_filesystem(path: Path) -> dict[str, Any]:
    result = run_command(["df", "-T", str(path)])
    payload: dict[str, Any] = {"command": result}
    if result.get("available") and result.get("returncode") == 0:
        lines = [line for line in result.get("stdout", "").splitlines() if line.strip()]
        if len(lines) >= 2:
            parts = lines[-1].split()
            if len(parts) >= 7:
                payload.update(
                    {
                        "filesystem": parts[0],
                        "type": parts[1],
                        "size": parts[2],
                        "used": parts[3],
                        "available": parts[4],
                        "use_percent": parts[5],
                        "mounted_on": parts[6],
                    }
                )
    return payload


def collect_existing_frameworks() -> dict[str, Any]:
    code = (
        "import json\n"
        "out={}\n"
        "for name in ['torch','torchvision','torchaudio','tensorflow','jax','jaxlib','numpy']:\n"
        "    try:\n"
        "        m=__import__(name)\n"
        "        out[name]=getattr(m,'__version__','unknown')\n"
        "    except Exception as e:\n"
        "        out[name]=None\n"
        "try:\n"
        "    import torch\n"
        "    out['torch_cuda_available']=torch.cuda.is_available()\n"
        "    out['torch_cuda_version']=getattr(torch.version,'cuda',None)\n"
        "except Exception:\n"
        "    pass\n"
        "print(json.dumps(out))\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        return {"error": proc.stderr.strip()}
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"raw": proc.stdout.strip()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", "-o", type=Path, help="Write JSON output to this file.")
    parser.add_argument("--cwd", type=Path, default=Path.cwd(), help="Directory used for disk-space reporting.")
    args = parser.parse_args()

    nvidia_full = run_command(["nvidia-smi"])
    conda_info = run_command(["conda", "info", "--json"])
    conda_envs = run_command(["conda", "env", "list", "--json"])
    conda_config_dirs = run_command(["conda", "config", "--show", "envs_dirs", "pkgs_dirs", "--json"])
    mamba_version = run_command(["mamba", "--version"])
    nvcc_version = run_command(["nvcc", "--version"])

    disk = shutil.disk_usage(args.cwd)
    payload: dict[str, Any] = {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "python": {
            "executable": sys.executable,
            "version": platform.python_version(),
        },
        "environment": {
            "cwd": str(args.cwd.resolve()),
            "conda_executable": shutil.which("conda"),
            "mamba_executable": shutil.which("mamba"),
            "nvcc_executable": shutil.which("nvcc"),
            "path": os.environ.get("PATH", ""),
        },
        "disk": {
            "path": str(args.cwd.resolve()),
            "total_bytes": disk.total,
            "used_bytes": disk.used,
            "free_bytes": disk.free,
        },
        "filesystem": {
            "cwd": collect_filesystem(args.cwd.resolve()),
            "home": collect_filesystem(Path.home()),
        },
        "gpu": {
            "nvidia_smi": nvidia_full,
            "parsed": parse_nvidia_smi(nvidia_full.get("stdout", "")),
            "devices": collect_gpu_query(),
            "nvcc": nvcc_version,
        },
        "conda": conda_info,
        "conda_envs": conda_envs,
        "conda_config_dirs": conda_config_dirs,
        "mamba": mamba_version,
        "existing_frameworks": collect_existing_frameworks(),
    }

    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
