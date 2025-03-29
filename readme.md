# Installation
'''
git clone https://github.com/cyantangerine/docling-server
cd docling-server
'''
'''
conda create -n docling-server python=3.12
'''
'''
conda activate docling-server
'''
'''
pip install uv
uv pip install docling rapidocr_onnxruntime
'''
'''
uv pip install onnxruntime-gpu
'''
'''
mkdir models
'''
'''
python download_model.py
'''
# Test
'''
python ocr.py
'''
# Run
'''

'''