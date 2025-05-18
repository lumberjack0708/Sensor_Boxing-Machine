import time
import RPi.GPIO as GPIO
from led_controller import LedController

# 設定GPIO
btn_pin = 4  # GPIO4（實體腳位7）
GPIO.setmode(GPIO.BCM)
GPIO.setup(btn_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

if __name__ == "__main__":
    # print("請按下/放開 GPIO4 的按鈕進行測試（Ctrl+C 離開）")
    # try:
    #     last_state = GPIO.LOW
    #     while True:
    #         current_state = GPIO.input(btn_pin)
    #         if current_state == GPIO.HIGH and last_state == GPIO.LOW:
    #             print("按下")
    #         elif current_state == GPIO.LOW and last_state == GPIO.HIGH:
    #             print("放開")
    #         last_state = current_state
    #         time.sleep(0.01)
    # except KeyboardInterrupt:
    #     print("結束程式。")
    # finally:
    #     GPIO.cleanup()
    led_controller = LedController()
    led_controller.clear()
