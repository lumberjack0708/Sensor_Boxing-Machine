# RandomGenerate/SPI_v2/led_controller.py
import time
from rpi_ws281x import Adafruit_NeoPixel, Color

class LedController:
    """控制 WS281x LED 燈條的類別。"""

    def __init__(self, count, pin, freq_hz, dma, invert, brightness, channel):
        """
        初始化 LED 控制器。

        參數:
            count (int): LED 燈珠數量。
            pin (int): 連接到燈條的 GPIO 腳位。
            freq_hz (int): LED 訊號頻率。
            dma (int): 用於產生訊號的 DMA 通道。
            invert (bool): 是否反轉訊號 (True/False)。
            brightness (int): 亮度 (0-255)。
            channel (int): LED 通道 (通常為 0)。
        """
        self.strip = Adafruit_NeoPixel(count, pin, freq_hz, dma, invert, brightness, channel)
        self.rainbow_j_offset = 0  # 用於彩虹動畫的內部狀態
        self.is_on = False # 追蹤燈條是否已 begin

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

    def update_rainbow_cycle_frame(self):
        """更新並顯示彩虹循環動畫的下一幀。"""
        if not self.strip or not self.is_on:
            return
        
        for i in range(self.strip.numPixels()):
            pixel_color_pos = (int(i * 256 / self.strip.numPixels()) + self.rainbow_j_offset) & 255
            self.strip.setPixelColor(i, self._wheel(pixel_color_pos))
        self.strip.show()
        self.rainbow_j_offset = (self.rainbow_j_offset + 1) % (256 * 5) # 讓彩虹流動，與原 main.py 邏輯保持一致

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
            for i in range(self.strip.numPixels()):
                self.strip.setPixelColor(i, flash_color)
            self.strip.show()
            time.sleep(duration_on)
            self.clear()
            time.sleep(duration_off)

    def set_brightness(self, brightness_value):
        """設定 LED 燈條的亮度。"""
        if not self.strip or not self.is_on:
            return
        # Adafruit_NeoPixel 庫似乎沒有直接的方法在初始化後更改亮度而不重新 begin
        # 或者，如果 strip 物件允許直接修改 brightness 屬性並呼叫 show() 生效，則可以這樣做。
        # 經查 rpi_ws281x， Adafruit_NeoPixel 有 setBrightness 方法
        # 但它似乎是全域的，或者需要在 show() 之前呼叫
        # 最安全的方式可能是在初始化時設定好，或者接受它就是固定的
        # 為了安全，這裡我們假設亮度在初始化時設定，或提供一個警告
        # print("警告: 動態調整亮度可能需要重新初始化 LED 燈條，此處未實作。")
        # 實際上 Adafruit_NeoPixel 有 setBrightness 方法，可以直接使用
        new_brightness = max(0, min(255, int(brightness_value)))
        self.strip.setBrightness(new_brightness)
        self.strip.show() # 更新顯示以應用新的亮度
        # print(f"LED 亮度已設定為: {new_brightness}") # 可選的除錯訊息

# 使用範例 (如果此檔案被直接執行)
if __name__ == '__main__':
    # LED 設定範例 (與 main.py 中的參數一致)
    LED_COUNT = 60
    LED_PIN = 18       # GPIO pin connected to the pixels (must support PWM!).
    LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
    LED_DMA = 10       # DMA channel to use for generating signal (try 10)
    LED_BRIGHTNESS = 25 # Set to 0 for darkest and 255 for brightest
    LED_INVERT = False   # True to invert the signal (when using NPN transistor level shift)
    LED_CHANNEL = 0      # Set to '1' for GPIOs 13, 19, 41, 45 or 53

    controller = LedController(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    controller.begin()

    if controller.strip and controller.is_on: # 確保 strip 初始化成功
        print("按下 Ctrl-C 結束範例程式...")
        try:
            print("顯示彩虹循環...")
            for _ in range(256 * 5 * 2): # 顯示兩輪彩虹
                controller.update_rainbow_cycle_frame()
                time.sleep(0.02)
                if _ == 200: # 測試中途重設動畫
                    print("測試：重設彩虹動畫狀態")
                    controller.reset_rainbow_animation_state()
            
            print("測試閃爍模式...")
            controller.show_flash_pattern(flash_color=Color(0,0,255), times=2, duration_on=0.2, duration_off=0.2)
            time.sleep(0.5)
            print("再次顯示彩虹...")
            controller.reset_rainbow_animation_state() # 重設後再開始
            for _ in range(256):
                controller.update_rainbow_cycle_frame()
                time.sleep(0.02)

        except KeyboardInterrupt:
            print("\n程式結束。")
        finally:
            print("清除 LED...")
            controller.clear()
            print("LED 已清除。")
    else:
        print("無法執行 LED 範例，因為燈條初始化失敗。") 