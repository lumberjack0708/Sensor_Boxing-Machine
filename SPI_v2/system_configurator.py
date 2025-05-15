"""
負責初始化所有硬體元件和主要控制模組的設定檔。
"""
import RPi.GPIO as GPIO
import board # For LcdGameController and SensorHandler pin definitions
import pygame # For LcdGameController which inits pygame
import time # 為 if __name__ == '__main__' 中的測試新增
import os

# 從專案的各個模組匯入類別
from .led_controller import LedController, Color # 為 if __name__ == '__main__' 中的 LED 測試新增 Color
from .sensor_handler import SensorHandler
from .emotion_calculator import EmotionCalculator
from .game_on_lcd import LcdGameController
from .music_player import MusicPlayer  # 新增：導入音樂播放器模組
from .hdmi_game_engine import HdmiGameEngine  # 新增：導入 HDMI 遊戲引擎
from .spi_lcd_display import SpiLcdDisplay    # 新增：導入 SPI LCD 顯示控制器

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

# --- 音樂播放設定 ---
MUSIC_DIRECTORIES = {
    'default': [
        "/home/pi/RandomGenerate/supercarloverdreamv2.mp3",
        "/home/pi/RandomGenerate/lovechacha.mp3"
    ],
    'game': [
        "/home/pi/RandomGenerate/supercarloverdreamv2.mp3",
        "/home/pi/RandomGenerate/lovechacha.mp3"
    ],
    'game_over': [
        "/home/pi/RandomGenerate/supercarloverdreamv2.mp3"
    ]
}
MUSIC_DEFAULT_VOLUME = 0.5  # 預設音量 (0.0-1.0)

def initialize_systems():
    """
    初始化所有硬體驅動和邏輯模組。
    回傳一個包含所有已初始化系統元件的字典。
    """
    print("系統設定：正在初始化所有硬體和模組...")
    initialized_components = {
        'success': True, # 整體初始化成功標誌
        'led_controller': None,
        'sensor_handler': None,
        'emotion_calculator': None,
        'hdmi_game_engine': None,
        'spi_lcd_display': None,
        'music_player': None
    }

    try:
        # GPIO 初始化 (按鈕)
        GPIO.setmode(GPIO.BCM)
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

        # 音樂播放器初始化
        music_player = None
        try:
            music_player = MusicPlayer(
                music_directories=MUSIC_DIRECTORIES,
                default_volume=MUSIC_DEFAULT_VOLUME
            )
            print("音樂播放器已初始化")
        except Exception as e:
            print(f"警告: 音樂播放器初始化失敗: {e}")
            print("將繼續但無法使用背景音樂功能")
            # 不將整體成功狀態設為失敗，因為音樂功能不是核心功能

        # HDMI Game Engine 初始化
        # Pygame 的 init() 會在這裡被呼叫 (如果尚未初始化的話)
        try:
            hdmi_game = HdmiGameEngine(
                screen_width=800,
                screen_height=600,
                player_img_path=PLAYER_IMAGE_PATH,
                obstacle_img_path=OBSTACLE_IMAGE_PATH,
                sensor_handler_instance=sensor_handler, 
                piezo_jump_threshold=PIEZO_JUMP_THRESHOLD
            )
            if hdmi_game.is_initialized:
                initialized_components['hdmi_game_engine'] = hdmi_game
                print("HDMI 遊戲引擎初始化成功。")
            else:
                print("警告 (系統設定): HDMI 遊戲引擎初始化未完全成功。")
                initialized_components['success'] = False # 遊戲引擎是核心
        except Exception as e:
            print(f"錯誤 (系統設定): HDMI 遊戲引擎初始化失敗: {e}")
            initialized_components['success'] = False

        # SPI LCD Display 初始化
        try:
            spi_lcd = SpiLcdDisplay(
                cs_pin_board=LCD_CS_PIN,
                dc_pin_board=LCD_DC_PIN,
                rst_pin_board=LCD_RESET_PIN,
                backlight_pin_board=LCD_BACKLIGHT_PIN,
                baudrate=LCD_BAUDRATE,
                rotation=LCD_ROTATION
            )
            if spi_lcd.is_initialized:
                initialized_components['spi_lcd_display'] = spi_lcd
                print("SPI LCD 顯示控制器初始化成功。")
            else:
                print("警告 (系統設定): SPI LCD 顯示控制器初始化未完全成功。")
                # initialized_components['success'] = False
        except Exception as e:
            print(f"錯誤 (系統設定): SPI LCD 顯示控制器初始化失敗: {e}")
            # initialized_components['success'] = False

    except Exception as e:
        print(f"系統初始化過程中發生嚴重錯誤: {e}")
        initialized_components['success'] = False
    
    if initialized_components['success']:
        print("系統設定：所有指定模組初始化流程完畢 (部分可能為警告)。")
    else:
        print("系統設定：部分關鍵模組初始化失敗。請檢查日誌。")
        
    return initialized_components

def cleanup_systems(initialized_components):
    """
    清理所有初始化的系統資源。
    參數:
        initialized_components (dict): 由 initialize_systems 返回的元件字典。
    """
    print("正在清理系統資源...")
    
    if initialized_components.get('hdmi_game_engine'):
        initialized_components['hdmi_game_engine'].cleanup()
        print("HDMI 遊戲引擎已清理。")

    if initialized_components.get('spi_lcd_display'):
        initialized_components['spi_lcd_display'].cleanup()
        print("SPI LCD 顯示器已清理。")

    if initialized_components.get('led_controller'):
        initialized_components['led_controller'].clear()
        print("LED 控制器已清理。")
    
    if initialized_components.get('music_player'):
        initialized_components['music_player'].cleanup()
        print("音樂播放器已清理。")
    
    # GPIO cleanup 應在最後
    GPIO.cleanup()
    print("GPIO 已清理。")
    
    # Pygame quit 也應在最後，確保所有使用 pygame 的模組都已清理完畢
    if pygame.get_init():
        pygame.quit()
        print("Pygame 已退出。")
    
    print("所有系統資源已清理完成。")

# 測試函式 (如果直接執行此檔案)
if __name__ == '__main__':
    print("正在直接測試 system_configurator.py...")
    # 為了能在此處測試 Color，需要從 led_controller 匯入它
    # from .led_controller import Color # 已在頂部匯入
    
    components = initialize_systems()

    print("\n--- 初始化結果摘要 ---")
    for key, value in components.items():
        if key == 'success':
            print(f"Overall Success: {value}")
        elif hasattr(value, 'is_initialized'):
            print(f"{key.replace('_', ' ').title()}: {'成功' if value.is_initialized else '失敗/未完全啟動'}")
        elif hasattr(value, 'is_on'): # For LedController
             print(f"{key.replace('_', ' ').title()}: {'成功' if value.is_on else '失敗/未完全啟動'}")
        elif value is not None:
            print(f"{key.replace('_', ' ').title()}: 已實例化 (但可能未完全成功, 請檢查詳細日誌)")
        else:
            print(f"{key.replace('_', ' ').title()}: 未能初始化 (None)")

    if components.get('led_controller'):
        print("\n測試 LED：顯示紅色 1 秒")
        for i in range(components['led_controller'].strip.numPixels()):
            components['led_controller'].strip.setPixelColor(i, Color(255,0,0)) # 使用匯入的 Color
        components['led_controller'].strip.show()
        time.sleep(1)
        components['led_controller'].clear()
        print("LED 測試完畢。")

    if components.get('sensor_handler') and components['sensor_handler'].is_initialized and components['sensor_handler'].adc_channels:
        print("\n測試感測器 (峰值)：讀取所有通道峰值 1 秒")
        overall_voltage = components['sensor_handler'].get_max_voltage_from_all_channels(duration_sec=1)
        print(f"  所有通道最大電壓 (1s): {overall_voltage:.3f}V")
        
        print("\n測試感測器 (即時拍擊)：檢查 3 秒內是否有拍擊 (>0.1V)")
        start_t = time.time()
        detected_piezo_jump = False
        while time.time() - start_t < 3:
            if components['sensor_handler'].check_any_piezo_trigger(threshold=PIEZO_JUMP_THRESHOLD):
                print("  偵測到即時拍擊!")
                detected_piezo_jump = True
                break
            time.sleep(0.05)
        if not detected_piezo_jump:
            print("  3秒內未偵測到即時拍擊。")
        print("感測器測試呼叫完畢。")

    if components.get('spi_lcd_display'):
        print("\n測試 SPI LCD：顯示訊息")
        components['spi_lcd_display'].display_message(["Config Test", "LCD OK!"], font_size='medium')
        time.sleep(2)

    if components.get('music_player'):
        print("\n測試音樂播放器...")
        components['music_player'].play_random_music(loop=False)
        time.sleep(3)  # 播放 3 秒
        components['music_player'].stop()
        print("音樂播放器測試完成。")

    if components.get('hdmi_game_engine'):
        print("\nHDMI 遊戲引擎已初始化。可由 main.py 呼叫其 run_game() 方法。")

    print("\n準備清理資源...")
    cleanup_systems(components)
    
    print("system_configurator.py 測試結束。") 