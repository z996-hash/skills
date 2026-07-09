#!/usr/bin/env python3
"""Classify deep learning environment install/runtime errors."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


PATTERNS: list[dict[str, Any]] = [
    {
        "category": "conda_solver",
        "regex": r"UnsatisfiableError|PackagesNotFoundError|ResolvePackageNotFound|ResolutionImpossible",
        "moves": ["Relax pins", "Use mamba", "Install core conda packages first, then pip packages"],
    },
    {
        "category": "cuda_framework_mismatch",
        "regex": r"Torch not compiled with CUDA enabled|CUDA driver version is insufficient|no kernel image is available|invalid device function|libcudart|cudart64",
        "moves": ["Install a framework CUDA build supported by the driver", "Avoid mixing pip and conda framework builds"],
    },
    {
        "category": "torchvision_abi",
        "regex": r"torchvision::nms|Couldn't load custom C\+\+ ops|undefined symbol|DLL load failed",
        "moves": ["Reinstall matching torch, torchvision, and torchaudio versions", "Remove duplicate framework installs"],
    },
    {
        "category": "numpy_abi",
        "regex": r"numpy\.dtype size changed|compiled using NumPy 1\.x|numpy\.core\.multiarray failed to import",
        "moves": ["Pin numpy<2 for older projects", "Reinstall compiled packages after changing NumPy"],
    },
    {
        "category": "custom_extension_build",
        "regex": r"CUDAExtension|CppExtension|fatal error: cuda\.h|nvcc fatal|Microsoft Visual C\+\+ 14\.0|gcc: error|cl\.exe",
        "moves": ["Prefer prebuilt wheels", "Verify compiler and CUDA toolkit only if source build is unavoidable"],
    },
    {
        "category": "openmmlab_binary",
        "regex": r"mmcv|mmcv-full|mmdet|mmengine|No module named mmcv\._ext",
        "moves": ["Match OpenMMLab package, PyTorch, and CUDA versions exactly", "Use official OpenMMLab wheel index"],
    },
    {
        "category": "missing_data_or_checkpoint",
        "regex": r"FileNotFoundError|No such file or directory|checkpoint|ckpt|dataset|weights",
        "moves": ["Report exact missing path", "Find documented dataset/checkpoint URL", "Validate imports separately"],
    },
    {
        "category": "out_of_memory",
        "regex": r"CUDA out of memory|CUBLAS_STATUS_ALLOC_FAILED|out of memory",
        "moves": ["Retry validation with batch size 1", "Reduce image size, point count, sequence length, or workers"],
    },
    {
        "category": "python_version",
        "regex": r"requires Python|Python version|SyntaxError|No matching distribution found",
        "moves": ["Adjust Python version to project constraints", "Check package wheels for the chosen Python version"],
    },
]


def read_sources(paths: list[Path]) -> str:
    if not paths:
        return sys.stdin.read()
    chunks = []
    for path in paths:
        try:
            chunks.append(path.read_text(encoding="utf-8", errors="replace"))
        except Exception as exc:
            chunks.append(f"\n[failed to read {path}: {exc!r}]\n")
    return "\n".join(chunks)


def classify(text: str) -> dict[str, Any]:
    hits = []
    for item in PATTERNS:
        matches = re.findall(item["regex"], text, flags=re.IGNORECASE)
        if matches:
            hits.append(
                {
                    "category": item["category"],
                    "match_count": len(matches),
                    "suggested_moves": item["moves"],
                }
            )
    if not hits:
        hits.append(
            {
                "category": "unknown",
                "match_count": 0,
                "suggested_moves": [
                    "Read the first real traceback above the final error",
                    "Check repository issues and official package docs",
                    "Try a smaller reproducible command",
                ],
            }
        )
    return {"categories": hits}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("logs", nargs="*", type=Path, help="Log files to classify. Reads stdin when omitted.")
    parser.add_argument("--output", "-o", type=Path, help="Write JSON output to this file.")
    args = parser.parse_args()

    text = read_sources(args.logs)
    payload = classify(text)
    payload["input_bytes"] = len(text.encode("utf-8", errors="replace"))
    out = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.output:
        args.output.write_text(out + "\n", encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
