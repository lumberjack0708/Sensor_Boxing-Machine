"""
負責初始化所有硬體元件和主要控制模組的設定檔。
"""
import RPi.GPIO as GPIO
import board # For LcdGameController and SensorHandler pin definitions
import pygame # For LcdGameController which inits pygame
import time # 為 if __name__ == '__main__' 中的測試新增

# 從專案的各個模組匯入類別
from .led_controller import LedController, Color # 為 if __name__ == '__main__' 中的 LED 測試新增 Color
from .sensor_handler import SensorHandler
from .emotion_calculator import EmotionCalculator
from .game_on_lcd import LcdGameController

# --- 硬體和模組設定常數 ---
# LED 燈條設定
LED_PIN        = 18
LED_COUNT      = 60
LED_FREQ_HZ    = 800000
LED_DMA        = 10
LED_BRIGHTNESS = 20
LED_INVERT     = False
LED_CHANNEL    = 0

# GPIO 按鈕設定
BTN_PIN = 4

# EmotionCalculator 參數設定
EMOTION_MIN_VOLTAGE_THRESHOLD = 0.02
EMOTION_MAX_VALUE = 800

# LcdGameController (ILI9341) 腳位設定 (使用 board.PinName)
LCD_CS_PIN = board.CE0
LCD_DC_PIN = board.D25
LCD_RESET_PIN = board.D24
LCD_BACKLIGHT_PIN = board.D27 # 可選，如果沒有背光控制則設為 None
LCD_BAUDRATE = 48000000
LCD_ROTATION = 270
# 遊戲資源路徑 (相對於 game_on_lcd.py 或主執行腳本的路徑)
# 假設 player.png 和 obstacle.png 與 game_on_lcd.py 在同一目錄
PLAYER_IMAGE_PATH = 'player.png' 
OBSTACLE_IMAGE_PATH = 'obstacle.png'

# 新增：拍擊跳躍的電壓閾值
PIEZO_JUMP_THRESHOLD = 0.1 

def initialize_systems():
    """
    初始化所有硬體驅動和邏輯模組。
    回傳一個包含已初始化物件實例的元組：
    (led_controller, sensor_handler, emotion_calc, lcd_game_ctrl)
    如果某個關鍵模組初始化失敗 (例如 LCD)，則對應的物件可能為 None。
    """
    print("系統設定：正在初始化所有硬體和模組...")
    
    # GPIO 初始化 (按鈕)
    # 注意：GPIO mode (BCM/BOARD) 和 cleanup 由主程式 (main.py) 管理較好，
    # 因為 setup 可能會被多次呼叫（儘管此處設計為一次性）。
    # 但為了集中設定，暫時在此處設定模式。
    # 如果 main.py 會在迴圈外設定和清理，這裡可以移除 setmode/setup。
    # 考量到 main.py 的 finally 會 cleanup，這裡的 setup 是安全的。
    GPIO.setmode(GPIO.BCM) # 如果 main.py 已設定，此處重複設定無害但可優化
    GPIO.setup(BTN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    print("按鈕 GPIO 初始化設定完成 (BTN_PIN 使用 BCM 模式)。")

    # 感測器處理器初始化
    sensor_handler = SensorHandler()
    if sensor_handler.initialize_ads1115():
        if not sensor_handler.setup_adc_channels(): # 使用預設通道 A0-A3
            print("警告 (系統設定): ADC 通道設定失敗。感測器可能無法正常讀取。")
    else:
        print("警告 (系統設定): ADS1115 初始化失敗。感測器讀取功能將不可用。")

    # LED 控制器初始化
    led_controller = LedController(
        count=LED_COUNT, pin=LED_PIN, freq_hz=LED_FREQ_HZ, dma=LED_DMA,
        invert=LED_INVERT, brightness=LED_BRIGHTNESS, channel=LED_CHANNEL
    )
    led_controller.begin() # 內部有成功/失敗的 print

    # 情緒計算器初始化
    emotion_calc = EmotionCalculator(
        min_voltage_threshold=EMOTION_MIN_VOLTAGE_THRESHOLD,
        max_emotion_value=EMOTION_MAX_VALUE
    )
    print(f"情緒計算器已初始化 (閾值={EMOTION_MIN_VOLTAGE_THRESHOLD}V, 上限={EMOTION_MAX_VALUE})。")

    # LCD 遊戲控制器初始化
    lcd_game_ctrl = None # 預設為 None
    try:
        lcd_game_ctrl = LcdGameController(
            cs_pin_board=LCD_CS_PIN,
            dc_pin_board=LCD_DC_PIN,
            rst_pin_board=LCD_RESET_PIN,
            backlight_pin_board=LCD_BACKLIGHT_PIN,
            baudrate=LCD_BAUDRATE,
            rotation=LCD_ROTATION,
            player_img_path=PLAYER_IMAGE_PATH,
            obstacle_img_path=OBSTACLE_IMAGE_PATH,
            sensor_handler_instance=sensor_handler, # <--- 將 sensor_handler 傳遞過去
            piezo_jump_threshold=PIEZO_JUMP_THRESHOLD # <--- 傳遞拍擊跳躍閾值
        )
        # LcdGameController 的 __init__ 內部會印出成功或拋出 RuntimeError
        print("LcdGameController 實例化成功 (詳細初始化狀態見其內部日誌)。")
    except RuntimeError as e:
        print(f"嚴重錯誤 (系統設定): LcdGameController 初始化失敗: {e}")
        # lcd_game_ctrl 會保持為 None
    except Exception as e:
        print(f"初始化 LcdGameController 時發生未預期錯誤: {e}")
        # lcd_game_ctrl 會保持為 None

    # Pygame 的 quit() 應由應用程式最外層 (main.py 的 finally) 管理。
    # LcdGameController 內部可能會 pygame.init()。

    print("系統設定：硬體和模組初始化流程完畢。")
    return led_controller, sensor_handler, emotion_calc, lcd_game_ctrl

# 測試函式 (如果直接執行此檔案)
if __name__ == '__main__':
    print("正在直接測試 system_configurator.py...")
    # 為了能在此處測試 Color，需要從 led_controller 匯入它
    # from .led_controller import Color # 已在頂部匯入
    
    led, sensor, emotion, lcd = initialize_systems()

    print("\n--- 初始化結果摘要 ---")
    print(f"LED Controller: {'成功' if led and led.strip and led.is_on else '失敗/未完全啟動'}")
    print(f"Sensor Handler: {'成功' if sensor and sensor.is_initialized and sensor.adc_channels else '失敗/未完全設定'}")
    print(f"Emotion Processor: {'已實例化' if emotion else '失敗'}")
    print(f"LCD Game Controller: {'成功' if lcd and lcd.disp else '失敗/未初始化顯示器'}")
    if lcd and hasattr(lcd, 'sensor_handler') and lcd.sensor_handler:
        print(f"  LCD Game Controller 已連結到 Sensor Handler: {'是' if lcd.sensor_handler == sensor else '否'}")
    else:
        print("  LCD Game Controller 未連結到 Sensor Handler 或 sensor_handler 屬性不存在")

    if led and led.strip and led.is_on:
        print("\n測試 LED：顯示紅色 1 秒")
        for i in range(led.strip.numPixels()):
            led.strip.setPixelColor(i, Color(255,0,0)) # 使用匯入的 Color
        led.strip.show()
        time.sleep(1)
        led.clear()
        print("LED 測試完畢。")

    if sensor and sensor.is_initialized and sensor.adc_channels:
        print("\n測試感測器 (峰值)：讀取所有通道峰值 1 秒")
        overall_voltage = sensor.get_max_voltage_from_all_channels(duration_sec=1)
        print(f"  所有通道最大電壓 (1s): {overall_voltage:.3f}V")
        
        print("\n測試感測器 (即時拍擊)：檢查 3 秒內是否有拍擊 (>0.1V)")
        start_t = time.time()
        detected_piezo_jump = False
        while time.time() - start_t < 3:
            if sensor.check_any_piezo_trigger(threshold=PIEZO_JUMP_THRESHOLD):
                print("  偵測到即時拍擊!")
                detected_piezo_jump = True
                break
            time.sleep(0.05)
        if not detected_piezo_jump:
            print("  3秒內未偵測到即時拍擊。")
        print("感測器測試呼叫完畢。")

    if lcd and lcd.disp:
        print("\nLCD Game Controller 已初始化，play_game() 可被呼叫。")
        # lcd.cleanup() # 通常在程式結束時呼叫

    print("\n清理 GPIO (如果在 initialize_systems 中設定了)...")
    GPIO.cleanup() # 因為 initialize_systems 設定了模式，這裡需要清理
    if pygame.get_init():
        pygame.quit()
    print("system_configurator.py 測試結束。") 