import os
import json
import uuid
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Используем временную папку Render, которая не зависит от перезапуска оперативной памяти
DB_DIR = "/tmp/tasks_db"
os.makedirs(DB_DIR, exist_ok=True)

def save_task(session_id, data):
    with open(os.path.join(DB_DIR, f"{session_id}.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

def get_task(session_id):
    path = os.path.join(DB_DIR, f"{session_id}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

@app.route('/')
def index():
    session_id = str(uuid.uuid4())
    return render_template('index.html', session_id=session_id)

@app.route('/submit_code', methods=['POST'])
def submit_code():
    data = request.get_json() or {}
    session_id = data.get('session_id')
    code = data.get('code')
    if not session_id or not code:
        return jsonify({'error': 'Missing session_id or code'}), 400
    
    # Записываем задачу со статусом "ожидает" (pending)
    save_task(session_id, {'code': code, 'status': 'pending', 'result': None})
    return jsonify({'status': 'ok'})

@app.route('/get_pending', methods=['GET'])
def get_pending():
    # Ищем первую попавшуюся задачу со статусом 'pending'
    for file in os.listdir(DB_DIR):
        if file.endswith(".json"):
            session_id = file.replace(".json", "")
            task = get_task(session_id)
            if task and task.get('status') == 'pending':
                task['status'] = 'processing' # Переводим в статус обработки агентом
                save_task(session_id, task)
                return jsonify({'session_id': session_id, 'code': task['code']})
    return jsonify({'session_id': None, 'code': None}), 204

@app.route('/submit_result', methods=['POST'])
def submit_result():
    data = request.get_json() or {}
    session_id = data.get('session_id')
    qr_base64 = data.get('qr_base64')
    if not session_id or not qr_base64:
        return jsonify({'error': 'Missing session_id or qr_base64'}), 400
    
    task = get_task(session_id)
    if not task:
        return jsonify({'error': 'Session not found'}), 404
    
    task['result'] = qr_base64
    task['status'] = 'completed'
    save_task(session_id, task)
    return jsonify({'status': 'ok'})

@app.route('/get_result', methods=['GET'])
def get_result():
    session_id = request.args.get('session_id')
    if not session_id:
        return jsonify({'error': 'Missing session_id'}), 400
    task = get_task(session_id)
    if not task:
        return jsonify({'error': 'Session not found'}), 404
    return jsonify({'result': task['result']})

if __name__ == '__main__':
    app.run(debug=True)
