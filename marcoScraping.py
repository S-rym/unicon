from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import getpass
import json
import sys

# ヘッドレスモードの設定を追加
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920,1080')

# ターミナルから学籍番号とパスワードを入力
student_id = sys.argv[1]
password = sys.argv[2]
classtime = sys.argv[3]

# ブラウザ起動（Chrome・ヘッドレス）
driver = webdriver.Chrome(options=options)

# ログインページへ
try:
    driver.get("https://marco-s.ms.dendai.ac.jp/")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "login"))
    )
except WebDriverException as e:
    print("サイトにアクセスできませんでした。IP制限の可能性があります。")
    print(f"エラー詳細: {e}")
    driver.quit()
    exit()
except TimeoutException:
    print("ログインページの読み込みに失敗しました。")
    driver.quit()
    exit()

# 学籍番号とパスワードを入力
username_input = driver.find_element(By.NAME, "login")
password_input = driver.find_element(By.NAME, "password")

username_input.send_keys(student_id)
password_input.send_keys(password)
password_input.send_keys(Keys.RETURN)

# ログイン後の画面が表示されるまで待機
WebDriverWait(driver, 10).until(
    EC.any_of(
        EC.presence_of_element_located((By.LINK_TEXT, "施設予約")),
        EC.presence_of_element_located((By.XPATH, "//li[contains(text(), 'ユーザーIDまたはパスワードが正しくありません。')]"))
    )
)

# ログイン失敗時のエラーメッセージを確認
error_message_elements = driver.find_elements(By.XPATH, "//li[contains(text(), 'ユーザーIDまたはパスワードが正しくありません。')]")
if error_message_elements:
    print("ログインに失敗しました。学籍番号またはパスワードが間違っています。")
    driver.quit()
    exit()
else:
    print("ログイン成功")

# 教室の利用状況ページへ移動
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

# 時限の時間割を定義
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

# 教室データをリストに格納
reservations = []
for elem in reserved_elements:
    classroom = elem.get_attribute("data-shisetsutip")
    start_time = elem.get_attribute("data-starthms")
    end_time = elem.get_attribute("data-endhms")
    time_slot = get_time_slot(start_time, end_time)
    reservations.append((classroom, time_slot))

target_slot = f"{classtime}時限"

unique_classrooms = set()
# ソート後のデータを表示（n時限目のみ）
for elem in reserved_elements:
    classroom_raw = elem.get_attribute("data-shisetsutip") or ""
    classrooms = classroom_raw.replace('<br>', '\n').replace('<br />', '\n').splitlines()

    start_time = elem.get_attribute("data-starthms")
    end_time = elem.get_attribute("data-endhms")
    time_slot = get_time_slot(start_time, end_time)

    if time_slot == target_slot:
        for c in classrooms:
            name = c.strip()
            if name:
                unique_classrooms.add(name)

# 出力
results = [{"classroom": name} for name in sorted(unique_classrooms)]
if not results:
    results.append({"classroom": None, "message": "予約なし"})

print(json.dumps(results, ensure_ascii=False, indent=2))


# 8. 終了
driver.quit()