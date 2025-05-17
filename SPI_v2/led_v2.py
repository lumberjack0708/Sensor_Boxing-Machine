import time
from rpi_ws281x import Adafruit_NeoPixel, Color

class LedController:
    """
    控制 WS281x LED 燈條的類別，支援 SPI 介面，讓一般使用者(非root)也能控制燈條。

    使用說明（SPI模式）：
    1. 請將LED資料線接到樹莓派的SPI MOSI腳位（如GPIO 10/BCM 10）。
    2. 於系統啟用SPI介面（sudo raspi-config → Interfacing Options → SPI）。
    3. 將使用者加入spi群組（sudo usermod -aG spi your_username），登出再登入或重開機。
    4. 初始化LedController時，請將led_pin設為10（SPI0 MOSI），channel設為0，freq_hz設為較高值（如2000000）。
    5. 執行本程式時不需sudo。

    例如：
        controller = LedController(led_pin=10, led_count=60, freq_hz=2000000, dma=10, invert=False, brightness=25, channel=0)
    """

    def __init__(self, led_pin=10, led_count=60, freq_hz=2000000, dma=10, invert=False, brightness=25, channel=0):
        """
        初始化 LED 控制器。

        參數:
            led_pin (int): SPI MOSI腳位請設為10。
            led_count (int): LED燈珠數量。
            freq_hz (int): SPI時脈頻率，建議2000000~32000000。
            dma (int): SPI模式下會被忽略。
            invert (bool): 是否反轉訊號。
            brightness (int): 亮度(0-255)。
            channel (int): SPI通道，0對應/dev/spidev0.0。
        """
        self.strip = Adafruit_NeoPixel(led_count, led_pin, freq_hz, dma, invert, brightness, channel)
        self.rainbow_j_offset = 0
        self.is_on = False
        self.default_brightness = brightness

    def begin(self):
        """啟動 LED 燈條通訊。"""
        if self.is_on:
            print("LED 燈條已啟動。")
            return
        try:
            self.strip.begin()
            self.is_on = True
            print("LED 燈條初始化並啟動成功（SPI模式，非root可用）。")
        except Exception as e:
            print(f"LED 燈條啟動失敗: {e}")
            self.strip = None
            self.is_on = False

    def _wheel(self, pos):
        """產生彩虹循環中的單一顏色。"""
        if pos < 0 or pos > 255:
            pos = pos % 256
        if pos < 85:
            return Color(pos * 3, 255 - pos * 3, 0)
        elif pos < 170:
            pos -= 85
            return Color(255 - pos * 3, 0, pos * 3)
        else:
            pos -= 170
            return Color(0, pos * 3, 255 - pos * 3)

    def update_rainbow_cycle_frame(self, j_offset=None):
        """更新並顯示彩虹循環動畫的下一幀。"""
        if not self.strip or not self.is_on:
            return
        current_offset = j_offset if j_offset is not None else self.rainbow_j_offset
        for i in range(self.strip.numPixels()):
            pixel_color_pos = (int(i * 256 / self.strip.numPixels()) + current_offset) & 255
            self.strip.setPixelColor(i, self._wheel(pixel_color_pos))
        self.strip.show()
        if j_offset is None:
            self.rainbow_j_offset = (self.rainbow_j_offset + 1) % 256

    def reset_rainbow_animation_state(self):
        """重設彩虹動畫的狀態。"""
        self.rainbow_j_offset = 0

    def clear(self):
        """清除所有 LED (設為黑色)。"""
        if not self.strip or not self.is_on:
            return
        for i in range(self.strip.numPixels()):
            self.strip.setPixelColor(i, Color(0, 0, 0))
        self.strip.show()

    def set_brightness(self, brightness_value, show=True):
        """設定 LED 燈條的亮度。"""
        if not self.strip or not self.is_on:
            return
        new_brightness = max(0, min(255, int(brightness_value)))
        self.strip.setBrightness(new_brightness)
        if show:
            self.strip.show()

    def reset_to_default_brightness(self, show=True):
        """恢復到初始設定的亮度。"""
        self.set_brightness(self.default_brightness, show=show)

    def static_color(self, color, show=True):
        """將所有 LED 設定為指定的靜態顏色。"""
        if not self.strip or not self.is_on:
            return
        for i in range(self.strip.numPixels()):
            self.strip.setPixelColor(i, color)
        if show:
            self.strip.show()

    def show_flash_pattern(self, flash_color=Color(50, 50, 50), times=3, duration_on=0.1, duration_off=0.1):
        """顯示一個簡單的閃爍燈效。"""
        if not self.strip or not self.is_on:
            return
        for _ in range(times):
            if not self.is_on: break
            self.static_color(flash_color)
            time.sleep(duration_on)
            if not self.is_on: break
            self.clear()
            time.sleep(duration_off)

    def color_wipe(self, color, wait_ms=50):
        """依序點亮每顆 LED，呈現指定顏色的 wiping 效果。"""
        if not self.strip or not self.is_on: return
        for i in range(self.strip.numPixels()):
            self.strip.setPixelColor(i, color)
            self.strip.show()
            time.sleep(wait_ms / 1000.0)

    def rainbow_effect(self, wait_ms=20, iterations=1):
        """整條 LED 同步漸變彩虹。"""
        if not self.strip or not self.is_on: return
        for j in range(256 * iterations):
            for i in range(self.strip.numPixels()):
                self.strip.setPixelColor(i, self._wheel((i + j) & 255))
            self.strip.show()
            time.sleep(wait_ms / 1000.0)
            if not self.is_on: break

# 範例程式（SPI模式，非root可用）
if __name__ == '__main__':
    LED_COUNT = 60
    LED_PIN = 10         # SPI0 MOSI
    LED_FREQ_HZ = 2000000  # SPI時脈頻率
    LED_DMA = 10         # SPI模式下會被忽略
    LED_BRIGHTNESS = 25
    LED_INVERT = False
    LED_CHANNEL = 0      # SPI0

    controller = LedController(LED_PIN, LED_COUNT, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    controller.begin()

    if controller.strip and controller.is_on:
        print("按下 Ctrl-C 結束範例程式...")
        try:
            print("顯示彩虹循環...")
            for _ in range(256):
                controller.update_rainbow_cycle_frame()
                time.sleep(0.02)
            print("測試閃爍模式...")
            controller.show_flash_pattern(flash_color=Color(0,0,255), times=2, duration_on=0.2, duration_off=0.2)
            time.sleep(0.5)
            print("再次顯示彩虹...")
            controller.reset_rainbow_animation_state()
            for _ in range(256):
                controller.update_rainbow_cycle_frame()
                time.sleep(0.02)
            print("\n測試靜態紅色...")
            controller.static_color(Color(255, 0, 0))
            time.sleep(2)
            controller.clear()
        except KeyboardInterrupt:
            print("\n程式結束。")
        finally:
            print("清除 LED...")
            controller.clear()
            print("LED 已清除。")
    else:
        print("無法執行 LED 範例，因為燈條初始化失敗。")