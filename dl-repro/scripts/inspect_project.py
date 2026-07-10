#!/usr/bin/env python3
"""Inspect a deep learning repository for dependency and validation signals."""

from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Optional


SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".venv",
    "venv",
    "env",
    "data",
    "datasets",
    "checkpoints",
    "weights",
    "logs",
    "runs",
    "outputs",
    "repro_logs",
    "dl-repro-env",
    ".codex-dl-repro-env",
}

SKIP_FILE_NAMES = {
    "system_info.json",
    "project_inspection.json",
    "repro_env_plan.json",
    "environment.repro.yml",
    "environment.repro.yaml",
    "repro_env_report.md",
}

SKIP_FILE_PATTERNS = [
    re.compile(r"^install\.iter\d+\.log$"),
    re.compile(r"^install\.try\d+\.log$"),
    re.compile(r"^smoke_test\.iter\d+\.json$"),
    re.compile(r"^smoke_test\.try\d+\.json$"),
    re.compile(r"^error\.iter\d+\.json$"),
    re.compile(r"^error\.try\d+\.json$"),
]

DEPENDENCY_NAMES = {
    "environment.yml",
    "environment.yaml",
    "conda.yml",
    "conda.yaml",
    "requirements.txt",
    "setup.py",
    "setup.cfg",
    "pyproject.toml",
    "Pipfile",
    "Dockerfile",
}

FRAMEWORK_PATTERNS = {
    "pytorch": [r"\btorch\b", r"pytorch", r"torchvision", r"torchaudio"],
    "tensorflow": [r"tensorflow", r"tensorflow-gpu", r"\btf\."],
    "jax": [r"\bjax\b", r"jaxlib", r"flax", r"haiku"],
    "paddle": [r"paddlepaddle", r"\bpaddle\b"],
    "openmmlab": [r"\bmmcv\b", r"\bmmcv-full\b", r"\bmmdet\b", r"\bmmseg\b", r"\bmmengine\b"],
}

RISK_PACKAGES = [
    "torchvision",
    "torchaudio",
    "mmcv",
    "mmcv-full",
    "mmdet",
    "mmengine",
    "detectron2",
    "pytorch3d",
    "torch-scatter",
    "torch-sparse",
    "tensorflow-gpu",
    "cupy",
    "apex",
    "xformers",
    "flash-attn",
    "numpy",
    "opencv-python",
    "spconv",
    "kaolin",
]


def read_text(path: Path, limit: int = 200_000) -> str:
    try:
        data = path.read_bytes()[:limit]
        return data.decode("utf-8", errors="replace")
    except Exception:
        return ""


def iter_files(root: Path):
    for current, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".tox")]
        current_path = Path(current)
        for name in files:
            if name in SKIP_FILE_NAMES or any(pattern.match(name) for pattern in SKIP_FILE_PATTERNS):
                continue
            path = current_path / name
            try:
                if path.stat().st_size > 5_000_000:
                    continue
            except OSError:
                continue
            yield path


def classify_file(path: Path) -> Optional[str]:
    lower = path.name.lower()
    if lower in DEPENDENCY_NAMES:
        return "dependency"
    if lower.startswith("requirements") and lower.endswith(".txt"):
        return "dependency"
    if lower.startswith("environment") and lower.endswith((".yml", ".yaml")):
        return "dependency"
    if "readme" in lower or lower.startswith("install"):
        return "readme"
    if ".github" in path.parts and path.suffix in {".yml", ".yaml"}:
        return "ci"
    if path.suffix == ".py":
        return "python"
    if path.suffix in {".cu", ".cuh", ".cpp", ".cc", ".cxx", ".h", ".hpp"}:
        return "native"
    if "config" in [part.lower() for part in path.parts] or path.suffix in {".yaml", ".yml", ".json", ".toml", ".py"}:
        if any(token in path.name.lower() for token in ["config", "cfg", "option"]):
            return "config"
    return None


def extract_requirements(text: str) -> list[str]:
    reqs = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("-r "):
            continue
        if line.startswith(("-", "name:", "channels:", "dependencies:")):
            continue
        line = re.sub(r"\s+#.*$", "", line).strip()
        if line:
            reqs.append(line)
    return reqs


def extract_python_candidates(text: str) -> list[str]:
    patterns = [
        r"python\s*[=<>!~]+\s*([0-9]+(?:\.[0-9]+)?)",
        r"python_requires\s*=\s*['\"]([^'\"]+)['\"]",
        r"requires-python\s*=\s*['\"]([^'\"]+)['\"]",
    ]
    found = []
    for pattern in patterns:
        found.extend(re.findall(pattern, text, flags=re.IGNORECASE))
    return sorted(set(found))


def extract_commands(text: str) -> list[str]:
    commands = []
    for line in text.splitlines():
        stripped = line.strip().strip("`")
        if re.search(r"\b(python|torchrun|accelerate|bash|sh)\b", stripped) and re.search(
            r"\b(train|test|eval|demo|infer|main)\w*\.py\b", stripped
        ):
            commands.append(stripped)
    return commands[:25]


def detect_frameworks(all_text: str) -> list[str]:
    found = []
    for name, patterns in FRAMEWORK_PATTERNS.items():
        if any(re.search(pattern, all_text, flags=re.IGNORECASE) for pattern in patterns):
            found.append(name)
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", type=Path, help="Repository path to inspect.")
    parser.add_argument("--output", "-o", type=Path, help="Write JSON output to this file.")
    parser.add_argument("--max-python-files", type=int, default=250)
    args = parser.parse_args()

    repo = args.repo.resolve()
    if not repo.exists():
        raise SystemExit(f"Repository path does not exist: {repo}")

    files_by_type: dict[str, list[str]] = defaultdict(list)
    dependency_entries: dict[str, list[str]] = {}
    python_candidates: set[str] = set()
    commands: list[str] = []
    all_text_chunks: list[str] = []
    imports = Counter()
    native_files = []
    custom_extension_signals = []

    python_seen = 0
    for path in iter_files(repo):
        kind = classify_file(path)
        if kind is None:
            continue
        rel = str(path.relative_to(repo))
        files_by_type[kind].append(rel)
        text = read_text(path)
        if kind in {"dependency", "readme", "ci", "config"}:
            all_text_chunks.append(text[:50_000])
            commands.extend(extract_commands(text))
            python_candidates.update(extract_python_candidates(text))
        if kind == "dependency":
            dependency_entries[rel] = extract_requirements(text)
        if kind == "python" and python_seen < args.max_python_files:
            python_seen += 1
            all_text_chunks.append(text[:20_000])
            for match in re.findall(r"^\s*(?:import|from)\s+([A-Za-z0-9_\.]+)", text, flags=re.MULTILINE):
                imports[match.split(".")[0]] += 1
            if re.search(r"CUDAExtension|CppExtension|torch\.utils\.cpp_extension", text):
                custom_extension_signals.append(rel)
        if kind == "native":
            native_files.append(rel)

    all_text = "\n".join(all_text_chunks)
    risk_packages = [
        package
        for package in RISK_PACKAGES
        if re.search(r"(^|[^A-Za-z0-9_.-])" + re.escape(package) + r"([^A-Za-z0-9_.-]|$)", all_text, re.IGNORECASE)
    ]

    payload: dict[str, Any] = {
        "repo": str(repo),
        "files": {key: sorted(value)[:200] for key, value in files_by_type.items()},
        "dependency_entries": dependency_entries,
        "frameworks": detect_frameworks(all_text),
        "risk_packages": sorted(set(risk_packages)),
        "python_candidates": sorted(python_candidates),
        "top_imports": imports.most_common(50),
        "custom_extensions": {
            "python_signals": sorted(custom_extension_signals),
            "native_files_sample": sorted(native_files)[:100],
            "native_file_count": len(native_files),
        },
        "candidate_commands": sorted(set(commands))[:25],
        "notes": [],
    }

    if native_files or custom_extension_signals:
        payload["notes"].append("Custom native/CUDA extension signals found; verify compiler and CUDA toolkit needs.")
    if "tensorflow-gpu" in payload["risk_packages"]:
        payload["notes"].append("Legacy tensorflow-gpu dependency found; modern TensorFlow packaging may differ.")
    if not payload["frameworks"]:
        payload["notes"].append("No major deep learning framework detected from scanned files.")

    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
