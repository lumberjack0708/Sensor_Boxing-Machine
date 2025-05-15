# 直接移植自 Arduino NeoPixel 範例，展示各種 WS281x LED 動畫效果

import time
from rpi_ws281x import *
import argparse

# LED 燈條設定
LED_COUNT      = 60     # LED 燈珠數量
LED_PIN        = 18     # 連接到燈條的 GPIO 腳位（18 為 PWM 腳位）
#LED_PIN        = 10    # 若用 SPI 則用 GPIO 10（/dev/spidev0.0）
LED_FREQ_HZ    = 800000  # LED 訊號頻率（通常為 800kHz）
LED_DMA        = 10      # 用於產生訊號的 DMA 通道（可嘗試 10）
LED_BRIGHTNESS = 5      # 亮度設定（0 最暗，255 最亮）
LED_INVERT     = False   # 若使用 NPN 電晶體電平轉換則設為 True
LED_CHANNEL    = 0       # 若用 GPIO 13、19、41、45、53 則設為 1

# 定義各種動畫函式
def colorWipe(strip, color, wait_ms=50):
    """依序點亮每顆 LED，呈現漸變效果"""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms/1000.0)

def theaterChase(strip, color, wait_ms=50, iterations=10):
    """戲院追逐燈效果"""
    for j in range(iterations):
        for q in range(3):
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, color)
            strip.show()
            time.sleep(wait_ms/1000.0)
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, 0)

def wheel(pos):
    """產生彩虹顏色（0-255）"""
    if pos < 85:
        return Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return Color(0, pos * 3, 255 - pos * 3)

def rainbow(strip, wait_ms=20, iterations=1):
    """整條 LED 同步漸變彩虹"""
    for j in range(256*iterations):
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, wheel((i+j) & 255))
        strip.show()
        time.sleep(wait_ms/1000.0)

def rainbowCycle(strip, wait_ms=20, iterations=5):
    """彩虹顏色平均分布在整條 LED 上，並循環"""
    for j in range(256*iterations):
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, wheel((int(i * 256 / strip.numPixels()) + j) & 255))
        strip.show()
        time.sleep(wait_ms/1000.0)

def theaterChaseRainbow(strip, wait_ms=50):
    """彩虹版戲院追逐燈效果"""
    for j in range(256):
        for q in range(3):
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, wheel((i+j) % 255))
            strip.show()
            time.sleep(wait_ms/1000.0)
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, 0)

# 主程式邏輯
if __name__ == '__main__':
    # 處理命令列參數
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--clear', action='store_true', help='結束時清除 LED 顯示')
    args = parser.parse_args()

    # 建立 NeoPixel 物件
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    # 初始化（必須先呼叫一次）
    strip.begin()

    print ('按 Ctrl-C 可結束程式。')
    if not args.clear:
        print('若要結束時自動關燈，請加上 "-c" 參數')

    try:
        while True:
            print ('色彩漸變動畫')
            colorWipe(strip, Color(255, 0, 0))  # 紅色漸變
            colorWipe(strip, Color(0, 255, 0))  # 綠色漸變
            colorWipe(strip, Color(0, 0, 255))  # 藍色漸變
            print ('戲院追逐燈動畫')
            theaterChase(strip, Color(127, 127, 127))  # 白色追逐
            theaterChase(strip, Color(127,   0,   0))  # 紅色追逐
            theaterChase(strip, Color(  0,   0, 127))  # 藍色追逐
            print ('彩虹動畫')
            rainbow(strip)
            rainbowCycle(strip)
            theaterChaseRainbow(strip)

    except KeyboardInterrupt:
        if args.clear:
            colorWipe(strip, Color(0,0,0), 10)  # 關閉所有 LED