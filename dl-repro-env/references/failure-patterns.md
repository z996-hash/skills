# Failure Patterns

Use this reference after installation or validation fails.

## Environment Solver Failures

Signs:

- `UnsatisfiableError`
- `PackagesNotFoundError`
- `ResolvePackageNotFound`
- `ResolutionImpossible`

Moves:

- Remove overly strict pins first.
- Use mamba if conda solve is slow.
- Split install into conda core packages first, then pip packages.
- Keep Python, framework, and CUDA pins explicit.

## CUDA / Framework Mismatch

Signs:

- `Torch not compiled with CUDA enabled`
- `CUDA driver version is insufficient`
- `no kernel image is available`
- `invalid device function`
- `libcudart.so not found`
- `cudart64_*.dll not found`

Moves:

- Check `nvidia-smi` driver and reported CUDA runtime.
- Install a framework CUDA build no newer than the driver supports.
- Avoid mixing pip and conda framework packages from different CUDA builds.
- Validate with a tiny tensor allocation before running project code.

## Torch / Torchvision ABI Mismatch

Signs:

- `operator torchvision::nms does not exist`
- `Couldn't load custom C++ ops`
- `undefined symbol`
- `DLL load failed`

Moves:

- Reinstall matching `torch`, `torchvision`, and `torchaudio`.
- Prefer official channels/index URLs.
- Remove stale duplicate framework installs from pip/conda.

## NumPy ABI Breakage

Signs:

- `numpy.dtype size changed`
- `A module that was compiled using NumPy 1.x cannot be run in NumPy 2`
- `ImportError: numpy.core.multiarray failed to import`

Moves:

- Pin `numpy<2` for older projects.
- Reinstall compiled packages after changing NumPy.

## Custom Extension Build Failure

Signs:

- `CUDAExtension`
- `fatal error: cuda.h`
- `nvcc fatal`
- `Microsoft Visual C++ 14.0 or greater is required`
- `gcc: error`

Moves:

- Prefer prebuilt wheels when available.
- Verify CUDA toolkit and compiler only if source build is unavoidable.
- Match extension package version to PyTorch and CUDA.
- On Windows, consider WSL2 if upstream only supports Linux.

## OpenMMLab / MMCV

Signs:

- `mmcv-full`
- `MMCV==`
- `undefined symbol`
- `No module named mmcv._ext`

Moves:

- Match `mmcv/mmcv-full`, PyTorch, and CUDA exactly.
- Prefer official OpenMMLab wheel index.
- Avoid mixing major generations of `mmcv`, `mmdet`, and `mmengine`.

## Missing Data Or Checkpoints

Signs:

- `FileNotFoundError`
- `No such file or directory`
- `checkpoint`
- `dataset`
- `weights`

Moves:

- Do not fabricate data.
- Report exact expected paths and download URLs if documented.
- Validate imports and model construction separately when data is unavailable.

## Out Of Memory

Signs:

- `CUDA out of memory`
- `CUBLAS_STATUS_ALLOC_FAILED`
- process killed during first batch

Moves:

- Retry validation with batch size 1.
- Reduce image size, point count, sequence length, or worker count for smoke tests.
- Report full reproduction memory needs separately from smoke-test success.
