# RandomGenerate/SPI_v2/led_controller.py
import time
from rpi_ws281x import Adafruit_NeoPixel, Color

class LedController:
    """控制 WS281x LED 燈條的類別。"""

    def __init__(self, led_pin=18, led_count=60, freq_hz=800000, dma=10, invert=False, brightness=25, channel=0):
        """
        初始化 LED 控制器。

        參數:
            led_pin (int): 連接到燈條的 GPIO 腳位。
            led_count (int): LED 燈珠數量。
            freq_hz (int): LED 訊號頻率。
            dma (int): 用於產生訊號的 DMA 通道。
            invert (bool): 是否反轉訊號 (True/False)。
            brightness (int): 亮度 (0-255)。
            channel (int): LED 通道 (通常為 0)。
        """
        self.strip = Adafruit_NeoPixel(led_count, led_pin, freq_hz, dma, invert, brightness, channel)
        self.rainbow_j_offset = 0  # 用於彩虹動畫的內部狀態
        self.is_on = False # 追蹤燈條是否已 begin
        self.default_brightness = brightness # 儲存初始亮度

    def begin(self):
        """啟動 LED 燈條通訊。"""
        if self.is_on:
            print("LED 燈條已啟動。")
            return
        try:
            self.strip.begin()
            self.is_on = True
            print("LED 燈條初始化並啟動成功。")
        except Exception as e:
            print(f"LED 燈條啟動失敗: {e}")
            self.strip = None 
            self.is_on = False

    def _wheel(self, pos):
        """內部輔助函式，產生彩虹循環中的單一顏色。"""
        # pos 在 0-255 之間
        if pos < 0 or pos > 255: # 確保 pos 在範圍內
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
        """
        更新並顯示彩虹循環動畫的下一幀。
        
        參數:
            j_offset (int, optional): 可選的外部偏移值。如果提供，則使用此值而不是內部 rainbow_j_offset。
                                     這允許外部控制動畫狀態。
        """
        if not self.strip or not self.is_on:
            return
        
        # 使用提供的 j_offset 或內部狀態
        current_offset = j_offset if j_offset is not None else self.rainbow_j_offset
        
        for i in range(self.strip.numPixels()):
            pixel_color_pos = (int(i * 256 / self.strip.numPixels()) + current_offset) & 255
            self.strip.setPixelColor(i, self._wheel(pixel_color_pos))
        self.strip.show()
        
        # 只有在使用內部狀態時才更新 rainbow_j_offset
        if j_offset is None:
            self.rainbow_j_offset = (self.rainbow_j_offset + 1) % 256

    def reset_rainbow_animation_state(self):
        """重設彩虹動畫的狀態，使其從頭開始。"""
        self.rainbow_j_offset = 0
        # print("彩虹動畫狀態已重設。") # 可選的除錯訊息

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
        if show: self.strip.show()
        # print(f"LED 設定為靜態顏色: R={color.r} G={color.g} B={color.b}") # 減少日誌

    def breathing_light(self, color, peak_brightness_fraction=1.0, duration_sec=3, cycles=None, steps_per_cycle=50):
        """
        執行呼吸燈效果。
        參數:
            color (Color): 呼吸燈的基礎顏色。
            peak_brightness_fraction (float): 呼吸到最亮時，相對於LED初始化亮度的比例 (0.0-1.0)。
            duration_sec (int): 如果 cycles 未指定，則為總持續時間。
            cycles (int, optional): 呼吸次數。如果指定，則忽略 duration_sec。
            steps_per_cycle (int): 每個呼吸週期（暗->亮->暗）的步數。
        """
        if not self.strip or not self.is_on:
            return
        
        original_brightness = self.strip.getBrightness()
        target_peak_brightness = int(original_brightness * peak_brightness_fraction)
        if target_peak_brightness == 0 and original_brightness > 0: # 避免完全不亮，除非原始亮度就是0
            target_peak_brightness = min(10, original_brightness) # 至少有點亮度
        if target_peak_brightness == 0: # 如果原始亮度也是0，則無法呼吸
             self.static_color(Color(0,0,0)); return

        # print(f"DEBUG: Breathing light. Original Brightness: {original_brightness}, Target Peak: {target_peak_brightness}")

        half_steps = steps_per_cycle // 2
        step_delay = (duration_sec / (cycles if cycles else 1)) / steps_per_cycle if cycles else duration_sec / steps_per_cycle

        num_cycles = cycles if cycles else int(duration_sec / (step_delay * steps_per_cycle))
        if num_cycles == 0: num_cycles = 1

        for _ in range(num_cycles):
            # Fade in (暗到亮)
            for i in range(half_steps):
                current_b = int((i / half_steps) * target_peak_brightness)
                self.set_brightness(max(0,min(255,current_b)), show=False) # 確保亮度在範圍內
                self.static_color(color, show=True) # 用 static_color 來設定顏色，setBrightness 後需要 show
                # self.strip.show() # static_color 內部已有 show
                time.sleep(step_delay)
            
            # Fade out (亮到暗)
            for i in range(half_steps, 0, -1):
                current_b = int((i / half_steps) * target_peak_brightness)
                self.set_brightness(max(0,min(255,current_b)), show=False)
                self.static_color(color, show=True)
                # self.strip.show()
                time.sleep(step_delay)
        
        self.set_brightness(original_brightness) # 恢復原始亮度
        self.clear() # 呼吸結束後清除，或恢復到某個狀態
        print("呼吸燈效果完成。")

    def show_flash_pattern(self, flash_color=Color(50, 50, 50), times=3, duration_on=0.1, duration_off=0.1):
        """
        顯示一個簡單的閃爍燈效。

        參數:
            flash_color (Color): 閃爍時的顏色。
            times (int): 閃爍次數。
            duration_on (float): 每次亮燈的持續時間 (秒)。
            duration_off (float): 每次滅燈的持續時間 (秒)。
        """
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
        print("Color wipe 完成。")

    def theater_chase(self, color, wait_ms=50, iterations=10):
        """戲院追逐燈效果。"""
        if not self.strip or not self.is_on: return
        for j in range(iterations):
            for q in range(3):
                for i in range(0, self.strip.numPixels(), 3):
                    if i + q < self.strip.numPixels(): # 邊界檢查
                        self.strip.setPixelColor(i + q, color)
                self.strip.show()
                time.sleep(wait_ms / 1000.0)
                for i in range(0, self.strip.numPixels(), 3):
                    if i + q < self.strip.numPixels(): # 邊界檢查
                        self.strip.setPixelColor(i + q, 0)
        print("Theater chase 完成。")

    def rainbow_effect(self, wait_ms=20, iterations=1):
        """整條 LED 同步漸變彩虹 (不同於 rainbowCycle)。"""
        if not self.strip or not self.is_on: return
        print("開始 Rainbow effect...")
        for j in range(256 * iterations):
            for i in range(self.strip.numPixels()):
                self.strip.setPixelColor(i, self._wheel((i + j) & 255))
            self.strip.show()
            time.sleep(wait_ms / 1000.0)
            if not self.is_on: break # 允許中途停止
        print("Rainbow effect 完成。")

    def rainbow_cycle_effect(self, wait_ms=20, iterations=5):
        """彩虹顏色平均分布在整條 LED 上，並循環。"""
        if not self.strip or not self.is_on: return
        print("開始 Rainbow cycle effect...")
        for j in range(256 * iterations):
            for i in range(self.strip.numPixels()):
                self.strip.setPixelColor(i, self._wheel((int(i * 256 / self.strip.numPixels()) + j) & 255))
            self.strip.show()
            time.sleep(wait_ms / 1000.0)
            if not self.is_on: break # 允許中途停止
        print("Rainbow cycle effect 完成。")

    def theater_chase_rainbow(self, wait_ms=50, iterations=1, cycle_limit=256):
        """彩虹版戲院追逐燈效果。"""
        if not self.strip or not self.is_on: return
        print(f"開始 Theater chase rainbow (iterations={iterations}, cycle_limit={cycle_limit}, wait_ms={wait_ms})...")
        for _ in range(iterations): 
            for j in range(cycle_limit): # 使用 cycle_limit 控制顏色變化範圍
                for q in range(3):
                    for i in range(0, self.strip.numPixels(), 3):
                        if i + q < self.strip.numPixels():
                            self.strip.setPixelColor(i + q, self._wheel((i + j) % 255)) # 顏色仍然用 %255 來循環
                    self.strip.show()
                    time.sleep(wait_ms / 1000.0)
                    for i in range(0, self.strip.numPixels(), 3):
                        if i + q < self.strip.numPixels():
                            self.strip.setPixelColor(i + q, 0)
                if not self.is_on: break 
            if not self.is_on: break 
        print("Theater chase rainbow 完成。")

# 使用範例 (如果此檔案被直接執行)
if __name__ == '__main__':
    # LED 設定範例
    LED_COUNT = 60
    LED_PIN = 18       # GPIO pin connected to the pixels (must support PWM!).
    LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
    LED_DMA = 10       # DMA channel to use for generating signal (try 10)
    LED_BRIGHTNESS = 25 # Set to 0 for darkest and 255 for brightest
    LED_INVERT = False   # True to invert the signal (when using NPN transistor level shift)
    LED_CHANNEL = 0      # Set to '1' for GPIOs 13, 19, 41, 45 or 53

    controller = LedController(LED_PIN, LED_COUNT, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    controller.begin()

    if controller.strip and controller.is_on: # 確保 strip 初始化成功
        print("按下 Ctrl-C 結束範例程式...")
        try:
            print("顯示彩虹循環 (使用內部狀態)...")
            for _ in range(256):
                controller.update_rainbow_cycle_frame()
                time.sleep(0.02)
            
            print("顯示彩虹循環 (使用外部控制的 j_offset)...")
            external_j = 0
            for _ in range(256):
                controller.update_rainbow_cycle_frame(j_offset=external_j)
                external_j = (external_j + 1) % 256
                time.sleep(0.02)
            
            print("測試閃爍模式...")
            controller.show_flash_pattern(flash_color=Color(0,0,255), times=2, duration_on=0.2, duration_off=0.2)
            time.sleep(0.5)
            print("再次顯示彩虹...")
            controller.reset_rainbow_animation_state() # 重設後再開始
            for _ in range(256):
                controller.update_rainbow_cycle_frame()
                time.sleep(0.02)

            print("\n測試靜態紅色...")
            controller.static_color(Color(255, 0, 0))
            time.sleep(2)
            controller.clear()
            print("\n測試呼吸藍色 (3秒, 2個循環)...")
            controller.breathing_light(Color(0, 0, 255), duration_sec=3, cycles=2)
            controller.clear()

        except KeyboardInterrupt:
            print("\n程式結束。")
        finally:
            print("清除 LED...")
            controller.clear()
            print("LED 已清除。")
    else:
        print("無法執行 LED 範例，因為燈條初始化失敗。") 