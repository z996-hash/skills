#!/usr/bin/env python3
"""Generate a conservative environment plan from system and project inspection JSON."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Optional


def load_json(path: Optional[Path]) -> dict[str, Any]:
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


def reported_cuda(system: dict[str, Any]) -> Optional[str]:
    return (
        system.get("gpu", {})
        .get("parsed", {})
        .get("reported_cuda_runtime")
    )


def choose_cuda_build(cuda: Optional[str]) -> Optional[str]:
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


def choose_installer(system: dict[str, Any]) -> str:
    if system.get("environment", {}).get("mamba_executable"):
        return "mamba"
    return "conda"


def pip_spec_from_command(command: str) -> str:
    prefix = "pip install "
    if command.startswith(prefix):
        return command[len(prefix):].strip()
    return command.strip()


def contains_dep(deps: list[str], pattern: str) -> bool:
    regex = re.compile(pattern, re.IGNORECASE)
    return any(regex.search(dep) for dep in deps)


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
    env_name = env_base
    python_version = choose_python(project)
    frameworks = set(project.get("frameworks") or [])
    deps = flatten_dependencies(project)
    cuda_build = choose_cuda_build(reported_cuda(system))
    gpu_available = has_gpu(system)
    installer = choose_installer(system)

    conda_commands = [f"{installer} create -y -n {env_name} python={python_version} pip"]
    pip_commands = []
    warnings = []
    speed_hints = []

    if "pytorch" in frameworks:
        if gpu_available and cuda_build:
            conda_commands.append(
                f"{installer} install -y -n {env_name} --override-channels -c pytorch -c nvidia -c defaults pytorch torchvision torchaudio pytorch-cuda={cuda_build}"
            )
        else:
            conda_commands.append(f"{installer} install -y -n {env_name} --override-channels -c pytorch -c defaults pytorch torchvision torchaudio cpuonly")
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
    if contains_dep(deps, r"pytorch[-_]?lightning\s*[=<>!~]*\s*1\."):
        warnings.append("Old PyTorch Lightning detected; if tensorboard/distutils import fails, pin setuptools==59.5.0.")
    if contains_dep(deps, r"transformers") and not contains_dep(deps, r"transformers\s*=="):
        warnings.append("Unpinned transformers detected; old code may need an older release if top_k_top_p_filtering is imported.")
    if system.get("filesystem", {}).get("cwd", {}).get("type", "").lower() in {"nfs", "nfs4", "cifs", "smbfs"}:
        speed_hints.append("Current workspace appears to be on a network filesystem; large conda transactions may be slow.")
    if installer == "mamba":
        speed_hints.append("Use mamba for solver-heavy transactions.")
    else:
        speed_hints.append("Install mamba first if conda solving is repeatedly slow.")
    speed_hints.extend(
        [
            "Avoid exploratory conda search unless strictly necessary.",
            "Keep framework install channels narrow with --override-channels.",
            "Do not clone or rename the final environment after compiled extensions are built.",
            "Use iteration logs such as install.iter1.log; keep the environment name stable.",
        ]
    )

    env_yml = {
        "name": env_name,
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
        env_yml["dependencies"].append({"pip": [pip_spec_from_command(cmd) for cmd in pip_commands]})

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
        "env_name": env_name,
        "python_version": python_version,
        "installer": installer,
        "frameworks": sorted(frameworks),
        "reported_cuda_runtime": reported_cuda(system),
        "chosen_pytorch_cuda_build": cuda_build,
        "conda_commands": conda_commands,
        "pip_commands_after_activation": pip_commands,
        "environment_yml": str(args.environment_yml),
        "warnings": warnings,
        "speed_hints": speed_hints,
        "validation": {
            "default_batch_size": 4,
            "oom_retry_batch_size": 1,
            "do_not_run_full_training_by_default": True,
        },
        "repair_policy": {
            "stable_env_name": env_name,
            "package_level_repair_first": True,
            "rebuild_same_env_name_if_base_stack_is_wrong": True,
            "never_clone_or_alias_successful_env": True,
            "remove_broken_env_if_final_result_fails": True,
        },
    }

    text = json.dumps(plan, indent=2, ensure_ascii=False)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
