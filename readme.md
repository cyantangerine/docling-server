# Installation
Clone the project.
```shell
git clone https://github.com/cyantangerine/docling-server
cd docling-server
```
Change some settings (if need).
```shell
cp .env.template .env
vim .env
```
Make environment vars active.
```shell
source .env
```
Create venv.
```shell
conda create -n docling-server python=3.12
```
```shell
conda activate docling-server
```
Install package.
```shell
pip install uv
uv pip install docling rapidocr_onnxruntime Flask gunicorn
```
If you have gpu, run this to accelerate.
```shell
uv pip install onnxruntime-gpu
```
Download models.
```shell
mkdir models
python download_model.py
```
# Test
Have a try!
```shell
python ocr.py
```
# Run
Run your server.
```shell
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```
http://127.0.0.1:8000/