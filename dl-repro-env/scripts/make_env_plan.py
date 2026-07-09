#!/usr/bin/env python3
"""Generate a conservative environment plan from system and project inspection JSON."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def load_json(path: Path | None) -> dict[str, Any]:
    if not path:
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return value[:48] or "project"


def choose_python(project: dict[str, Any]) -> str:
    candidates = project.get("python_candidates") or []
    joined = " ".join(candidates)
    for version in ["3.8", "3.9", "3.10", "3.7", "3.11"]:
        if version in joined:
            return version
    dependency_text = json.dumps(project.get("dependency_entries", {}), ensure_ascii=False).lower()
    if "tensorflow-gpu" in dependency_text or "tf.contrib" in dependency_text:
        return "3.8"
    return "3.10"


def reported_cuda(system: dict[str, Any]) -> str | None:
    return (
        system.get("gpu", {})
        .get("parsed", {})
        .get("reported_cuda_runtime")
    )


def choose_cuda_build(cuda: str | None) -> str | None:
    if not cuda:
        return None
    try:
        major, minor = [int(part) for part in cuda.split(".")[:2]]
    except Exception:
        return None
    value = major + minor / 10
    if value >= 12.4:
        return "12.4"
    if value >= 12.1:
        return "12.1"
    if value >= 11.8:
        return "11.8"
    return None


def has_gpu(system: dict[str, Any]) -> bool:
    return bool(system.get("gpu", {}).get("devices"))


def flatten_dependencies(project: dict[str, Any]) -> list[str]:
    deps = []
    for entries in (project.get("dependency_entries") or {}).values():
        deps.extend(entries)
    return deps


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--system", type=Path, help="system_info.json from collect_system_info.py")
    parser.add_argument("--project", type=Path, help="project_inspection.json from inspect_project.py")
    parser.add_argument("--repo-name", help="Repository name override for environment naming.")
    parser.add_argument("--output", "-o", type=Path, help="Write plan JSON to this file.")
    parser.add_argument("--environment-yml", type=Path, default=Path("environment.repro.yml"))
    args = parser.parse_args()

    system = load_json(args.system)
    project = load_json(args.project)
    repo_path = Path(project.get("repo", args.repo_name or "project"))
    repo_name = args.repo_name or repo_path.name
    env_base = f"repro-{slugify(repo_name)}"
    attempt_name = f"{env_base}-try1"
    python_version = choose_python(project)
    frameworks = set(project.get("frameworks") or [])
    deps = flatten_dependencies(project)
    cuda_build = choose_cuda_build(reported_cuda(system))
    gpu_available = has_gpu(system)

    conda_commands = [f"conda create -y -n {attempt_name} python={python_version}"]
    pip_commands = []
    warnings = []

    if "pytorch" in frameworks:
        if gpu_available and cuda_build:
            conda_commands.append(
                f"conda install -y -n {attempt_name} pytorch torchvision torchaudio pytorch-cuda={cuda_build} -c pytorch -c nvidia"
            )
        else:
            conda_commands.append(f"conda install -y -n {attempt_name} pytorch torchvision torchaudio cpuonly -c pytorch")
            warnings.append("No compatible NVIDIA GPU/CUDA runtime detected; planned CPU-only PyTorch.")
    if "tensorflow" in frameworks:
        pip_commands.append("pip install tensorflow")
        if any("tensorflow-gpu" in dep.lower() for dep in deps):
            warnings.append("Legacy tensorflow-gpu detected; prefer modern tensorflow package or Docker/WSL2 for old GPU stacks.")
    if "jax" in frameworks:
        pip_commands.append("pip install jax")
        warnings.append("Verify current official JAX CUDA wheel instructions before GPU install.")

    req_files = [
        file
        for file in (project.get("dependency_entries") or {}).keys()
        if Path(file).name.lower().startswith("requirements") and file.lower().endswith(".txt")
    ]
    for req in req_files[:3]:
        pip_commands.append(f"pip install -r {req}")

    if not frameworks:
        warnings.append("No major framework detected; install project dependencies conservatively, then validate imports.")
    if project.get("custom_extensions", {}).get("native_file_count"):
        warnings.append("Native/CUDA files detected; source builds may need compiler/CUDA toolkit alignment.")
    if "numpy" in project.get("risk_packages", []):
        warnings.append("If old compiled packages fail, try pinning numpy<2.")

    env_yml = {
        "name": attempt_name,
        "channels": ["pytorch", "nvidia", "conda-forge", "defaults"],
        "dependencies": [f"python={python_version}", "pip"],
    }
    if "pytorch" in frameworks:
        env_yml["dependencies"].extend(["pytorch", "torchvision", "torchaudio"])
        if gpu_available and cuda_build:
            env_yml["dependencies"].append(f"pytorch-cuda={cuda_build}")
        else:
            env_yml["dependencies"].append("cpuonly")
    if pip_commands:
        env_yml["dependencies"].append({"pip": [cmd.removeprefix("pip install ").strip() for cmd in pip_commands]})

    yml_lines = [f"name: {env_yml['name']}", "channels:"]
    yml_lines.extend([f"  - {channel}" for channel in env_yml["channels"]])
    yml_lines.append("dependencies:")
    for dep in env_yml["dependencies"]:
        if isinstance(dep, str):
            yml_lines.append(f"  - {dep}")
        else:
            yml_lines.append("  - pip:")
            for pip_dep in dep["pip"]:
                yml_lines.append(f"      - {pip_dep}")
    args.environment_yml.write_text("\n".join(yml_lines) + "\n", encoding="utf-8")

    plan = {
        "repo_name": repo_name,
        "final_env_name": env_base,
        "first_attempt_env_name": attempt_name,
        "python_version": python_version,
        "frameworks": sorted(frameworks),
        "reported_cuda_runtime": reported_cuda(system),
        "chosen_pytorch_cuda_build": cuda_build,
        "conda_commands": conda_commands,
        "pip_commands_after_activation": pip_commands,
        "environment_yml": str(args.environment_yml),
        "warnings": warnings,
        "validation": {
            "default_batch_size": 4,
            "oom_retry_batch_size": 1,
            "do_not_run_full_training_by_default": True,
        },
        "cleanup_policy": {
            "remove_failed_attempt_envs": True,
            "keep_only_final_success_env": True,
            "never_remove_base_or_unmatched_envs": True,
        },
    }

    text = json.dumps(plan, indent=2, ensure_ascii=False)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
