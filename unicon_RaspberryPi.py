import RPi.GPIO as GPIO
import time

#a,bは随時変える
PIR1_PIN = a #センサー1のGPIOピンの番号
PIR2_PIN = b #センサー2のGPIOピンの番号

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIR1_PIN, GPIO.IN)
GPIO.setup(PIR2_PIN, GPIO.IN)

count = 0  #人数

#初期の状態
pir1_prev = False
pir2_prev = False

print("Start counting people.")

try:
    while True:
        #現在の状態
        pir1_curr = GPIO.input(PIR1_PIN)
        pir2_curr = GPIO.input(PIR2_PIN)

        #センサーの変化
        pir1_change = pir1_curr and not pir1_prev
        pir2_change = pir2_curr and not pir2_prev

        #入退室判定
        if pir1_change:
            time_pir1 = time.time()

        if pir2_change:
            time_pir2 = time.time()

        # 入室判定：PIR1 → PIR2
        if ('time_pir1' in locals() and 'time_pir2' in locals()):
            if 0 < time_pir2 - time_pir1 < 2:  #PIR1が反応後、2秒以内にPIR2が反応したら入室とみなす（秒数は随時変える）
                count += 1
                print(f"Entering. Current number of people :  {count}")
                del time_pir1
                del time_pir2

            # 退室判定：PIR2 → PIR1
            elif 0 < time_pir1 - time_pir2 < 2: #PIR2が反応後、2秒以内にPIR1が反応したら入室とみなす（秒数は随時変える）
                if count > 0:
                    count -= 1
                print(f"Exit. Current number of people :  {count}")
                del time_pir1
                del time_pir2

        pir1_prev = pir1_curr
        pir2_prev = pir2_curr

        time.sleep(0.1)

except KeyboardInterrupt:
    print("Finish counting people.")

finally:
    GPIO.cleanup()
