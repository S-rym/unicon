from flask import Flask, render_template, request, jsonify
import subprocess
import json
import sqlite3
import os
import time  # 追加

app = Flask(__name__)

DB_PATH = 'reservations.db'

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
    c.execute('''
        CREATE TABLE IF NOT EXISTS available_rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            building TEXT,
            floor TEXT,
            classroom_number TEXT,
            classtime TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS sensor_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id TEXT,
            location TEXT,
            current_count INTEGER,
            total_entries INTEGER,
            total_exits INTEGER,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

# ✅ 全削除に修正済み
def save_reservations_to_db(student_id, _, reservations):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM reservations')  # 学生ID問わず全削除
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

# ✅ 全削除に修正済み
def save_available_rooms_to_db(student_id, available_data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM available_rooms')  # 学生ID問わず全削除
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

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    student_id = data.get('studentId')
    password = data.get('password')
    if not all([student_id, password]):
        return jsonify({'success': False, 'message': '必要な情報が不足しています。'}), 400
    try:
        result = subprocess.run([
            'python3', 'marcoScraping.py', student_id, password
        ], capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        try:
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

                return jsonify({'success': True, 'message': 'ログイン成功', 'data': all_reserved})

            else:
                return jsonify({'success': False, 'message': '予約情報の形式が正しくありません。'})

        except json.JSONDecodeError:
            return jsonify({'success': False, 'message': 'IDまたはパスワードが間違っています。'})
    except subprocess.CalledProcessError as e:
        return jsonify({
            'success': False,
            'message': 'IDまたはパスワードが間違っているか、予期せぬエラーが発生しています。',
            'details': e.stderr
        }), 500

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
