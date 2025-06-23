from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import sys
import csv
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import tempfile

if len(sys.argv) < 3:
    print("使用法: python3 your_script_name.py <学籍番号> <パスワード> ")
    sys.exit(1)

student_id = sys.argv[1]
password = sys.argv[2]

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
    print("サイトにアクセスできませんでした。IP制限の可能性があります。")
    print(f"エラー詳細: {e}")
    driver.quit()
    sys.exit()
except TimeoutException:
    print("ログインページの読み込みに失敗しました。")
    driver.quit()
    sys.exit()

username_input = driver.find_element(By.NAME, "login")
password_input = driver.find_element(By.NAME, "password")

username_input.send_keys(student_id)
password_input.send_keys(password)
password_input.send_keys(Keys.RETURN)

WebDriverWait(driver, 10).until(
    EC.any_of(
        EC.presence_of_element_located((By.LINK_TEXT, "施設予約")),
        EC.presence_of_element_located((By.XPATH, "//li[contains(text(), 'ユーザーIDまたはパスワードが正しくありません。')]"))
    )
)

error_message_elements = driver.find_elements(By.XPATH, "//li[contains(text(), 'ユーザーIDまたはパスワードが正しくありません。')]")
if error_message_elements:
    print("ログインに失敗しました。学籍番号またはパスワードが間違っています。")
    driver.quit()
    sys.exit()

hover_target = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.LINK_TEXT, "施設予約"))
)
actions = ActionChains(driver)
actions.move_to_element(hover_target).perform()

roomReserve_button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.LINK_TEXT, "施設予約状況"))
)
roomReserve_button.click()

campusSelect_button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.ID, "bunruiTree"))
)
campusSelect_button.click()

campusSelect_cbx = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, "label[for='cbx_1_2']"))
)
driver.execute_script("arguments[0].scrollIntoView(true);", campusSelect_cbx)
campusSelect_cbx.click()

campusSelectAgree_button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.ID, "shisetsuTreeAgree"))
)
campusSelectAgree_button.click()

search_button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn.agree.search.search_btn"))
)
search_button.click()

try:
    reserved_elements = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.schedule[data-yoyakuname="予約済み"]'))
    )
except TimeoutException:
    reserved_elements = []

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

def parse_shisetsucdlist(code):
    code = str(code).zfill(9)
    goukan = str(int(code[1:3]))
    floor = str(int(code[3:5]))
    room_id = code[5:7]
    classroom_number = f"{goukan}{floor}{room_id}"
    return goukan, floor, classroom_number

reserved_classrooms_by_slot = {slot[0]: set() for slot in time_slots}
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

# 空き教室抽出
all_available_rooms = {}
for slot_name, _, _ in time_slots:
    reserved_set = reserved_classrooms_by_slot.get(slot_name, set())
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

# 予約済み教室も辞書形式で用意
all_reserved_rooms = {}
for slot_name, _, _ in time_slots:
    reserved_set = reserved_classrooms_by_slot.get(slot_name, set())
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
