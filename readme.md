# Installation
```shell
git clone https://github.com/cyantangerine/docling-server
cd docling-server
```
```shell
conda create -n docling-server python=3.12
```
```shell
conda activate docling-server
```
```shell
pip install uv
uv pip install docling rapidocr_onnxruntime
```
```shell
uv pip install onnxruntime-gpu
```
```shell
mkdir models
```
```shell
python download_model.py
```
# Test
```shell
python ocr.py
```
# Run
```shell

```