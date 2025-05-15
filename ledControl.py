import board
import neopixel
import time

# 設定燈條參數
LED_COUNT = 8         # LED 總數，請依你的燈條數量調整
LED_PIN = board.D18   # 預設 GPIO18 (PIN 12)，可依需求更改
ORDER = neopixel.GRB  # WS2812B 預設色彩順序

# 初始化燈條
pixels = neopixel.NeoPixel(LED_PIN, LED_COUNT, brightness=0.2, auto_write=False, pixel_order=ORDER)

def color_wipe(color, wait_ms=50):
    for i in range(LED_COUNT):
        pixels[i] = color
        pixels.show()
        time.sleep(wait_ms / 1000.0)

try:
    while True:
        color_wipe((255, 0, 0))  # 紅色
        time.sleep(1)
        color_wipe((0, 255, 0))  # 綠色
        time.sleep(1)
        color_wipe((0, 0, 255))  # 藍色
        time.sleep(1)
        color_wipe((0, 0, 0))    # 全部熄滅
        time.sleep(1)
except KeyboardInterrupt:
    pixels.fill((0, 0, 0))
    pixels.show()
