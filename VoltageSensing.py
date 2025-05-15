# 壓電測試＋按鈕觸發（取3秒內電壓最高值）
# A0
import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import RPi.GPIO as GPIO

# 設定GPIO
btn_pin = 4  # GPIO4（實體腳位7）
GPIO.setmode(GPIO.BCM)
GPIO.setup(btn_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# 建立 I2C 介面
i2c = busio.I2C(board.SCL, board.SDA)

# 初始化 ADS1115
ads = ADS.ADS1115(i2c)

# 設定輸入通道 A0
chan = AnalogIn(ads, ADS.P0)

def monitor_anger(duration=3, threshold=0.24):
    print("開始偵測怒氣（3秒內取最高電壓）...")
    start_time = time.time()
    max_voltage = 0
    while time.time() - start_time < duration:
        voltage = chan.voltage
        if voltage > max_voltage:
            max_voltage = voltage
        time.sleep(0.01)  # 快速取樣
    print(f"3秒內最高電壓：{max_voltage:.3f} V")
    if max_voltage > threshold:
        print("你的怒氣已到達雲林")
    else:
        print("怒氣未達標，請再努力！")

if __name__ == "__main__":
    print("請按下按鈕開始怒氣測試（Ctrl+C 離開）")
    try:
        while True:
            if GPIO.input(btn_pin) == GPIO.HIGH:
                monitor_anger()
                # 等待按鈕放開，避免重複觸發
                while GPIO.input(btn_pin) == GPIO.HIGH:
                    time.sleep(0.05)
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("結束程式。")
    finally:
        GPIO.cleanup()

# 電壓: 0.002 V
# 電壓: 0.003 V
# 電壓: 1.497 V   ← 拍桌子時可能會跳到這種高值！
