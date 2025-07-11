from flask import Flask, render_template, request, jsonify, Response
import subprocess
import json
import sqlite3
import os
import time
import threading

app = Flask(__name__)
DB_PATH = 'reservations.db'

# グローバル進捗状況
progress_status = {"status": "idle", "message": ""}


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # 省略（DB初期化用テーブルCREATE）
    conn.commit()
    conn.close()


def save_reservations_to_db(student_id, _, reservations):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM reservations')
    for entry in reservations:
        classroom = entry.get('classroom')
        classtime = entry.get('classtime')
        if classroom and classtime:
            c.execute('''
                INSERT INTO reservations (student_id, classroom, classtime)
                VALUES (?, ?, ?)
            ''', (student_id, classroom, classtime))
    conn.commit()
    conn.close()


def save_available_rooms_to_db(student_id, available_data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM available_rooms')
    for classtime, rooms in available_data.items():
        for room in rooms:
            building = room.get('号館')
            floor = room.get('階数')
            classroom_number = room.get('教室番号')
            if building and floor and classroom_number:
                c.execute('''
                    INSERT INTO available_rooms (student_id, building, floor, classroom_number, classtime)
                    VALUES (?, ?, ?, ?, ?)
                ''', (student_id, building, floor, classroom_number, classtime))
    conn.commit()
    conn.close()


# 🔸【追加】プログレス画面表示
@app.route('/progress')
def progress():
    return render_template('progress.html')


# 🔸【追加】非同期処理をバックグラウンドで開始
@app.route('/start_task', methods=['POST'])
def start_task():
    data = request.get_json()
    student_id = data.get('studentId')
    password = data.get('password')

    def run_task():
        global progress_status
        try:
            progress_status["status"] = "running"
            progress_status["message"] = "ログイン中..."

            result = subprocess.run([
                'python3', 'marcoScraping.py', student_id, password
            ], capture_output=True, text=True, check=True)

            progress_status["message"] = "データ処理中..."

            output = result.stdout.strip()
            reservation_data = json.loads(output)

            if (isinstance(reservation_data, dict)
                and "空き教室" in reservation_data
                and "予約済み教室" in reservation_data):

                reserved_entries = reservation_data.get("予約済み教室", {})
                all_reserved = []
                for classtime, rooms in reserved_entries.items():
                    for room in rooms:
                        all_reserved.append({
                            "classroom": room.get("教室番号"),
                            "classtime": classtime
                        })

                available_entries = reservation_data.get("空き教室", {})

                save_reservations_to_db(student_id, None, all_reserved)
                save_available_rooms_to_db(student_id, available_entries)

                progress_status["status"] = "complete"
                progress_status["message"] = "完了！"
            else:
                progress_status["status"] = "error"
                progress_status["message"] = "データ形式が不正です"

        except Exception as e:
            progress_status["status"] = "error"
            progress_status["message"] = f"エラー: {str(e)}"

    threading.Thread(target=run_task).start()
    return jsonify({"status": "started"})


# 🔸【追加】進捗状況をリアルタイム送信（SSE）
@app.route('/progress_stream')
def progress_stream():
    def generate():
        prev_status = ""
        while True:
            if progress_status["status"] != prev_status:
                yield f"data: {json.dumps(progress_status)}\n\n"
                prev_status = progress_status["status"]
            if progress_status["status"] in ["complete", "error"]:
                break
            time.sleep(0.5)

    return Response(generate(), mimetype='text/event-stream')

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/game')
def game():
    return render_template('game.html')  #追加

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

@app.route('/view_reserva')
def view_reserva():
    return render_template('view_reservations.html')

@app.route('/view_reservations')
def view_reservations():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT student_id, classroom, classtime, timestamp FROM reservations ORDER BY timestamp DESC")
    reserved_rows = c.fetchall()

    c.execute("SELECT student_id, building, floor, classroom_number, classtime, timestamp FROM available_rooms ORDER BY timestamp DESC")
    available_rows = c.fetchall()

    c.execute("SELECT sensor_id, location, current_count, total_entries, total_exits, timestamp FROM sensor_logs ORDER BY timestamp DESC LIMIT 50")
    sensor_rows = c.fetchall()

    conn.close()

    reserved_list = [
        {"student_id": r[0], "classroom": r[1], "classtime": r[2], "timestamp": r[3]}
        for r in reserved_rows
    ]
    available_list = [
        {"student_id": r[0], "号館": r[1], "階数": r[2], "教室番号": r[3], "classtime": r[4], "timestamp": r[5]}
        for r in available_rows
    ]
    sensor_list = [
        {"sensor_id": r[0], "location": r[1], "current_count": r[2], "total_entries": r[3], "total_exits": r[4], "timestamp": r[5]}
        for r in sensor_rows
    ]

    return render_template('view_reservations.html',
                           reservations=reserved_list,
                           available_rooms=available_list,
                           sensor_logs=sensor_list)

@app.route('/api/reservations', methods=['GET'])
def api_reservations():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT classroom, classtime FROM reservations ORDER BY timestamp DESC")
    rows = c.fetchall()
    conn.close()
    reservations = [{'classroom': row[0], 'classtime': row[1]} for row in rows if row[0] is not None]
    return jsonify({'success': True, 'reservations': reservations})

@app.route('/api/available_rooms', methods=['GET'])
def api_available_rooms():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT building, floor, classroom_number, classtime FROM available_rooms ORDER BY timestamp DESC")
    rows = c.fetchall()
    conn.close()
    available_rooms = [
        {
            "building": r[0],
            "floor": r[1],
            "classroom_number": r[2],
            "classtime": r[3]
        }
        for r in rows
    ]
    return jsonify({'success': True, 'available_rooms': available_rooms})

@app.route('/api/sensor_data', methods=['POST'])
def receive_sensor_data():
    data = request.get_json()
    sensor_id = data.get('sensor_id')
    location = data.get('location')
    current_count = data.get('current_count')
    total_entries = data.get('total_entries')
    total_exits = data.get('total_exits')
    timestamp = data.get('timestamp')

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO sensor_logs (sensor_id, location, current_count, total_entries, total_exits, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (sensor_id, location, current_count, total_entries, total_exits, timestamp))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'データを受信・保存しました'})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
