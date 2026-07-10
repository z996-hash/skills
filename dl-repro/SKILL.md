---
name: dl-repro-env
description: Reproduce deep learning research code from paper titles, arXiv links, project pages, or GitHub repositories. Use when the user wants to find or clone official research code, inspect dependency files, match PyTorch/TensorFlow/JAX/CUDA packages to the local GPU and NVIDIA driver, create a stable final-named conda environment, install dependencies, run fast small-batch validation, diagnose failures, repair packages in place when safe, rebuild the same environment name when necessary, remove broken environments, and leave a reproducibility report.
---

# DL Repro Env

## Overview

Use this skill as an execution protocol for deep learning paper/code reproduction. The goal is not merely to install packages; the goal is to leave one clean, validated conda environment and a report explaining exactly what worked, what was changed, and what still blocks full reproduction.

This skill is compatible with Codex and Claude. The core contract is this `SKILL.md` plus optional `scripts/` and `references/` resources. Codex may read `agents/openai.yaml` for UI metadata; Claude can ignore it.

## Hard Rules

- Never install into `base`.
- Never modify NVIDIA drivers or system CUDA automatically.
- Create the conda environment with the final stable name from the beginning, such as `repro-<repo>`.
- Do not create `repro-<repo>-try<N>` environments by default.
- Do not clone, rename, alias, or symlink a validated conda environment into the final name. Compiled extensions may contain absolute paths or RPATHs.
- Never keep a broken environment as the final result.
- Never delete user-created environments.
- Before deleting an existing `repro-<repo>` environment, verify that it was created by this workflow or ask the user for confirmation.
- Prefer reversible patches, copied configs, or generated override files over editing original repository files.
- Prefer package-level repairs before deleting the whole environment.
- Run the fastest useful validation after installation; do not run full training unless the user explicitly asks.
- Treat network downloads, large package installs, and conda environment removal as actions that may require user approval in the host agent.

## Workflow

1. Resolve the target.
   - If the user gives a GitHub URL, clone that repository.
   - If the repository already exists locally or remotely, reuse it unless the user asks for a fresh clone.
   - On environment retry, never reclone the repository. Reuse the same checkout and record the commit.
   - If the user gives a paper title, DOI, arXiv link, or project page, find the most likely official code repository.
   - Prefer links from the paper, official project page, authors, Papers With Code, or README.
   - If multiple repositories are plausible, compare title, authors, README text, stars, commit history, issue activity, and release tags before choosing.

2. Collect local system information.
   - Run `scripts/collect_system_info.py --output system_info.json`.
   - Record OS, Python, conda/mamba availability, GPU model, GPU memory, NVIDIA driver, reported CUDA runtime, disk space, filesystem type, conda env/cache dirs, and optional existing framework versions.
   - Use `nvidia-smi` as the driver/runtime compatibility signal when present.
   - If the default conda environment or package cache path is on NFS or another slow network filesystem, prefer a faster writable env/cache location when available, or warn the user before installing a large CUDA stack.

3. Inspect the repository.
   - Run `scripts/inspect_project.py <repo> --output project_inspection.json`.
   - Read install sections in README files plus `environment.yml`, `requirements.txt`, `setup.py`, `pyproject.toml`, `Dockerfile`, `.github/workflows`, install scripts, and example commands.
   - Load `references/repo-inspection.md` when dependency declarations conflict or the install path is unclear.

4. Preflight common risks before installing.
   - Check Python constraints, framework family, CUDA requirements, custom CUDA/C++ extensions, OS assumptions, hardcoded paths, and dataset/checkpoint expectations.
   - Flag version-sensitive packages such as `torchvision`, `torchaudio`, `mmcv`, `mmdet`, `mmengine`, `detectron2`, `pytorch3d`, `torch-scatter`, `torch-sparse`, `tensorflow-gpu`, `cupy`, `apex`, `xformers`, `flash-attn`, `numpy`, and `opencv-python`.
   - Load `references/framework-compatibility.md` for framework/CUDA decisions.
   - Load `references/failure-patterns.md` when errors appear or risky packages are present.

5. Generate an environment plan.
   - Run `scripts/make_env_plan.py --system system_info.json --project project_inspection.json --output repro_env_plan.json`.
   - Prefer the repository's declared environment when compatible.
   - If incompatible with local driver/GPU/OS, choose the closest compatible binary stack.
   - Prefer mamba when available; otherwise use conda.
   - Prefer conda/mamba for Python and binary-heavy packages. Use pip after core conda packages are installed.
   - Avoid slow exploratory `conda search` calls. Use repository declarations, official install matrices, direct install attempts, or bounded `--dry-run --json` checks instead.
   - Keep channels narrow for each transaction. Use `--override-channels` for framework installs when the stack is known.
   - Avoid mixing `defaults` and `conda-forge` for ABI-sensitive image/scientific libraries unless the plan deliberately chooses one channel family.
   - Use pip cache by default. Avoid `--no-cache-dir` unless a cached wheel is known to be corrupt.
   - Save a candidate `environment.repro.yml` or exact install command list.

6. Install directly into the final environment name.
   - Use the stable name `repro-<repo>` from the first creation.
   - After creation, run `scripts/mark_repro_env.py --env-name repro-<repo> --repo <repo> --commit <commit>` so future resets can distinguish workflow-created environments from user-created environments.
   - Save install output to `install.iter<N>.log`, where `N` is the repair/rebuild iteration, not part of the environment name.
   - If a package install fails after the environment exists, first attempt a minimal in-place repair: uninstall, downgrade, upgrade, pin, or reinstall the failing package family.
   - If the framework stack, Python version, ABI baseline, or CUDA runtime choice is wrong, remove the whole `repro-<repo>` environment and recreate the same name from the revised plan.
   - Do not conda-clone a working environment just to obtain the final name.
   - For long-running installs, prefer an activated shell with unbuffered output over `conda run` so logs show progress reliably.

7. Run fast validation immediately after installation.
   - Run `scripts/run_fast_validation.py --repo <repo> --output smoke_test.iter<N>.json` inside `repro-<repo>`.
   - Prefer validation in this order:
     1. framework import test
     2. CUDA availability and small tensor allocation
     3. repository import test
     4. smallest official demo or inference command
     5. one mini training step only if no inference path exists
   - Force a small batch size. Use `batch_size=4`, `batchsize=4`, `bs=4`, or an equivalent CLI override.
   - If a config file must be changed, use `scripts/patch_batch_config.py` to create a copied config instead of editing the original.
   - If CUDA out-of-memory occurs, retry validation with batch size `1`.

8. Repair loop.
   - On failure, run `scripts/classify_error.py install.iter<N>.log smoke_test.iter<N>.json --output error.iter<N>.json`.
   - Inspect local README/issues/docs first, then search official docs or GitHub issues when network is available.
   - Apply the smallest clear fix first: package pin, package uninstall/reinstall, framework wheel change, config override, path fix, activate script, build flag, or missing system note.
   - Do not rebuild the environment for local package problems such as Pillow/libtiff, setuptools, transformers API drift, missing `LD_LIBRARY_PATH`, or optional dependency shims.
   - Rebuild the same environment name only when the base choice is wrong or the environment is corrupted: Python version, PyTorch/TensorFlow/JAX CUDA build, ABI baseline, broken conda transaction, or incompatible compiled extension baseline.
   - Before rebuilding, remove `repro-<repo>` with `scripts/reset_repro_env.py --env-name repro-<repo> --yes` after required approval.
   - Stop after repeated failure and remove the broken final environment unless the user explicitly wants to keep it for debugging.
   - Stop when the blocker requires data, checkpoints, credentials, OS changes, driver changes, or hardware the user does not have.

9. Finalize only after success.
   - Keep the already-validated `repro-<repo>` environment.
   - Do not clone or alias it.
   - Write `repro_env_report.md`.

## Report Requirements

Create `repro_env_report.md` with:

- paper/repository source and chosen commit
- repository path
- final conda environment name
- activation command
- OS, GPU, NVIDIA driver, and reported CUDA runtime
- Python version and framework versions
- exact install commands or `environment.repro.yml`
- validation command, batch size, and result
- changed files, copied configs, or patch files
- repair/rebuild iterations and why each was chosen
- unresolved blockers and exact next command for the user

## Resources

- `scripts/collect_system_info.py`: gather local OS, conda, GPU, CUDA, and disk information.
- `scripts/inspect_project.py`: inspect dependency files, frameworks, custom ops, imports, and likely run commands.
- `scripts/make_env_plan.py`: generate a conservative conda/pip plan from system and project inspection JSON.
- `scripts/run_fast_validation.py`: run import, CUDA, repository import, and optional command smoke tests.
- `scripts/patch_batch_config.py`: create a temporary small-batch config copy.
- `scripts/classify_error.py`: classify install/runtime errors into common deep learning reproduction failure categories.
- `scripts/mark_repro_env.py`: write a small marker into `conda-meta` after creating a workflow-managed environment.
- `scripts/reset_repro_env.py`: safely remove a final-named workflow environment before recreating the same name.
- `references/repo-inspection.md`: repository inspection checklist and precedence rules.
- `references/framework-compatibility.md`: framework/CUDA/Python compatibility heuristics.
- `references/failure-patterns.md`: common failure signatures and repair moves.
