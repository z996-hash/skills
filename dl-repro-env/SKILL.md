---
name: dl-repro-env
description: Reproduce deep learning research code from paper titles, arXiv links, project pages, or GitHub repositories. Use when the user wants to find or clone official research code, inspect dependency files, match PyTorch/TensorFlow/JAX/CUDA packages to the local GPU and NVIDIA driver, create disposable conda environments, install dependencies, run fast small-batch validation, diagnose failures, retry with revised environment plans, remove failed environments, and leave only the final working environment with a reproducibility report.
---

# DL Repro Env

## Overview

Use this skill as an execution protocol for deep learning paper/code reproduction. The goal is not merely to install packages; the goal is to leave one clean, validated conda environment and a report explaining exactly what worked, what was changed, and what still blocks full reproduction.

This skill is compatible with Codex and Claude. The core contract is this `SKILL.md` plus optional `scripts/` and `references/` resources. Codex may read `agents/openai.yaml` for UI metadata; Claude can ignore it.

## Hard Rules

- Never install into `base`.
- Never modify NVIDIA drivers or system CUDA automatically.
- Never keep failed attempt environments.
- Never delete user-created environments.
- Only remove conda environments created by this run whose names match the planned attempt pattern.
- Prefer reversible patches, copied configs, or generated override files over editing original repository files.
- Run the fastest useful validation after installation; do not run full training unless the user explicitly asks.
- Treat network downloads, large package installs, and conda environment removal as actions that may require user approval in the host agent.

## Workflow

1. Resolve the target.
   - If the user gives a GitHub URL, clone that repository.
   - If the user gives a paper title, DOI, arXiv link, or project page, find the most likely official code repository.
   - Prefer links from the paper, official project page, authors, Papers With Code, or README.
   - If multiple repositories are plausible, compare title, authors, README text, stars, commit history, issue activity, and release tags before choosing.

2. Collect local system information.
   - Run `scripts/collect_system_info.py --output system_info.json`.
   - Record OS, Python, conda/mamba availability, GPU model, GPU memory, NVIDIA driver, reported CUDA runtime, disk space, and optional existing framework versions.
   - Use `nvidia-smi` as the driver/runtime compatibility signal when present.

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
   - Prefer conda/mamba for Python and binary-heavy packages. Use pip after core conda packages are installed.
   - Save a candidate `environment.repro.yml` or exact install command list.

6. Install in disposable attempt environments.
   - Name attempts as `repro-<repo>-try1`, `repro-<repo>-try2`, and so on.
   - Create a new environment for each materially different plan.
   - Save install output to `install.try<N>.log`.
   - If installation fails, classify the error, remove the failed attempt environment, revise the plan, and retry.

7. Run fast validation immediately after installation.
   - Run `scripts/run_fast_validation.py --repo <repo> --output smoke_test.try<N>.json` inside the attempt environment.
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
   - On failure, run `scripts/classify_error.py install.try<N>.log smoke_test.try<N>.json --output error.try<N>.json`.
   - Inspect local README/issues/docs first, then search official docs or GitHub issues when network is available.
   - Apply the smallest clear fix: package pin, framework wheel change, Python downgrade, config override, path fix, build flag, or missing system note.
   - Remove the failed attempt environment before creating the next one.
   - Stop after repeated failures or when the blocker requires data, checkpoints, credentials, OS changes, driver changes, or hardware the user does not have.

9. Finalize only after success.
   - Rename or recreate the successful attempt as `repro-<repo>` when practical.
   - Remove all failed `repro-<repo>-try<N>` environments from this run.
   - Leave only the final successful environment.
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
- failed attempts and why each was removed
- unresolved blockers and exact next command for the user

## Resources

- `scripts/collect_system_info.py`: gather local OS, conda, GPU, CUDA, and disk information.
- `scripts/inspect_project.py`: inspect dependency files, frameworks, custom ops, imports, and likely run commands.
- `scripts/make_env_plan.py`: generate a conservative conda/pip plan from system and project inspection JSON.
- `scripts/run_fast_validation.py`: run import, CUDA, repository import, and optional command smoke tests.
- `scripts/patch_batch_config.py`: create a temporary small-batch config copy.
- `scripts/classify_error.py`: classify install/runtime errors into common deep learning reproduction failure categories.
- `scripts/cleanup_failed_envs.py`: safely remove only disposable attempt environments created by this workflow.
- `references/repo-inspection.md`: repository inspection checklist and precedence rules.
- `references/framework-compatibility.md`: framework/CUDA/Python compatibility heuristics.
- `references/failure-patterns.md`: common failure signatures and repair moves.
