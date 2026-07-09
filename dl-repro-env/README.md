# DL Repro Env

`dl-repro-env` is a portable Agent Skill for reproducing deep learning research code from a paper title, arXiv link, project page, or GitHub repository.

It is designed for messy real-world reproduction work: old PyTorch versions, CUDA mismatches, fragile `requirements.txt` files, custom CUDA extensions, missing checkpoints, Windows/Linux differences, and repositories that do not match your local GPU environment.

## What It Does

- Find or clone the target research repository.
- Inspect local system information: OS, conda/mamba, GPU, NVIDIA driver, CUDA runtime, disk space, and existing framework versions.
- Inspect repository environment files: `README`, `environment.yml`, `requirements.txt`, `setup.py`, `pyproject.toml`, `Dockerfile`, CI files, configs, and scripts.
- Detect high-risk dependencies such as `torchvision`, `mmcv`, `detectron2`, `pytorch3d`, `torch-scatter`, `tensorflow-gpu`, `xformers`, `flash-attn`, and `numpy`.
- Generate a conservative conda environment plan.
- Install into disposable attempt environments such as `repro-project-try1`.
- Run the fastest validation after install, using small batch size by default.
- Retry with `batch_size=1` if CUDA memory fails.
- Classify errors and revise the environment plan.
- Delete failed attempt environments created by the workflow.
- Keep only the final successful conda environment.
- Write a final `repro_env_report.md` explaining what was installed, what was validated, what changed, and what remains blocked.

## Repository Layout

```text
dl-repro-env/
  SKILL.md
  agents/
    openai.yaml
  references/
    failure-patterns.md
    framework-compatibility.md
    repo-inspection.md
  scripts/
    collect_system_info.py
    inspect_project.py
    make_env_plan.py
    run_fast_validation.py
    patch_batch_config.py
    classify_error.py
    cleanup_failed_envs.py
```

## Install In Codex

Codex discovers personal skills from your Codex skills directory. Put this folder there as `dl-repro-env`.

### Windows PowerShell

```powershell
git clone <YOUR_REPO_URL> dl-repro-env
New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\skills" | Out-Null
Copy-Item -Recurse -Force ".\dl-repro-env" "$env:USERPROFILE\.codex\skills\dl-repro-env"
```

### macOS / Linux

```bash
git clone <YOUR_REPO_URL> dl-repro-env
mkdir -p ~/.codex/skills
cp -R ./dl-repro-env ~/.codex/skills/dl-repro-env
```

Then start a new Codex session and ask:

```text
Use $dl-repro-env to reproduce this repository: https://github.com/<owner>/<repo>
```

Or:

```text
Use $dl-repro-env to reproduce the code for paper: <paper title or arXiv URL>
```

## Install In Claude Code

Claude Code supports personal skills in `~/.claude/skills/<skill-name>/SKILL.md` and project skills in `.claude/skills/<skill-name>/SKILL.md`.

### Personal Skill

Available in all Claude Code projects.

#### Windows PowerShell

```powershell
git clone <YOUR_REPO_URL> dl-repro-env
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\skills" | Out-Null
Copy-Item -Recurse -Force ".\dl-repro-env" "$env:USERPROFILE\.claude\skills\dl-repro-env"
```

#### macOS / Linux

```bash
git clone <YOUR_REPO_URL> dl-repro-env
mkdir -p ~/.claude/skills
cp -R ./dl-repro-env ~/.claude/skills/dl-repro-env
```

Start Claude Code in a project:

```bash
claude
```

Invoke the skill directly:

```text
/dl-repro-env https://github.com/<owner>/<repo>
```

Or let Claude choose it automatically:

```text
Reproduce this deep learning repository with a clean conda environment and fast validation: https://github.com/<owner>/<repo>
```

### Project-Local Skill

Use this when you want the skill available only inside one project.

```bash
mkdir -p .claude/skills
cp -R ./dl-repro-env .claude/skills/dl-repro-env
```

Then run Claude Code from that project and call:

```text
/dl-repro-env <paper title, arXiv URL, project page, or GitHub URL>
```

## Use In Claude.ai

If your Claude.ai account supports custom Skills, create a ZIP archive and upload it in the Skills settings UI.

### Windows PowerShell

```powershell
Compress-Archive -Path ".\dl-repro-env\*" -DestinationPath ".\dl-repro-env.zip" -Force
```

### macOS / Linux

```bash
zip -r dl-repro-env.zip dl-repro-env
```

Upload `dl-repro-env.zip`, enable the skill, then ask Claude:

```text
Use dl-repro-env to reproduce this repository: https://github.com/<owner>/<repo>
```

## Typical Workflow

```text
Use $dl-repro-env to reproduce this paper/code:
https://github.com/<owner>/<repo>

Requirements:
- create a clean conda environment
- match my local GPU/CUDA setup
- install dependencies
- run the fastest validation
- use batch size 4 first
- if validation fails, diagnose and retry
- remove failed attempt environments
- keep only the successful environment
- write a final report
```

## Safety Notes

- This skill must not install into `base`.
- This skill must not modify NVIDIA drivers or system CUDA automatically.
- Failed attempt environments should be deleted after each failed attempt.
- Only environments created by the current workflow and matching the attempt naming pattern should be removed.
- Full training should not be run unless explicitly requested.
- Missing datasets, checkpoints, credentials, driver changes, or OS changes should be reported as blockers instead of guessed or silently bypassed.

## Validation

The skill has been checked with:

```bash
python <skill-creator>/scripts/quick_validate.py ./dl-repro-env
python -c "import ast, pathlib; [ast.parse(p.read_text(encoding='utf-8')) for p in pathlib.Path('dl-repro-env/scripts').glob('*.py')]; print('syntax ok')"
```
