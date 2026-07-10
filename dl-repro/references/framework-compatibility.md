# Framework Compatibility

Use this reference when choosing Python, CUDA, and framework packages.

## General Rules

- Treat `nvidia-smi`'s "CUDA Version" as the maximum CUDA runtime supported by the installed driver, not proof that a local toolkit is installed.
- Prefer prebuilt framework binaries over compiling from source.
- Match `torch`, `torchvision`, and `torchaudio` from the same official release family.
- Keep Python conservative for old research code. Many 2018-2021 repositories work best with Python 3.7-3.9; newer repositories usually tolerate Python 3.10-3.11.
- Avoid `numpy>=2` for old repositories unless the project is explicitly modernized.
- Do not install or modify system NVIDIA drivers.
- If the repository requires Linux-only packages and the host is Windows, prefer WSL2/Docker guidance instead of forcing native Windows builds.
- Use the final environment name from the start. Do not build in `repro-*-try1` and clone or alias it later.
- Prefer package-level repair for leaf dependency failures. Rebuild the same environment name only when the base Python/framework/CUDA choice is wrong.
- If the default conda env or package cache path is on NFS, expect large PyTorch/CUDA transactions to be slow; use a faster writable env/cache location when available.
- Use cached wheels/packages by default. Disable caches only when corruption is suspected.
- For long commands, prefer an activated shell and unbuffered output over `conda run` so progress appears in logs.

## PyTorch

Use the repository's declared PyTorch version when it is compatible with local drivers. If no version is declared:

- Prefer a currently supported PyTorch binary from the official install selector.
- Choose a CUDA build no newer than the driver's reported maximum CUDA runtime.
- Use CPU-only builds when no NVIDIA GPU is present.

Common repair moves:

- Replace mismatched `torchvision` with the version matching `torch`.
- Replace `cudatoolkit` pins with the framework's packaged CUDA runtime when appropriate.
- For `torch-scatter`, `torch-sparse`, and related packages, install wheels matching both `torch` and CUDA.
- For `pytorch3d`, match Python, PyTorch, CUDA, and platform carefully; use official wheels when available.
- For old PyTorch stacks, check `setuptools`, `torchmetrics`, `transformers`, and `numpy` pins early; targeted pins are much faster than full environment rebuilds.

## TensorFlow

- Treat `tensorflow-gpu` as a legacy package. Modern TensorFlow includes GPU support on supported Linux configurations.
- Native Windows GPU support is limited for newer TensorFlow releases; WSL2 is often the practical path.
- Old TensorFlow repositories may require Python 3.6-3.8 and CUDA/cuDNN versions that are no longer easy to install. Prefer Docker or WSL2 when exact legacy binaries are required.

## JAX

- Install `jax` and CUDA-enabled `jaxlib` from official JAX instructions.
- Match CUDA wheel support to the NVIDIA driver and platform.
- If no GPU support is available, validate with CPU first and report the limitation.

## Custom CUDA/C++ Extensions

Before building extensions, check:

- compiler availability
- CUDA toolkit availability when source compilation is required
- `CUDA_HOME`
- Visual Studio Build Tools on Windows
- GCC version compatibility on Linux
- PyTorch ABI compatibility

If build failure is not trivial, prefer a prebuilt wheel, Dockerfile, or version downgrade over repeated source builds.
