#!/usr/bin/env python3
"""Run fast smoke validation inside a candidate reproduction environment."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Optional


def test_import(name: str) -> dict[str, Any]:
    started = time.time()
    try:
        module = importlib.import_module(name)
        return {
            "ok": True,
            "module": name,
            "version": getattr(module, "__version__", "unknown"),
            "seconds": round(time.time() - started, 3),
        }
    except Exception as exc:
        return {"ok": False, "module": name, "error": repr(exc), "seconds": round(time.time() - started, 3)}


def test_torch_cuda() -> dict[str, Any]:
    try:
        import torch

        payload: dict[str, Any] = {
            "ok": True,
            "torch_version": torch.__version__,
            "torch_cuda_version": getattr(torch.version, "cuda", None),
            "cuda_available": torch.cuda.is_available(),
            "device_count": torch.cuda.device_count(),
        }
        if torch.cuda.is_available():
            device = torch.device("cuda:0")
            tensor = torch.zeros((16, 16), device=device)
            payload["allocation_ok"] = bool(tensor.sum().item() == 0)
            payload["device_name"] = torch.cuda.get_device_name(0)
            payload["memory_allocated"] = torch.cuda.memory_allocated(0)
        return payload
    except Exception as exc:
        return {"ok": False, "error": repr(exc)}


def test_tensorflow_gpu() -> dict[str, Any]:
    try:
        import tensorflow as tf

        gpus = tf.config.list_physical_devices("GPU")
        return {"ok": True, "tensorflow_version": tf.__version__, "gpu_count": len(gpus), "gpus": [str(gpu) for gpu in gpus]}
    except Exception as exc:
        return {"ok": False, "error": repr(exc)}


def test_repo_import(repo: Path) -> dict[str, Any]:
    if not repo.exists():
        return {"ok": False, "error": f"repo does not exist: {repo}"}
    candidates = []
    for child in repo.iterdir():
        if child.is_dir() and (child / "__init__.py").exists() and not child.name.startswith("."):
            candidates.append(child.name)
    results = []
    sys.path.insert(0, str(repo))
    for name in candidates[:10]:
        results.append(test_import(name))
    return {"ok": any(item.get("ok") for item in results) if results else None, "candidates": candidates[:10], "results": results}


def run_command(command: str, cwd: Optional[Path], timeout: int, env: dict[str, str]) -> dict[str, Any]:
    started = time.time()
    proc = subprocess.run(
        command,
        shell=True,
        cwd=str(cwd) if cwd else None,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )
    return {
        "command": command,
        "returncode": proc.returncode,
        "ok": proc.returncode == 0,
        "seconds": round(time.time() - started, 3),
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
    }


def append_batch_arg(command: str, mode: str, batch_size: int) -> str:
    if mode == "none":
        return command
    if mode == "underscore":
        return f"{command} --batch_size {batch_size}"
    if mode == "dash":
        return f"{command} --batch-size {batch_size}"
    if mode == "bs":
        return f"{command} --bs {batch_size}"
    return command


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, help="Repository path to import-test and use as command cwd.")
    parser.add_argument("--command", action="append", help="Optional smoke command to run. Can be repeated.")
    parser.add_argument("--timeout", type=int, default=600, help="Timeout per command in seconds.")
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--oom-retry-batch-size", type=int, default=1)
    parser.add_argument("--append-batch-arg", choices=["none", "underscore", "dash", "bs"], default="none")
    parser.add_argument("--output", "-o", type=Path, help="Write JSON result to this file.")
    args = parser.parse_args()

    env = dict(os.environ)
    env.setdefault("PYTHONUNBUFFERED", "1")
    payload: dict[str, Any] = {
        "python": {"executable": sys.executable, "version": sys.version},
        "imports": {},
        "cuda": {},
        "repo_import": None,
        "commands": [],
        "batch_size": args.batch_size,
    }

    for module in ["torch", "torchvision", "torchaudio", "tensorflow", "jax", "numpy"]:
        payload["imports"][module] = test_import(module)
    payload["cuda"]["torch"] = test_torch_cuda()
    payload["cuda"]["tensorflow"] = test_tensorflow_gpu()
    if args.repo:
        payload["repo_import"] = test_repo_import(args.repo.resolve())

    for command in args.command or []:
        command_with_batch = append_batch_arg(command, args.append_batch_arg, args.batch_size)
        result = run_command(command_with_batch, args.repo, args.timeout, env)
        if not result["ok"] and "out of memory" in (result["stderr_tail"] + result["stdout_tail"]).lower():
            retry_command = append_batch_arg(command, args.append_batch_arg, args.oom_retry_batch_size)
            retry = run_command(retry_command, args.repo, args.timeout, env)
            retry["oom_retry"] = True
            retry["batch_size"] = args.oom_retry_batch_size
            payload["commands"].append(result)
            payload["commands"].append(retry)
        else:
            result["batch_size"] = args.batch_size if args.append_batch_arg != "none" else None
            payload["commands"].append(result)

    hard_failures = []
    torch_import = payload["imports"]["torch"]
    if torch_import["ok"] and not payload["cuda"]["torch"].get("ok"):
        hard_failures.append("torch import succeeded but CUDA/tensor allocation test failed")
    for result in payload["commands"]:
        if not result.get("ok"):
            hard_failures.append(f"command failed: {result.get('command')}")
    payload["ok"] = not hard_failures
    payload["hard_failures"] = hard_failures

    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
