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
        self.sensor1_state = False
        self.sensor2_state = False
        self.last_detection_time = 0
        self.detection_sequence = []
        self.debounce_time = 0.5
        if GPIO_AVAILABLE:
            self.setup_gpio()
        else:
            print("シミュレーションモードで起動")

    def setup_gpio(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(SENSOR1_PIN, GPIO.IN)
        GPIO.setup(SENSOR2_PIN, GPIO.IN)
        print(f"GPIO設定完了 - センサー1: Pin{SENSOR1_PIN}, センサー2: Pin{SENSOR2_PIN}")

    def read_sensors(self):
        if GPIO_AVAILABLE:
            sensor1 = GPIO.input(SENSOR1_PIN)
            sensor2 = GPIO.input(SENSOR2_PIN)
        else:
            import random
            sensor1 = random.choice([0, 0, 0, 1]) > 0
            sensor2 = random.choice([0, 0, 0, 1]) > 0
        return bool(sensor1), bool(sensor2)

    def add_detection_event(self, sensor_num, state):
        current_time = time.time()
        if current_time - self.last_detection_time < self.debounce_time:
            return
        self.last_detection_time = current_time
        self.detection_sequence.append({
            'sensor': sensor_num,
            'state': state,
            'time': current_time,
            'timestamp': datetime.now().isoformat()
        })
        self.detection_sequence = [
            event for event in self.detection_sequence
            if current_time - event['time'] < 10
        ]
        self.analyze_movement()

    def analyze_movement(self):
        global current_count, total_entries, total_exits, detection_log
        if len(self.detection_sequence) < 2:
            return
        recent_events = self.detection_sequence[-4:]
        if self.check_entry_pattern(recent_events):
            current_count += 1
            total_entries += 1
            self.log_movement("入室", current_count)
            self.detection_sequence.clear()
        elif self.check_exit_pattern(recent_events):
            current_count = max(0, current_count - 1)
            total_exits += 1
            self.log_movement("退室", current_count)
            self.detection_sequence.clear()

    def check_entry_pattern(self, events):
        if len(events) < 2:
            return False
        for i in range(len(events) - 1):
            if (events[i]['sensor'] == 1 and events[i]['state'] == True and
                events[i+1]['sensor'] == 2 and events[i+1]['state'] == True):
                return True
        return False

    def check_exit_pattern(self, events):
        if len(events) < 2:
            return False
        for i in range(len(events) - 1):
            if (events[i]['sensor'] == 2 and events[i]['state'] == True and
                events[i+1]['sensor'] == 1 and events[i+1]['state'] == True):
                return True
        return False

    def log_movement(self, movement_type, new_count):
        log_entry = {
            'type': movement_type,
            'count': new_count,
            'timestamp': datetime.now().isoformat(),
            'total_entries': total_entries,
            'total_exits': total_exits
        }
        detection_log.append(log_entry)
        if len(detection_log) > 100:
            detection_log.pop(0)
        print(f"[{movement_type}] 現在人数: {new_count} (入室計: {total_entries}, 退室計: {total_exits})")

counter = PIRSensorCounter()

def sensor_monitoring_thread():
    global is_detecting
    print("センサー監視開始")
    prev_sensor1 = False
    prev_sensor2 = False
    try:
        while is_detecting:
            sensor1, sensor2 = counter.read_sensors()
            if sensor1 != prev_sensor1:
                counter.add_detection_event(1, sensor1)
                print(f"センサー1: {'ON' if sensor1 else 'OFF'}")
            if sensor2 != prev_sensor2:
                counter.add_detection_event(2, sensor2)
                print(f"センサー2: {'ON' if sensor2 else 'OFF'}")
            prev_sensor1 = sensor1
            prev_sensor2 = sensor2
            time.sleep(0.1)
    except Exception as e:
        print(f"センサー監視エラー: {e}")

@app.route('/')
def index():
    return render_template('unicon_sensor.html')

@app.route('/api/count')
def get_count():
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
    global is_detecting
    is_detecting = False
    return jsonify({'status': 'stopped'})

@app.route('/api/reset')
def reset_count():
    global current_count, total_entries, total_exits, detection_log
    current_count = 0
    total_entries = 0
    total_exits = 0
    detection_log.clear()
    return jsonify({'status': 'reset', 'count': 0})

@app.route('/api/log')
def get_log():
    return jsonify({'log': detection_log[-20:]})

@app.route('/api/send_to_unicon')
def send_to_unicon():
    data = {
        'sensor_id': 'classroom_A_entrance',
        'location': 'classroom_A',
        'current_count': current_count,
        'total_entries': total_entries,
        'total_exits': total_exits,
        'timestamp': datetime.now().isoformat(),
        'sensor_type': 'pir_dual'
    }
    unicon_server_url = "http://133.14.14.13:5000/api/sensor_data"
    try:
        response = requests.post(unicon_server_url, json=data, timeout=5)
        return jsonify({'status': 'sent', 'response_code': response.status_code})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/sensor_status')
def sensor_status():
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
