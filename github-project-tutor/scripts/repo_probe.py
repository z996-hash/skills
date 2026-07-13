#!/usr/bin/env python3
"""Create a lightweight, evidence-oriented index of a source repository.

The probe never imports or executes repository code. Python files are parsed with
the standard-library AST; other files contribute only to the repository inventory.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
from collections import Counter
from pathlib import Path
from typing import Any


IGNORE_DIRS = {
    ".git", ".hg", ".svn", ".idea", ".vscode", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", "__pycache__", "node_modules", "dist",
    "build", "site-packages", ".venv", "venv", "env", "data", "datasets",
    "checkpoints", "weights", "outputs", "runs", "wandb",
}
MANIFEST_NAMES = {
    "pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "environment.yml",
    "package.json", "cargo.toml", "go.mod", "pom.xml", "build.gradle", "makefile",
    "dockerfile", "compose.yaml", "docker-compose.yml", ".gitmodules",
}
ENTRY_NAMES = {
    "main.py", "train.py", "evaluate.py", "eval.py", "test.py", "infer.py",
    "inference.py", "predict.py", "serve.py", "server.py", "app.py", "cli.py",
}
SHAPE_CALLS = {
    "view", "reshape", "flatten", "unflatten", "permute", "transpose", "movedim",
    "squeeze", "unsqueeze", "cat", "stack", "chunk", "pad", "interpolate",
    "einsum", "rearrange", "repeat", "expand", "contiguous",
}
MODEL_BASES = {"Module", "LightningModule", "Model", "PreTrainedModel"}
DATA_BASES = {"Dataset", "IterableDataset", "DataModule", "Sequence"}


def dotted_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = dotted_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return ""


def line_text(lines: list[str], lineno: int) -> str:
    if 1 <= lineno <= len(lines):
        return lines[lineno - 1].strip()[:240]
    return ""


class PythonInspector(ast.NodeVisitor):
    def __init__(self, lines: list[str]) -> None:
        self.lines = lines
        self.imports: list[dict[str, Any]] = []
        self.symbols: list[dict[str, Any]] = []
        self.shape_ops: list[dict[str, Any]] = []
        self.has_main_guard = False

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.append({"module": alias.name, "name": None, "level": 0, "line": node.lineno})

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            self.imports.append({
                "module": node.module or "", "name": alias.name,
                "level": node.level, "line": node.lineno,
            })

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        bases = [dotted_name(base) for base in node.bases]
        tail_bases = {base.rsplit(".", 1)[-1] for base in bases}
        role = "class"
        if tail_bases & MODEL_BASES:
            role = "model"
        elif tail_bases & DATA_BASES:
            role = "dataset"
        self.symbols.append({"kind": role, "name": node.name, "line": node.lineno, "bases": bases})
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        decorators = [dotted_name(dec) for dec in node.decorator_list]
        self.symbols.append({"kind": "function", "name": node.name, "line": node.lineno, "decorators": decorators})
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_If(self, node: ast.If) -> None:
        try:
            text = ast.unparse(node.test)
        except Exception:
            text = ""
        if "__name__" in text and "__main__" in text:
            self.has_main_guard = True
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        name = dotted_name(node.func)
        tail = name.rsplit(".", 1)[-1]
        if tail in SHAPE_CALLS:
            self.shape_ops.append({
                "operation": name, "line": node.lineno,
                "source": line_text(self.lines, node.lineno),
            })
        self.generic_visit(node)


def module_name(rel: Path) -> str | None:
    if rel.suffix != ".py":
        return None
    parts = list(rel.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts) or None


def resolve_local_import(current: str | None, item: dict[str, Any], modules: set[str]) -> str | None:
    imported = item["module"]
    level = item["level"]
    if level and current:
        package = current.split(".")[:-1]
        keep = max(0, len(package) - level + 1)
        prefix = package[:keep]
        candidate = ".".join(prefix + ([imported] if imported else []))
    else:
        candidate = imported
    choices = [candidate]
    if item.get("name"):
        choices.insert(0, ".".join(filter(None, [candidate, item["name"]])))
    for choice in choices:
        probe = choice
        while probe:
            if probe in modules:
                return probe
            probe = probe.rsplit(".", 1)[0] if "." in probe else ""
    return None


def inspect_repo(root: Path, max_files: int, max_bytes: int) -> dict[str, Any]:
    files: list[Path] = []
    truncated = False
    for base, dirs, names in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in IGNORE_DIRS and not d.startswith("."))
        for name in sorted(names):
            path = Path(base) / name
            try:
                size = path.stat().st_size
            except OSError:
                continue
            if size <= max_bytes:
                files.append(path)
            if len(files) >= max_files:
                truncated = True
                break
        if truncated:
            break

    rels = [path.relative_to(root) for path in files]
    modules = {name for rel in rels if (name := module_name(rel))}
    extensions = Counter((rel.suffix.lower() or "[no extension]") for rel in rels)
    manifests = [str(rel).replace("\\", "/") for rel in rels if rel.name.lower() in MANIFEST_NAMES]
    python_files: list[dict[str, Any]] = []
    entrypoints: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    for path, rel in zip(files, rels):
        if path.suffix != ".py":
            continue
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source, filename=str(rel))
        except (OSError, SyntaxError) as exc:
            errors.append({"file": str(rel).replace("\\", "/"), "error": str(exc)})
            continue
        inspector = PythonInspector(source.splitlines())
        inspector.visit(tree)
        current_module = module_name(rel)
        local_imports = []
        for item in inspector.imports:
            resolved = resolve_local_import(current_module, item, modules)
            if resolved:
                local_imports.append({**item, "resolved": resolved})
        record = {
            "file": str(rel).replace("\\", "/"),
            "module": current_module,
            "lines": len(source.splitlines()),
            "symbols": inspector.symbols,
            "imports": inspector.imports,
            "local_imports": local_imports,
            "shape_ops": inspector.shape_ops,
            "has_main_guard": inspector.has_main_guard,
        }
        python_files.append(record)
        reasons = []
        if rel.name.lower() in ENTRY_NAMES:
            reasons.append("conventional filename")
        if inspector.has_main_guard:
            reasons.append("__main__ guard")
        if any(s["kind"] == "function" and s["name"] in {"main", "cli", "train", "predict", "serve"} for s in inspector.symbols):
            reasons.append("entry-like function")
        if reasons:
            entrypoints.append({"file": record["file"], "reasons": reasons})

    return {
        "root": str(root.resolve()),
        "file_count_scanned": len(files),
        "truncated": truncated,
        "extensions": dict(extensions.most_common()),
        "manifests": manifests,
        "entrypoint_candidates": entrypoints,
        "python_files": python_files,
        "parse_errors": errors,
    }


def render_markdown(data: dict[str, Any]) -> str:
    out = ["# Repository probe", "", f"- Root: `{data['root']}`", f"- Files scanned: {data['file_count_scanned']}"]
    if data["truncated"]:
        out.append("- Warning: file limit reached; inventory is incomplete")
    out.extend(["", "## File types", ""])
    out.extend(f"- `{ext}`: {count}" for ext, count in data["extensions"].items())
    out.extend(["", "## Manifests", ""])
    if data["manifests"]:
        out.extend(f"- `{name}`" for name in data["manifests"])
    else:
        out.append("- None detected")
    out.extend(["", "## Entrypoint candidates", ""])
    if data["entrypoint_candidates"]:
        out.extend(f"- `{item['file']}` - {', '.join(item['reasons'])}" for item in data["entrypoint_candidates"])
    else:
        out.append("- None detected")
    out.extend(["", "## Python module index", ""])
    for item in data["python_files"]:
        noteworthy = [s for s in item["symbols"] if s["kind"] in {"model", "dataset"} or s["name"] in {"main", "train", "forward", "__getitem__", "collate_fn", "predict"}]
        if not (noteworthy or item["local_imports"] or item["shape_ops"]):
            continue
        out.append(f"### `{item['file']}`")
        if noteworthy:
            out.append("- Key symbols: " + ", ".join(f"{s['name']} ({s['kind']}, L{s['line']})" for s in noteworthy))
        if item["local_imports"]:
            edges = sorted({imp["resolved"] for imp in item["local_imports"]})
            out.append("- Local imports: " + ", ".join(f"`{edge}`" for edge in edges))
        if item["shape_ops"]:
            ops = item["shape_ops"][:20]
            out.append("- Shape operations:")
            out.extend(f"  - L{op['line']} `{op['operation']}` in `{op['source']}`" for op in ops)
            if len(item["shape_ops"]) > len(ops):
                out.append(f"  - … {len(item['shape_ops']) - len(ops)} more")
        out.append("")
    if data["parse_errors"]:
        out.extend(["## Parse errors", ""])
        out.extend(f"- `{item['file']}`: {item['error']}" for item in data["parse_errors"])
    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", type=Path, help="Local repository root")
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    parser.add_argument("--output", type=Path, help="Write output to a file instead of stdout")
    parser.add_argument("--max-files", type=int, default=5000)
    parser.add_argument("--max-bytes", type=int, default=2_000_000, help="Skip files larger than this")
    args = parser.parse_args()
    root = args.repo.resolve()
    if not root.is_dir():
        parser.error(f"not a directory: {root}")
    data = inspect_repo(root, args.max_files, args.max_bytes)
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n" if args.format == "json" else render_markdown(data)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
