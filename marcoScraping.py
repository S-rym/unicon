from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import time
import getpass

# ターミナルから学籍番号とパスワードを入力
student_id = input("学籍番号を入力してください(英字部分は「大文字」): ")
password = getpass.getpass("パスワードを入力してください: ")

# ブラウザ起動（Chrome）
driver = webdriver.Chrome()

# ログインページへ
driver.get("https://marco-s.ms.dendai.ac.jp/")

time.sleep(3)

# 学籍番号とパスワードを入力
username_input = driver.find_element(By.NAME, "login")
password_input = driver.find_element(By.NAME, "password")

username_input.send_keys(student_id)
password_input.send_keys(password)
password_input.send_keys(Keys.RETURN)

time.sleep(3)

# ログイン失敗時のエラーメッセージを確認
error_message_elements = driver.find_elements(By.XPATH, "//li[contains(text(), 'ユーザーIDまたはパスワードが正しくありません。')]")
if error_message_elements:
    print("ログインに失敗しました。学籍番号またはパスワードが間違っています。")
    driver.quit()
    exit()
else:
    print("ログイン成功")

# 教室の利用状況ページへ移動
hover_target = driver.find_element(By.LINK_TEXT, "施設予約") 

actions = ActionChains(driver)
actions.move_to_element(hover_target).perform()

time.sleep(1) 

roomReserve_button = driver.find_element(By.LINK_TEXT, "施設予約状況") 
roomReserve_button.click()

time.sleep(1)

campusSelect_button = driver.find_element(By.ID, "bunruiTree") 
campusSelect_button.click()

time.sleep(1)

campusSelect_cbx = driver.find_element(By.CSS_SELECTOR, "label[for='cbx_1_2']")
campusSelect_cbx.click()

time.sleep(1)

campusSelectAgree_button = driver.find_element(By.ID, "shisetsuTreeAgree") 
campusSelectAgree_button.click()

time.sleep(1)

search_button = driver.find_element(By.CSS_SELECTOR, ".btn.agree.search.search_btn")
search_button.click()

time.sleep(5)

# 予約済み教室名と使用時間を取得
reserved_elements = driver.find_elements(By.CSS_SELECTOR, 'div.schedule[data-yoyakuname="予約済み"]')

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

# 時限でソート
reservations_sorted = sorted(reservations, key=lambda x: x[1])

# ソート後のデータを表示
for classroom, time_slot in reservations_sorted:
    print(f"{time_slot} : {classroom}")

# 8. 終了
driver.quit()
