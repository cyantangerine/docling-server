conda create -n ocrdocling python=3.12

conda activate ocrdocling 

pip install uv

uv pip install docling rapidocr_onnxruntime

uv pip install onnxruntime-gpu

mkdir models

python download_model.py