from flask import Flask, render_template, request, jsonify
import subprocess
import json
import sqlite3
import os

app = Flask(__name__)

# データベースファイルのパス
DB_PATH = 'reservations.db'

# データベースの初期化（存在しない場合に作成）
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            classroom TEXT,
            classtime TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# データベースに予約情報を保存（JSON出力をそのまま保存）
def save_reservations_to_db(student_id, _, reservations):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 同じ学籍番号の既存データを削除（全時限分）
    c.execute('DELETE FROM reservations WHERE student_id = ?', (student_id,))

    # 新しい予約情報を挿入
    for entry in reservations:
        classroom = entry.get('classroom')
        classtime = entry.get('classtime')
        if classroom and classtime:  # 両方が存在する場合のみ挿入
            c.execute('''
                INSERT INTO reservations (student_id, classroom, classtime)
                VALUES (?, ?, ?)
            ''', (student_id, classroom, classtime))
    conn.commit()
    conn.close()

# 初期化を実行
init_db()

# ページルーティング
@app.route('/')
def login():
    return render_template('login.html')

@app.route('/account')
def account():
    return render_template('account.html')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/graph')
def graph():
    return render_template('graph.html')

@app.route('/map')
def map():
    return render_template('map.html')

@app.route('/search_reservation')
def search_reservation():
    return render_template('search_reservation.html')

@app.route('/setting')
def setting():
    return render_template('setting.html')

# データベース確認用ページ
@app.route('/view_reserva')
def view_reserva():
    return render_template('view_reservations.html')

# API：ログインして予約情報を取得・保存
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    student_id = data.get('studentId')
    password = data.get('password')

    if not all([student_id, password]):
        return jsonify({'success': False, 'message': '必要な情報が不足しています。'}), 400

    try:
        result = subprocess.run(
            ['python3', 'marcoScraping.py', student_id, password],
            capture_output=True,
            text=True,
            check=True
        )

        output = result.stdout.strip()

        try:
            reservation_data = json.loads(output)

            if isinstance(reservation_data, dict):
                all_entries = []
                for slot_entries in reservation_data.values():
                    all_entries.extend(slot_entries)
                save_reservations_to_db(student_id, None, all_entries)
                return jsonify({'success': True, 'message': 'ログイン成功', 'data': all_entries})
            else:
                return jsonify({'success': False, 'message': '予約情報の形式が正しくありません。'})

        except json.JSONDecodeError:
            return jsonify({'success': False, 'message': 'IDまたはパスワードが間違っています。'})

    except subprocess.CalledProcessError as e:
        return jsonify({
            'success': False,
            'message': 'スクリプトの実行に失敗しました',
            'details': e.stderr
        }), 500


# データベースから予約情報を一覧表示（HTML）
@app.route('/view_reservations')
def view_reservations():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, student_id, classroom, classtime, timestamp FROM reservations ORDER BY timestamp DESC")
    reservations = c.fetchall()
    conn.close()

    return render_template('view_reservations.html', reservations=reservations)

# API：予約情報をJSONで取得
@app.route('/api/reservations', methods=['GET'])
def api_reservations():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT classroom, classtime FROM reservations ORDER BY timestamp DESC")
    rows = c.fetchall()
    conn.close()

    reservations = [{'classroom': row[0], 'classtime': row[1]} for row in rows if row[0] is not None]

    return jsonify({'success': True, 'reservations': reservations})


# アプリ起動
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
