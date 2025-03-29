from flask import Flask, request, jsonify, render_template, send_from_directory
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid
from ocr import ocr_docling

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULT_FOLDER'] = 'static/results'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

# 确保目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULT_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        # 生成唯一文件名
        filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())
        upload_filename = f"{unique_id}_{filename}"
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], upload_filename)
        
        file.save(upload_path)
        
        # 创建结果目录
        result_dir = os.path.join(app.config['RESULT_FOLDER'], unique_id)
        os.makedirs(result_dir, exist_ok=True)
        
        # 调用OCR函数
        ocr_docling(doc_path=upload_path, output_path=result_dir, image=True, latex=False, code=True)
        
        # 获取结果文件列表
        result_files = os.listdir(result_dir)
        
        return jsonify({
            'success': True,
            'result_id': unique_id,
            'files': result_files
        }), 200
    
    return jsonify({'error': 'Invalid file format, only PDF allowed'}), 400

@app.route('/results/<path:filename>')
def serve_result(filename):
    return send_from_directory(app.config['RESULT_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True, port=3294)