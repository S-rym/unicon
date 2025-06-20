#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UNICON - 人数カウントセンサーシステム
赤外線人感センサー × 2 を使用した入退室検知
"""
from flask import Flask, render_template, jsonify
import threading
import time
import json
from datetime import datetime
import requests
# GPIO制御用
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    print("RPi.GPIO not available - running in simulation mode")
    GPIO_AVAILABLE = False
app = Flask(__name__)
# GPIO設定
SENSOR1_PIN = 18  # Pin12 - 入口側センサー
SENSOR2_PIN = 24  # Pin18 - 出口側センサー
# グローバル変数
current_count = 0
total_entries = 0
total_exits = 0
is_detecting = False
detection_log = []
class PIRSensorCounter:
    def __init__(self):
        self.count = 0
        self.sensor1_state = False  # 入口センサー状態
        self.sensor2_state = False  # 出口センサー状態
        self.last_detection_time = 0
        self.detection_sequence = []  # 検知シーケンス
        self.debounce_time = 0.5  # 500ms debounce
        if GPIO_AVAILABLE:
            self.setup_gpio()
        else:
            print("シミュレーションモードで起動")
    def setup_gpio(self):
        """GPIO初期設定"""
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(SENSOR1_PIN, GPIO.IN)
        GPIO.setup(SENSOR2_PIN, GPIO.IN)
        print(f"GPIO設定完了 - センサー1: Pin{SENSOR1_PIN}, センサー2: Pin{SENSOR2_PIN}")
    def read_sensors(self):
        """センサー状態読み取り"""
        if GPIO_AVAILABLE:
            sensor1 = GPIO.input(SENSOR1_PIN)
            sensor2 = GPIO.input(SENSOR2_PIN)
        else:
            # シミュレーション用
            import random
            sensor1 = random.choice([0, 0, 0, 1]) > 0  # 25%の確率で検知
            sensor2 = random.choice([0, 0, 0, 1]) > 0
        return bool(sensor1), bool(sensor2)
    def add_detection_event(self, sensor_num, state):
        """検知イベントを記録"""
        current_time = time.time()
        # デバウンス処理
        if current_time - self.last_detection_time < self.debounce_time:
            return
        self.last_detection_time = current_time
        # 検知シーケンスに追加
        self.detection_sequence.append({
            'sensor': sensor_num,
            'state': state,
            'time': current_time,
            'timestamp': datetime.now().isoformat()
        })
        # 古いイベントを削除（10秒以上前）
        self.detection_sequence = [
            event for event in self.detection_sequence
            if current_time - event['time'] < 10
        ]
        # 入退室判定
        self.analyze_movement()
    def analyze_movement(self):
        """検知パターンから入退室を判定"""
        global current_count, total_entries, total_exits, detection_log
        if len(self.detection_sequence) < 2:
            return
        # 最近の検知パターンを分析
        recent_events = self.detection_sequence[-4:]  # 最新4イベント
        # 入室パターン: センサー1 → センサー2
        if self.check_entry_pattern(recent_events):
            current_count += 1
            total_entries += 1
            self.log_movement("入室", current_count)
            self.detection_sequence.clear()  # シーケンスリセット
        # 退室パターン: センサー2 → センサー1
        elif self.check_exit_pattern(recent_events):
            current_count = max(0, current_count - 1)
            total_exits += 1
            self.log_movement("退室", current_count)
            self.detection_sequence.clear()  # シーケンスリセット
    def check_entry_pattern(self, events):
        """入室パターンチェック"""
        if len(events) < 2:
            return False
        # センサー1がON → センサー2がON のパターンを探す
        for i in range(len(events) - 1):
            if (events[i]['sensor'] == 1 and events[i]['state'] == True and
                events[i+1]['sensor'] == 2 and events[i+1]['state'] == True):
                return True
        return False
    def check_exit_pattern(self, events):
        """退室パターンチェック"""
        if len(events) < 2:
            return False
        # センサー2がON → センサー1がON のパターンを探す
        for i in range(len(events) - 1):
            if (events[i]['sensor'] == 2 and events[i]['state'] == True and
                events[i+1]['sensor'] == 1 and events[i+1]['state'] == True):
                return True
        return False
    def log_movement(self, movement_type, new_count):
        """移動ログを記録"""
        log_entry = {
            'type': movement_type,
            'count': new_count,
            'timestamp': datetime.now().isoformat(),
            'total_entries': total_entries,
            'total_exits': total_exits
        }
        detection_log.append(log_entry)
        # ログは最新100件まで保持
        if len(detection_log) > 100:
            detection_log.pop(0)
        print(f"[{movement_type}] 現在人数: {new_count} (入室計: {total_entries}, 退室計: {total_exits})")
counter = PIRSensorCounter()
def sensor_monitoring_thread():
    """センサー監視スレッド"""
    global is_detecting
    print("センサー監視開始")
    prev_sensor1 = False
    prev_sensor2 = False
    try:
        while is_detecting:
            # センサー状態読み取り
            sensor1, sensor2 = counter.read_sensors()
            # 状態変化を検知
            if sensor1 != prev_sensor1:
                counter.add_detection_event(1, sensor1)
                print(f"センサー1: {'ON' if sensor1 else 'OFF'}")
            if sensor2 != prev_sensor2:
                counter.add_detection_event(2, sensor2)
                print(f"センサー2: {'ON' if sensor2 else 'OFF'}")
            prev_sensor1 = sensor1
            prev_sensor2 = sensor2
            time.sleep(0.1)  # 100ms間隔で監視
    except Exception as e:
        print(f"センサー監視エラー: {e}")
@app.route('/')
def index():
    """メインページ"""
    return render_template('unicon_sensor.html')
@app.route('/api/count')
def get_count():
    """現在の人数とステータス取得"""
    return jsonify({
        'count': current_count,
        'total_entries': total_entries,
        'total_exits': total_exits,
        'timestamp': datetime.now().isoformat(),
        'status': 'detecting' if is_detecting else 'stopped',
        'gpio_available': GPIO_AVAILABLE
    })
@app.route('/api/start')
def start_detection():
    """検出開始"""
    global is_detecting
    if not is_detecting:
        is_detecting = True
        thread = threading.Thread(target=sensor_monitoring_thread)
        thread.daemon = True
        thread.start()
        return jsonify({'status': 'started'})
    return jsonify({'status': 'already_running'})
@app.route('/api/stop')
def stop_detection():
    """検出停止"""
    global is_detecting
    is_detecting = False
    return jsonify({'status': 'stopped'})
@app.route('/api/reset')
def reset_count():
    """カウントリセット"""
    global current_count, total_entries, total_exits, detection_log
    current_count = 0
    total_entries = 0
    total_exits = 0
    detection_log.clear()
    return jsonify({'status': 'reset', 'count': 0})
@app.route('/api/log')
def get_log():
    """検知ログ取得"""
    return jsonify({'log': detection_log[-20:]})  # 最新20件
@app.route('/api/send_to_unicon')
def send_to_unicon():
    """UNICONサーバにデータ送信"""
    data = {
        'sensor_id': 'classroom_A_entrance',
        'location': 'classroom_A',
        'current_count': current_count,
        'total_entries': total_entries,
        'total_exits': total_exits,
        'timestamp': datetime.now().isoformat(),
        'sensor_type': 'pir_dual'
    }
    # TODO: UNICONサーバのURL設定
    # unicon_server_url = "http://UNICON_SERVER_IP:PORT/api/sensor_data"
    # try:
    #     response = requests.post(unicon_server_url, json=data, timeout=5)
    #     return jsonify({'status': 'sent', 'response_code': response.status_code})
    # except Exception as e:
    #     return jsonify({'status': 'error', 'message': str(e)})
    # デバッグ用
    print(f"UNICON送信データ: {data}")
    return jsonify({'status': 'debug_mode', 'data': data})
@app.route('/api/sensor_status')
def sensor_status():
    """センサーハードウェア状態"""
    if GPIO_AVAILABLE:
        sensor1, sensor2 = counter.read_sensors()
        return jsonify({
            'sensor1': sensor1,
            'sensor2': sensor2,
            'gpio_mode': 'hardware'
        })
    else:
        return jsonify({
            'sensor1': False,
            'sensor2': False,
            'gpio_mode': 'simulation'
        })
def cleanup():
    """終了処理"""
    global is_detecting
    is_detecting = False
    if GPIO_AVAILABLE:
        GPIO.cleanup()
if __name__ == '__main__':
    try:
        print("=== UNICON 人数カウントセンサー ===")
        print("大学空き教室混雑状況検知システム")
        print(f"モード: {'ハードウェア' if GPIO_AVAILABLE else 'シミュレーション'}")
        print("ブラウザで http://192.168.2.116:5000 にアクセス")
        print("Ctrl+C で終了")
        app.run(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        print("\nシステム終了中...")
    finally:
        cleanup()