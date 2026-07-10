#!/usr/bin/env python3
"""Create a copied config with small batch-size overrides."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


PATTERNS = [
    (re.compile(r"(^\s*batch_size\s*[:=]\s*)([0-9]+)", re.MULTILINE), "batch_size"),
    (re.compile(r"(^\s*batchsize\s*[:=]\s*)([0-9]+)", re.MULTILINE), "batchsize"),
    (re.compile(r"(^\s*bs\s*[:=]\s*)([0-9]+)", re.MULTILINE), "bs"),
    (re.compile(r"(^\s*BATCH_SIZE\s*[:=]\s*)([0-9]+)", re.MULTILINE), "BATCH_SIZE"),
    (re.compile(r"(['\"]batch_size['\"]\s*:\s*)([0-9]+)"), "dict_batch_size"),
    (re.compile(r"(['\"]batchsize['\"]\s*:\s*)([0-9]+)"), "dict_batchsize"),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--output", "-o", type=Path, help="Copied config path. Defaults to <stem>.batch<batch><suffix>.")
    args = parser.parse_args()

    source = args.config
    text = source.read_text(encoding="utf-8", errors="replace")
    changes = []
    for pattern, label in PATTERNS:
        text, count = pattern.subn(lambda m: f"{m.group(1)}{args.batch_size}", text)
        if count:
            changes.append({"pattern": label, "count": count})

    output = args.output or source.with_name(f"{source.stem}.batch{args.batch_size}{source.suffix}")
    output.write_text(text, encoding="utf-8")
    print(f"wrote={output}")
    print(f"changes={changes}")
    return 0 if changes else 2


if __name__ == "__main__":
    raise SystemExit(main())
