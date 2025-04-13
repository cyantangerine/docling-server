import json
import logging
from pathlib import Path
import shutil
from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import requests
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid
import threading
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


@app.route('/remove_result', methods=['POST'])
def remove_result():
    task_id = request.args.get('id')
    if not task_id or not isinstance(task_id, str) or task_id == '.' or task_id == '..' or task_id.find("/") != -1:
        return jsonify({'code': -1,'error': 'Missing task ID'}), 400
    
    filename = Path(app.config['RESULT_FOLDER']) / Path(task_id)
    if not filename.exists():
        return jsonify({'code': -1,'error': 'Task not found'}), 404

    filename2 = filename / 'result.json'
    if not filename2.exists():
        return jsonify({'code': 1, 'error': 'Task is running. Can not delete now, please try again later.'}), 200
    
    shutil.rmtree(filename)
    return jsonify({'code': 0}), 200

@app.route('/result', methods=['GET'])
def get_result():
    task_id = request.args.get('id')
    if not task_id:
        return jsonify({'code': -1,'error': 'Missing task ID'}), 400
    
    filename = Path(app.config['RESULT_FOLDER']) / Path(task_id) 
    if not filename.exists():
        return jsonify({'code': -1,'error': 'Task not found'}), 404

    filename = filename / 'result.json'
    if not filename.exists():
        return jsonify({'code': 1, 'error': 'Task is running'}), 200
    data = ''
    with open(filename, 'r') as f:
        data = f.read()
    return jsonify(json.loads(data)), 200

@app.route('/upload', methods=['POST'])
def upload_file():
    print(dict(request.form))
    print(dict(request.files))
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    callback_url = request.form.get('callback_url')
    
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
        
        def ocr():
            def cb(data):
                if callback_url:
                    requests.request('POST', callback_url, json=data)
                else:
                    logging.info(f"Unknown callback URL, ignoring callback. {data}")
                    requests.request('POST', 'http://localhost:9380/v1/document/ocr_result', json=data)
            try:
                # 调用OCR函数
                result_obj = ocr_docling(server_path_prefix=result_dir, doc_path=upload_path, output_path=result_dir, image=True, latex=True, code=True)
                
                # 获取结果文件列表
                result_files = os.listdir(result_dir)
                
                with open(f"{result_dir}/result.json", 'w') as f:
                    data = {
                        'code': 0,
                        'success': True,
                        'result_id': unique_id,
                        'result': result_obj,
                        'files': result_files,
                        'filename': filename
                    }
                    f.write(json.dumps(data))
                    cb({
                        'code': 0,
                        'success': True,
                        'doc_id': unique_id,
                        'markdown': result_obj['markdown'],
                        'pictures': result_obj['pictures'],
                        'filename': filename
                    })
            except Exception as e:
                with open(f"{result_dir}/result.json", 'w') as f:
                    data = {
                        'code': -1,
                        'success': False,
                        'result_id': unique_id,
                        'error': str(e),
                        'filename': filename
                    }
                    f.write(json.dumps(data))       
                    cb({
                        'code': -1,
                        'success': False,
                        'doc_id': unique_id,
                        'error': str(e),
                        'filename': filename
                    })
                
        threading.Thread(
            target=ocr,
        ).start()
        return jsonify({
                    'success': True,
                    'result_id': unique_id
                }), 200
        
    
    return jsonify({'error': 'Invalid file format, only PDF allowed'}), 400

@app.route('/results/<path:filename>')
def serve_result(filename):
    # 获取目录路径
    dir_path = os.path.join(app.config['RESULT_FOLDER'], filename)
    
    if not os.path.exists(dir_path):
        return "Not found", 404
    
    if os.path.isdir(dir_path):
        # 获取目录中的文件和文件夹列表
        files = os.listdir(dir_path)
        # 渲染模板，显示文件列表
        return render_template('ftp.html', files=files, directory=filename)
    else:
        return send_from_directory(app.config['RESULT_FOLDER'], filename)


        

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=3294)