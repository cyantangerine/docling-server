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
uv pip install docling rapidocr_onnxruntime Flask gunicorn
```
```shell
uv pip install onnxruntime-gpu
```
```shell
mkdir models
python download_model.py
```
# Test
```shell
python ocr.py
```
# Run
```shell
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```
http://127.0.0.1:8000/