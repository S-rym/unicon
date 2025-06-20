from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

import sys
import json
import tempfile
import time
import csv

# ターミナルから学籍番号とパスワードを取得
if len(sys.argv) < 3:
    print("使用法: python3 marcoScraping.py <学籍番号> <パスワード>")
    sys.exit(1)

student_id = sys.argv[1]
password = sys.argv[2]

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument(f"--user-data-dir={tempfile.mkdtemp()}")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.binary_location = '/opt/google/chrome/google-chrome'

service = Service('/home/tatsumi/unicon_app/chromedriver-linux64/chromedriver-linux64/chromedriver')
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    driver.get("https://marco-s.ms.dendai.ac.jp/")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "login")))
except (WebDriverException, TimeoutException):
    print("サイトにアクセスできませんでした。")
    driver.quit()
    sys.exit()

username_input = driver.find_element(By.NAME, "login")
password_input = driver.find_element(By.NAME, "password")
username_input.send_keys(student_id)
password_input.send_keys(password)
password_input.send_keys(Keys.RETURN)

WebDriverWait(driver, 10).until(EC.any_of(
    EC.presence_of_element_located((By.LINK_TEXT, "施設予約")),
    EC.presence_of_element_located((By.XPATH, "//li[contains(text(), 'ユーザーIDまたはパスワードが正しくありません。')]"))
))

if driver.find_elements(By.XPATH, "//li[contains(text(), 'ユーザーIDまたはパスワードが正しくありません。')]"):
    print("ログインに失敗しました。")
    driver.quit()
    sys.exit()

# 施設予約状況へ移動
hover_target = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.LINK_TEXT, "施設予約")))
ActionChains(driver).move_to_element(hover_target).perform()
WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.LINK_TEXT, "施設予約状況"))).click()
WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "bunruiTree"))).click()
cbx = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "label[for='cbx_1_2']")))
driver.execute_script("arguments[0].scrollIntoView(true);", cbx)
cbx.click()
WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "shisetsuTreeAgree"))).click()
WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn.agree.search.search_btn"))).click()

try:
    reserved_elements = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.schedule[data-yoyakuname="予約済み"]'))
    )
except TimeoutException:
    reserved_elements = []

# 時限の時間割定義
time_slots = [
    ("1時限", "090000", "110000"),
    ("2時限", "111000", "125000"),
    ("3時限", "134000", "152000"),
    ("4時限", "153000", "171000"),
    ("5時限", "172000", "190000"),
]

def get_time_slot(start_time, end_time):
    for slot_name, slot_start, slot_end in time_slots:
        if slot_start <= start_time <= slot_end and slot_start <= end_time <= slot_end:
            return slot_name
    return "不明な時限"

def parse_classroom_name(name):
    num = ''.join(filter(str.isdigit, name))
    if not num:
        return None, None, name
    num = num.zfill(5)
    try:
        goukan = str(int(num[:2]))
        floor = str(int(num[2:3]))
        room_id = num[3:]
    except ValueError:
        return None, None, name
    classroom_number = str(int(floor + room_id)) if goukan in ("10", "12") else str(int(num[1:]))
    return goukan, floor, classroom_number

def split_room_number(room_number):
    num = room_number.zfill(5)
    goukan = str(int(num[:2]))
    floor = str(int(num[2:3]))
    room_id = num[3:]
    classroom_number = str(int(floor + room_id)) if goukan in ("10", "12") else str(int(num[1:]))
    return goukan, floor, classroom_number

all_reservations = {}
unique_classrooms = set()
reserved_by_slot = {f"{i}時限": set() for i in range(1, 6)}

for elem in reserved_elements:
    classroom_raw = elem.get_attribute("data-shisetsutip") or ""
    classrooms = classroom_raw.replace('<br>', '\n').replace('<br />', '\n').splitlines()
    start_time = elem.get_attribute("data-starthms")
    end_time = elem.get_attribute("data-endhms")
    time_slot = get_time_slot(start_time, end_time)

    for c in classrooms:
        name = c.strip()
        if name and time_slot:
            all_reservations.setdefault(time_slot, []).append({"classroom": name, "classtime": time_slot})

    code_raw = elem.get_attribute("data-shisetsucdlist") or ""
    codes = code_raw.replace('<br>', '\n').replace('<br />', '\n').splitlines()
    for code in codes:
        code = code.strip()
        if code:
            goukan, floor, classroom_number = parse_classroom_name(code)
            if classroom_number:
                reserved_by_slot[time_slot].add(classroom_number)
                unique_classrooms.add((goukan, floor, classroom_number))

with open('room_list.csv', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rooms = [row["教室番号"] for row in reader]

available_by_slot = {}
for slot_name, _, _ in time_slots:
    reserved_set = reserved_by_slot[slot_name]
    available_this_slot = []
    for room_number in rooms:
        goukan, floor, classroom_number = split_room_number(room_number)
        if classroom_number not in reserved_set:
            available_this_slot.append({
                "号館": goukan, 
                "階数": floor, 
                "教室番号": classroom_number,
                "classtime": slot_name  # ここで時限を追加
                })
    available_by_slot[slot_name] = available_this_slot

output = {
    "reserved": all_reservations,
    "available": available_by_slot
}

print(json.dumps(output, ensure_ascii=False, indent=2))
driver.quit()