# Repository Inspection

Use this reference when repository dependency signals conflict or the install path is unclear.

## Dependency Source Precedence

Prefer the most specific and executable source:

1. Official Dockerfile or devcontainer that the README explicitly recommends.
2. `environment.yml`, `environment.yaml`, or `conda.yml`.
3. Official install script such as `install.sh`, `setup.sh`, or `scripts/install*`.
4. `requirements.txt`, `requirements/*.txt`, `setup.py`, `pyproject.toml`.
5. CI files such as `.github/workflows/*.yml`.
6. README install commands.
7. Imports discovered from source files.

When sources conflict, preserve the conflict in the report and choose the path closest to the README's recommended reproduction command.

## Files To Inspect

- `README*`, `docs/*`, `INSTALL*`
- `environment*.yml`, `conda*.yml`
- `requirements*.txt`, `requirements/*.txt`
- `setup.py`, `setup.cfg`, `pyproject.toml`
- `Dockerfile`, `.devcontainer/*`
- `.github/workflows/*`
- `train*.py`, `test*.py`, `eval*.py`, `demo*.py`, `infer*.py`
- `configs/*`, `config/*`, `options/*`

## Signals That Need Special Care

- Custom extensions: `CUDAExtension`, `CppExtension`, `torch.utils.cpp_extension`, `.cu`, `.cuh`, `setup_cuda.py`.
- OpenMMLab stack: `mmcv`, `mmcv-full`, `mmdet`, `mmseg`, `mmengine`.
- 3D/geometry stack: `pytorch3d`, `torch-scatter`, `torch-sparse`, `spconv`, `kaolin`.
- Transformer acceleration: `flash-attn`, `xformers`, `apex`, `bitsandbytes`.
- Old TensorFlow: `tensorflow-gpu`, `tf.contrib`, `keras<2.4`.
- Pinned old scientific packages: `numpy<1.20`, `scipy<1.6`, `opencv-python<4`.

## Run Command Discovery

Prefer the smallest command that exercises the model path:

1. `demo.py`, `inference.py`, or README demo command.
2. `test.py` or official evaluation with a tiny sample.
3. A script that imports model/config and creates one forward pass.
4. One training step with batch size 4, then batch size 1 if memory fails.

Do not start full training unless the user explicitly asks.
