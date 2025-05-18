"""
負責初始化所有硬體元件和主要控制模組的設定檔。
"""
import RPi.GPIO as GPIO
import board
import pygame 
import time 
import os

# 從專案的各個模組匯入類別
from led_controller import LedController, Color
from sensor_handler import SensorHandler
from emotion_calculator import EmotionCalculator
# from game_on_lcd import LcdGameController # 此行已移除，因為 game_on_lcd.py 已被取代
from music_player import MusicPlayer
from hdmi_game_engine import HdmiGameEngine
from spi_lcd_display import SpiLcdDisplay

# --- 硬體和模組設定常數 ---
# LED 燈條設定
LED_PIN        = 18
LED_COUNT      = 60
LED_FREQ_HZ    = 800000
LED_DMA        = 10
LED_BRIGHTNESS = 25
LED_INVERT     = False
LED_CHANNEL    = 0

# GPIO 按鈕設定
BUTTON_PIN = 4

# EmotionCalculator 參數設定
EMOTION_VOLTAGE_THRESHOLD = 0.05 
MAX_EMOTION_INDEX = 500      

# SensorHandler / ADS1115 設定
ADC_ADDRESS = 0x48
PIEZO_CHANNELS = [0, 1, 2, 3] 
ADC_GAIN = 2/3                
PIEZO_JUMP_THRESHOLD = 0.1    

# SPI LCD Display (ILI9341) 腳位設定
LCD_CS_PIN = board.CE0
LCD_DC_PIN = board.D25
LCD_RESET_PIN = board.D24
LCD_BACKLIGHT_PIN = board.D27 
LCD_BAUDRATE = 48000000
LCD_ROTATION = 0

# HDMI Game Engine 設定
HDMI_SCREEN_WIDTH = 800 
HDMI_SCREEN_HEIGHT = 600 
PLAYER_IMAGE_PATH = os.path.join(os.path.dirname(__file__), 'player.png')
OBSTACLE_IMAGE_PATH = os.path.join(os.path.dirname(__file__), 'obstacle.png')

# 音樂播放設定
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
MUSIC_DEFAULT_VOLUME = 0.5
MUSIC_GAME_VOLUME = 0.8     # 遊戲進行時的音量 (0.0-1.0)

def initialize_systems():
    """
    初始化所有硬體驅動和邏輯模組。
    回傳一個包含所有已初始化系統元件的字典。
    """
    print("系統設定：正在初始化所有硬體和模組...")
    initialized_components = {
        'success': True, 
        'led_controller': None,
        'sensor_handler': None,
        'emotion_calculator': None,
        'hdmi_game_engine': None,
        'spi_lcd_display': None,
        'music_player': None
    }

    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        print(f"按鈕 GPIO 初始化設定完成 (GPIO{BUTTON_PIN} 使用 BCM 模式)。")

        try:
            led_controller = LedController(
                led_pin=LED_PIN, led_count=LED_COUNT, freq_hz=LED_FREQ_HZ, dma=LED_DMA,
                invert=LED_INVERT, brightness=LED_BRIGHTNESS, channel=LED_CHANNEL
            )
            led_controller.begin()
            if led_controller.is_on:
                initialized_components['led_controller'] = led_controller
                print("LED 控制器初始化成功。")
            else:
                print("警告 (系統設定): LED 控制器 begin() 未成功，但程式繼續。")
        except Exception as e:
            print(f"錯誤 (系統設定): LED 控制器初始化失敗: {e}")
            initialized_components['success'] = False

        sensor_handler_instance = None
        try:
            sensor_handler_instance = SensorHandler()
            if sensor_handler_instance.initialize_ads1115(): 
                if sensor_handler_instance.setup_adc_channels(channel_pins_config=None):
                    initialized_components['sensor_handler'] = sensor_handler_instance
                    print("感測器處理器 (ADS1115) 初始化成功。")
                else:
                    print("警告 (系統設定): ADC 通道設定失敗。感測器可能無法正常讀取。")
            else:
                print("警告 (系統設定): ADS1115 初始化失敗。感測器讀取功能將不可用。")
        except Exception as e:
            print(f"錯誤 (系統設定): 感測器處理器初始化失敗: {e}")
            initialized_components['success'] = False

        try:
            emotion_calc = EmotionCalculator(
                min_voltage_threshold=EMOTION_VOLTAGE_THRESHOLD,
                max_emotion_value=MAX_EMOTION_INDEX
            )
            initialized_components['emotion_calculator'] = emotion_calc
            print(f"情緒計算器已初始化 (閾值={EMOTION_VOLTAGE_THRESHOLD}V, 上限={MAX_EMOTION_INDEX})。")
        except Exception as e:
            print(f"錯誤 (系統設定): 情緒計算器初始化失敗: {e}")
            initialized_components['success'] = False

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
        except Exception as e:
            print(f"錯誤 (系統設定): SPI LCD 顯示控制器初始化失敗: {e}")

        try:
            hdmi_game = HdmiGameEngine(
                screen_width=HDMI_SCREEN_WIDTH,
                screen_height=HDMI_SCREEN_HEIGHT,
                player_img_path=PLAYER_IMAGE_PATH,
                obstacle_img_path=OBSTACLE_IMAGE_PATH,
                sensor_handler_instance=initialized_components.get('sensor_handler'), 
                piezo_jump_threshold=PIEZO_JUMP_THRESHOLD,
                led_controller_instance=initialized_components.get('led_controller')
            )
            if hdmi_game.is_initialized:
                initialized_components['hdmi_game_engine'] = hdmi_game
                print("HDMI 遊戲引擎初始化成功。")
            else:
                print("警告 (系統設定): HDMI 遊戲引擎初始化未完全成功。")
                initialized_components['success'] = False 
        except Exception as e:
            print(f"錯誤 (系統設定): HDMI 遊戲引擎初始化失敗: {e}")
            initialized_components['success'] = False

        try:
            music_player = MusicPlayer(
                music_directories=MUSIC_DIRECTORIES,
                default_volume=MUSIC_DEFAULT_VOLUME
            )
            initialized_components['music_player'] = music_player
            print("音樂播放器已初始化。")
        except Exception as e:
            print(f"警告 (系統設定): 音樂播放器初始化失敗: {e}")

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
    清理所有初始化的系統資源，除了 GPIO 本身和 Pygame 的退出。
    GPIO.cleanup() 和 pygame.quit() 應由主應用程式在最外層管理。
    參數:
        initialized_components (dict): 由 initialize_systems 返回的元件字典。
    """
    print("正在清理系統模組資源...")
    
    if initialized_components.get('hdmi_game_engine'):
        initialized_components['hdmi_game_engine'].cleanup()
        print("HDMI 遊戲引擎已清理。")

    if initialized_components.get('spi_lcd_display'):
        initialized_components['spi_lcd_display'].cleanup()
        print("SPI LCD 顯示器已清理。")

    if initialized_components.get('led_controller'):
        led_controller = initialized_components['led_controller']
        if led_controller and hasattr(led_controller, 'clear'): # 確保物件存在且有 clear 方法
            led_controller.clear()
            print("LED 控制器已清理。")
    
    if initialized_components.get('music_player'):
        music_player = initialized_components['music_player']
        if music_player and hasattr(music_player, 'cleanup'): # 確保物件存在且有 cleanup 方法
            music_player.cleanup()
            print("音樂播放器已清理。")
    
    # GPIO.cleanup() 和 pygame.quit() 將由 main.py 的 finally 塊處理
    print("模組資源清理完成。GPIO 和 Pygame 將由主程式處理。")


if __name__ == '__main__':
    print("正在直接測試 system_configurator.py...")
    
    components = initialize_systems()

    print("\n--- 初始化結果摘要 ---")
    for key, value in components.items():
        if key == 'success':
            print(f"Overall Success: {value}")
        elif hasattr(value, 'is_initialized'):
            print(f"{key.replace('_', ' ').title()}: {'成功' if value.is_initialized else '失敗/未完全啟動'}")
        elif hasattr(value, 'is_on'): 
             print(f"{key.replace('_', ' ').title()}: {'成功' if value.is_on else '失敗/未完全啟動'}")
        elif value is not None:
            print(f"{key.replace('_', ' ').title()}: 已實例化 (但可能未完全成功, 請檢查詳細日誌)")
        else:
            print(f"{key.replace('_', ' ').title()}: 未能初始化 (None)")

    if components.get('led_controller'):
        print("\n測試 LED：顯示紅色 1 秒")
        components['led_controller'].show_flash_pattern(flash_color=Color(255,0,0), times=1, duration_on=1)
        components['led_controller'].clear()

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
        components['music_player'].play_random_music(category='default', loop=False)
        time.sleep(2)
        components['music_player'].stop()
    
    if components.get('hdmi_game_engine'):
        print("\nHDMI 遊戲引擎已初始化。可由 main.py 呼叫其 run_game() 方法。")

    print("\n準備清理資源...")
    cleanup_systems(components)
    
    # 因為 initialize_systems 內部執行了 GPIO.setmode 和 pygame.init (間接通過 HdmiGameEngine),
    # 所以在這個測試塊的末尾也需要它們的清理。
    if GPIO.getmode() is not None: # 檢查 GPIO 是否已被設定模式
        GPIO.cleanup()
        print("GPIO (來自 system_configurator.py 測試) 已清理。")
    if pygame.get_init():
        pygame.quit()
        print("Pygame (來自 system_configurator.py 測試) 已退出。")
    
    print("system_configurator.py 測試結束。") 