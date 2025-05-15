import time
import RPi.GPIO as GPIO
# import board # 由 system_configurator 內部處理

# 從新模組匯入初始化函式和控制器類別 (儘管類別主要由 configurator 內部使用)
from .system_configurator import initialize_systems, BTN_PIN # 直接從設定檔取用 BTN_PIN
# from .led_controller import LedController # 已由 system_configurator 處理
# from .sensor_handler import SensorHandler # 已由 system_configurator 處理
# from .emotion_calculator import EmotionCalculator # 已由 system_configurator 處理
# from .game_on_lcd import LcdGameController # 已由 system_configurator 處理

import pygame # Pygame 的 quit 需要在 main 的 finally 中處理

from .game_interactions import get_player_emotion_index # 匯入新的互動邏輯函式

# --- 主要的硬體/模組實例將從 initialize_systems() 獲取 ---
led_strip_controller = None
sensor_input_handler = None
emotion_processor = None
lcd_game_manager = None

# --- 全域常數 (如果還有 main.py 特有的) ---
GAME_START_THRESHOLD = 10 # 啟動遊戲所需的情緒指數閾值

if __name__ == "__main__":
    # 初始化所有系統和模組
    # initialize_systems() 會回傳 (led_controller, sensor_handler, emotion_calc, lcd_game_ctrl)
    try:
        led_strip_controller, sensor_input_handler, emotion_processor, lcd_game_manager = initialize_systems()
    except Exception as e:
        print(f"系統初始化過程中發生嚴重錯誤: {e}")
        print("程式無法繼續執行。")
        # 確保在退出前進行可能的清理
        if 'led_strip_controller' in locals() and led_strip_controller and hasattr(led_strip_controller, 'is_on') and led_strip_controller.is_on:
            led_strip_controller.clear()
        GPIO.cleanup() # 即使設定失敗，也嘗試清理 GPIO
        if pygame.get_init(): pygame.quit()
        exit(1)

    # 檢查各模組初始化狀態
    # 注意：initialize_systems 內部已有日誌，這裡的檢查是為了 main 的流程控制
    led_ok = led_strip_controller and hasattr(led_strip_controller, 'strip') and hasattr(led_strip_controller, 'is_on') and led_strip_controller.is_on
    # sensor_ok 的判斷現在更依賴 sensor_handler 是否為 None 及其 is_initialized 和 adc_channels 狀態
    sensor_ok = sensor_input_handler is not None and \
                  hasattr(sensor_input_handler, 'is_initialized') and sensor_input_handler.is_initialized and \
                  hasattr(sensor_input_handler, 'adc_channels') and bool(sensor_input_handler.adc_channels)
    lcd_game_ok = lcd_game_manager and hasattr(lcd_game_manager, 'disp') and lcd_game_manager.disp
    emotion_calc_ok = emotion_processor is not None

    if not led_ok: print("主程式警告: LED 控制器似乎未完全運作。")
    if not sensor_ok: print("主程式警告: 感測器處理器似乎未完全運作或通道未設定。")
    if not lcd_game_ok: print("主程式警告: LCD 遊戲控制器似乎未完全運作。")
    if not emotion_calc_ok: print("主程式警告: 情緒計算器未實例化。")

    print("\n系統準備就緒。按下按鈕開始遊戲。")
    if led_ok: print("待機模式：LED 彩虹燈效。")

    try:
        while True:
            if led_ok: led_strip_controller.update_rainbow_cycle_frame()

            if GPIO.input(BTN_PIN) == GPIO.HIGH:
                print("\n按鈕已按下！")
                
                if led_ok:
                    led_strip_controller.clear()
                    time.sleep(0.1)
                    led_strip_controller.show_flash_pattern(times=2, duration_on=0.05, duration_off=0.05)
                
                # 使用 game_interactions 模組的函式來獲取情緒指數
                negative_emotion_index = get_player_emotion_index(
                    sensor_handler_instance=sensor_input_handler, 
                    emotion_calculator_instance=emotion_processor,
                    sensor_is_ready=sensor_ok, 
                    emotion_calc_is_ready=emotion_calc_ok,
                    duration_sec=3
                )
                # get_player_emotion_index 內部已有詳細的 print 輸出

                if negative_emotion_index <= GAME_START_THRESHOLD:
                    print(f"負面情緒指數 ({negative_emotion_index}) 過低 (未超過 {GAME_START_THRESHOLD})。請再試一次。")
                    # TODO: 可以在 LCD上顯示"情緒不足"的提示 (如果 lcd_game_ok)
                    print("回到待機模式...")
                    while GPIO.input(BTN_PIN) == GPIO.HIGH: time.sleep(0.05)
                    if led_ok: led_strip_controller.reset_rainbow_animation_state()
                    continue

                if lcd_game_ok:
                    print(f"啟動 LCD 遊戲，負面情緒指數: {negative_emotion_index}")
                    lcd_game_manager.play_game(negative_emotion_index)
                    print("LCD 遊戲結束。")
                else:
                    print("錯誤: LCD 遊戲控制器未就緒。遊戲無法啟動。")

                print("回到待機模式...")
                while GPIO.input(BTN_PIN) == GPIO.HIGH: time.sleep(0.05)
                print("按鈕已釋放。")
                if led_ok: led_strip_controller.reset_rainbow_animation_state()

            time.sleep(0.02)

    except KeyboardInterrupt:
        print("\n程式被使用者中斷。")
    except Exception as e:
        print(f"\n主迴圈發生未預期錯誤: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n正在清理資源...")
        if lcd_game_manager: 
            print("清理 LCD 遊戲控制器...")
            lcd_game_manager.cleanup()
        if led_strip_controller and hasattr(led_strip_controller, 'is_on') and led_strip_controller.is_on:
            print("關閉 LED...")
            led_strip_controller.clear()
        
        # GPIO.cleanup() 應該在主程式的最後執行，確保所有 GPIO 使用都已結束
        # initialize_systems() 內部設定了 GPIO.setmode 和 GPIO.setup(BTN_PIN)
        # 所以 main.py 的 finally 負責 cleanup 是合理的。
        print("清理 GPIO...")
        GPIO.cleanup()
        
        if pygame.get_init():
            print("關閉 Pygame...")
            pygame.quit()
        print("清理完畢，程式結束。")

