from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from collections import defaultdict
import tempfile
import json
import sys
import csv

# 引数チェック
if len(sys.argv) < 3:
    print("使用法: python3 marcoScraping.py <学籍番号> <パスワード>", file=sys.stderr)
    sys.exit(1)

student_id = sys.argv[1]
password = sys.argv[2]

# Chromeオプション設定
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument(f"--user-data-dir={tempfile.mkdtemp()}")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.binary_location = '/opt/google/chrome/google-chrome'  # 適宜修正
service = Service('/home/tatsumi/unicon_app/chromedriver-linux64/chromedriver-linux64/chromedriver')  # 適宜修正

driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    driver.get("https://marco-s.ms.dendai.ac.jp/")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "login"))
    )
except WebDriverException as e:
    print("サイトにアクセスできませんでした。IP制限の可能性があります。", file=sys.stderr)
    print(f"エラー詳細: {e}", file=sys.stderr)
    driver.quit()
    sys.exit(1)
except TimeoutException:
    print("ログインページの読み込みに失敗しました。", file=sys.stderr)
    driver.quit()
    sys.exit(1)

# ログイン処理
username_input = driver.find_element(By.NAME, "login")
password_input = driver.find_element(By.NAME, "password")
username_input.send_keys(student_id)
password_input.send_keys(password)
password_input.send_keys(Keys.RETURN)

# ログイン後判定
try:
    WebDriverWait(driver, 10).until(
        EC.any_of(
            EC.presence_of_element_located((By.LINK_TEXT, "施設予約")),
            EC.presence_of_element_located((By.XPATH, "//li[contains(text(), 'ユーザーIDまたはパスワードが正しくありません。')]"))
        )
    )
except TimeoutException:
    print("ログイン後のページ読み込みに失敗しました。", file=sys.stderr)
    driver.quit()
    sys.exit(1)

if driver.find_elements(By.XPATH, "//li[contains(text(), 'ユーザーIDまたはパスワードが正しくありません。')]"):
    print("ログインに失敗しました。学籍番号またはパスワードが間違っています。", file=sys.stderr)
    driver.quit()
    sys.exit(1)

# 施設予約ページへ遷移
hover_target = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.LINK_TEXT, "施設予約")))
ActionChains(driver).move_to_element(hover_target).perform()

roomReserve_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.LINK_TEXT, "施設予約状況")))
roomReserve_button.click()

campusSelect_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "bunruiTree")))
campusSelect_button.click()

campusSelect_cbx = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "label[for='cbx_1_2']")))
driver.execute_script("arguments[0].scrollIntoView(true);", campusSelect_cbx)
campusSelect_cbx.click()

campusSelectAgree_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "shisetsuTreeAgree")))
campusSelectAgree_button.click()

search_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn.agree.search.search_btn")))
search_button.click()

# 予約情報取得
try:
    reserved_elements = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.schedule[data-yoyakuname="予約済み"]'))
    )
except TimeoutException:
    reserved_elements = []

# 時限スロット定義
time_slots = [
    ("1時限", "090000", "110000"),
    ("2時限", "110000", "125000"),
    ("3時限", "125000", "152000"),
    ("4時限", "152000", "171000"),
    ("5時限", "171000", "190000"),
]

def get_time_slot(start_time, end_time):
    for slot_name, slot_start, slot_end in time_slots:
        if slot_start <= start_time <= slot_end and slot_start <= end_time <= slot_end:
            return slot_name
    print(f"[警告] 不明な時限: start={start_time}, end={end_time}", file=sys.stderr)
    return "不明な時限"

def parse_shisetsucdlist(code):
    code = str(code).zfill(9)
    goukan = str(int(code[1:3]))
    floor = str(int(code[3:5]))
    room_id = code[5:7]
    classroom_number = f"{goukan}{floor}{room_id}"
    return goukan, floor, classroom_number

reserved_classrooms_by_slot = defaultdict(set)

for elem in reserved_elements:
    code_raw = elem.get_attribute("data-shisetsucdlist") or ""
    codes = code_raw.replace('<br>', '\n').replace('<br />', '\n').splitlines()
    start_time = elem.get_attribute("data-starthms")
    end_time = elem.get_attribute("data-endhms")
    time_slot = get_time_slot(start_time, end_time)
    for code in codes:
        code = code.strip()
        if code:
            goukan, floor, classroom_number = parse_shisetsucdlist(code)
            reserved_classrooms_by_slot[time_slot].add(classroom_number)

rooms = []
with open('room_list.csv', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        room_number = row["教室番号"]
        rooms.append({"教室番号": room_number})

def split_room_number(room_number):
    num = room_number.zfill(5)
    goukan = str(int(num[:2]))
    floor = str(int(num[2:3]))
    room_id = num[3:]
    if goukan in ("10", "12"):
        classroom_number = str(int(floor + room_id))
    else:
        classroom_number = str(int(num[1:]))
    return goukan, floor, classroom_number

all_available_rooms = {}
for slot_name in reserved_classrooms_by_slot:
    reserved_set = reserved_classrooms_by_slot[slot_name]
    available_rooms = [
        {
            "号館": split_room_number(room["教室番号"])[0],
            "階数": split_room_number(room["教室番号"])[1],
            "教室番号": split_room_number(room["教室番号"])[2],
        }
        for room in rooms
        if split_room_number(room["教室番号"])[2] not in reserved_set
    ]
    all_available_rooms[slot_name] = available_rooms

all_reserved_rooms = {}
for slot_name in reserved_classrooms_by_slot:
    reserved_set = reserved_classrooms_by_slot[slot_name]
    reserved_rooms = [
        {
            "号館": split_room_number(r)[0],
            "階数": split_room_number(r)[1],
            "教室番号": split_room_number(r)[2]
        }
        for r in reserved_set
    ]
    all_reserved_rooms[slot_name] = reserved_rooms

output_dict = {
    "空き教室": all_available_rooms,
    "予約済み教室": all_reserved_rooms,
}

print(json.dumps(output_dict, ensure_ascii=False, indent=2))

driver.quit()
