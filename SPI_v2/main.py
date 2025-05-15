import time
import RPi.GPIO as GPIO
import pygame # Pygame 的 init/quit 需要在此層級管理
import signal
import sys # 用於 sys.exit()
# import board # 由 system_configurator 內部處理

# 從新模組匯入初始化函式和控制器類別 (儘管類別主要由 configurator 內部使用)
from system_configurator import initialize_systems, cleanup_systems, BUTTON_PIN, MUSIC_DEFAULT_VOLUME, MUSIC_GAME_VOLUME # 直接從設定檔取用 BUTTON_PIN 和音量常數
# from .led_controller import LedController # 已由 system_configurator 處理
# from .sensor_handler import SensorHandler # 已由 system_configurator 處理
# from .emotion_calculator import EmotionCalculator # 已由 system_configurator 處理
# from .game_on_lcd import LcdGameController # 已由 system_configurator 處理

from game_interactions import get_player_emotion_index # 匯入新的互動邏輯函式
from led_controller import LedController, Color # 修正此處的匯入

# --- 全域常數 ---
GAME_START_THRESHOLD = 10 # 啟動遊戲所需的情緒指數閾值

# ===== 主程式 =====
def main():
    """應用程式主入口點，處理主事件迴圈和遊戲狀態。"""
    print("\n=== 互動式解壓小遊戲 v2.1 (HDMI 版本) ===")
    print("正在啟動系統...")
    
    initialized_systems = None # 確保在 finally 中可用
    try:
        initialized_systems = initialize_systems()
        
        if not initialized_systems.get('success', False):
            print("嚴重錯誤: 系統關鍵部分初始化失敗。請檢查上方日誌。程式即將退出。")
            # 即使初始化失敗，也嘗試清理已部分初始化的資源
            if initialized_systems: # 確保字典本身存在
                cleanup_systems(initialized_systems)
            else: # 如果 initialize_systems 本身就崩了
                GPIO.cleanup() # 嘗試基本的 GPIO 清理
                if pygame.get_init(): pygame.quit()
            sys.exit(1)
        
        led_controller = initialized_systems.get('led_controller')
        sensor_handler = initialized_systems.get('sensor_handler')
        emotion_calculator = initialized_systems.get('emotion_calculator')
        hdmi_game_engine = initialized_systems.get('hdmi_game_engine')
        spi_lcd_display = initialized_systems.get('spi_lcd_display')
        music_player = initialized_systems.get('music_player')

        # 檢查核心模組是否都已成功初始化
        if not all([led_controller, sensor_handler, emotion_calculator, hdmi_game_engine, spi_lcd_display]):
            print("警告: 部分核心模組未能成功初始化，程式功能可能受限或無法執行。")
            # 根據需求決定是否在此處退出，目前選擇繼續，讓使用者看到錯誤訊息

        # 設定信號處理以優雅地處理 Ctrl+C
        running_main_loop = [True] # 使用列表以便在回調函數中修改
        def signal_handler_main(sig, frame):
            print("\n接收到中斷信號 (Ctrl+C)，正在準備退出主迴圈...")
            running_main_loop[0] = False
            # 嘗試主動發送一個 Pygame QUIT 事件，以便遊戲引擎迴圈能更快響應
            if pygame.get_init():
                try:
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
                except Exception as e:
                    print(f"在信號處理器中發送 pygame.QUIT 事件時發生錯誤: {e}")
        
        signal.signal(signal.SIGINT, signal_handler_main)
        signal.signal(signal.SIGTERM, signal_handler_main)
        
        waiting_for_button = True
        rainbow_j_offset = 0
        
        if music_player:
            music_player.play_random_music(category='default', loop=True)
        
        if spi_lcd_display:
            spi_lcd_display.show_standby_message("按鈕啟動")
        else:
            print("SPI LCD 未初始化，無法顯示待機訊息。")

        if hdmi_game_engine: # 新增：程式啟動時更新 HDMI 待機畫面
            hdmi_game_engine.show_hdmi_standby_screen(title="互動解壓挑戰", line1="按按鈕開始")

        if led_controller:
            led_controller.reset_rainbow_animation_state() # 確保彩虹從頭開始

        print("\n系統已就緒，等待按鈕按下以開始測量情緒...")
        
        while running_main_loop[0]:
            if waiting_for_button:
                if led_controller:
                    led_controller.update_rainbow_cycle_frame(rainbow_j_offset) # 主迴圈控制彩虹動畫幀更新
                    rainbow_j_offset = (rainbow_j_offset + 1) % (256*5) # 調整彩虹長度和速度
                time.sleep(0.02) # 稍微降低待機時的更新頻率
                
                if GPIO.input(BUTTON_PIN) == GPIO.HIGH:
                    print("\n按鈕已按下！")
                    waiting_for_button = False
                    
                    if led_controller: 
                        print("LED：按鈕按下，執行戲院追逐彩虹燈效...")
                        # 執行一個短暫的、炫彩的阻塞動畫作為測量提示
                        led_controller.theater_chase_rainbow(wait_ms=40, iterations=1, cycle_limit=20) 
                    
                    if music_player: music_player.fade_out(300)
                    if spi_lcd_display: spi_lcd_display.display_message(["測量情緒中..."], font_size='large')
                    if hdmi_game_engine: 
                        hdmi_game_engine.show_measuring_emotion_screen(duration=3)

                    emotion_index = 0
                    if sensor_handler and emotion_calculator:
                        emotion_index = get_player_emotion_index(
                            sensor_handler, emotion_calculator, duration_sec=3
                        )
                    else:
                        print("錯誤: 感測器或情緒計算器未初始化，無法獲取情緒指數。")
                        emotion_index = GAME_START_THRESHOLD + 1 # 模擬一個值以便測試流程

                    if emotion_index >= GAME_START_THRESHOLD:
                        print(f"測量完成！負面情緒指數: {emotion_index}")
                        if spi_lcd_display: spi_lcd_display.display_message([f"情緒值: {emotion_index}", "準備開始遊戲"], font_size='medium')
                        
                        if music_player: 
                            music_player.set_volume(MUSIC_GAME_VOLUME) 
                            music_player.switch_to_category('game', loop=True)
                        
                        game_results = None
                        if hdmi_game_engine:
                            print("啟動 HDMI 遊戲...")
                            game_results = hdmi_game_engine.run_game(emotion_index)
                            print(f"HDMI 遊戲結束。結果: {game_results}")
                        else:
                            print("錯誤: HDMI 遊戲引擎未初始化，無法啟動遊戲。")
                            # 模擬遊戲結果以便流程繼續
                            game_results = {'score': 0, 'final_mileage': emotion_index, 'reason': 'engine_fail'}

                        # 遊戲結束後的 LED 和音樂處理
                        if music_player:
                            music_player.set_volume(MUSIC_DEFAULT_VOLUME) 
                            music_player.switch_to_category('game_over', loop=False)
                        
                        if led_controller and game_results: # 遊戲結束燈效
                            reason = game_results.get('reason')
                            print(f"LED：遊戲結束，原因: {reason}")
                            if reason == "mileage_zero": # 成功
                                led_controller.color_wipe(Color(0, 255, 0), wait_ms=25) # 綠色擦拭
                                time.sleep(0.5)
                                led_controller.rainbow_effect(wait_ms=20, iterations=1) # 短暫勝利彩虹
                            elif reason == "collision": # 失敗
                                led_controller.color_wipe(Color(255, 0, 0), wait_ms=25) # 紅色擦拭
                                time.sleep(0.5)
                                led_controller.show_flash_pattern(Color(150,0,0), times=4, duration_on=0.15, duration_off=0.1)
                            else: # 其他退出情況 (例如按Q)
                                led_controller.color_wipe(Color(0,0,0), wait_ms=10) # 快速熄滅
                            # time.sleep(1.5) # 等待顯示效果後，HdmiGameEngine的clear會執行
                        
                        if spi_lcd_display and game_results:
                            spi_lcd_display.display_game_results(
                                game_results.get('score', 0),
                                game_results.get('final_mileage', 0),
                                game_results.get('reason', 'unknown')
                            )
                        
                        # 等待一段時間讓玩家看 LCD 結果，同時播放結束音樂
                        if music_player and music_player.is_music_playing():
                            wait_start_time = time.time()
                            while music_player.is_music_playing() and (time.time() - wait_start_time < 5):
                                time.sleep(0.1) # 等待音樂播放或最多5秒
                            music_player.stop() # 確保音樂停了
                        elif not music_player:
                            time.sleep(3) # 如果沒有音樂播放器，固定等待3秒
                        
                        if music_player: 
                            # music_player.stop() # 確保音樂停了 (switch_to_category 內部會先 stop)
                            music_player.set_volume(MUSIC_DEFAULT_VOLUME) # 確保切回預設音樂時是預設音量
                            music_player.switch_to_category('default', loop=True)

                    else:
                        print(f"負面情緒指數 ({emotion_index}) 過低 (未達到 {GAME_START_THRESHOLD})。請再試一次。")
                        if spi_lcd_display: spi_lcd_display.display_message(["情緒不足", "請再試一次"], font_size='large')
                        time.sleep(2)
                        if music_player: 
                            music_player.set_volume(MUSIC_DEFAULT_VOLUME) # 確保是預設音量
                            music_player.switch_to_category('default', loop=True)
                    
                    if spi_lcd_display: spi_lcd_display.show_standby_message("按鈕啟動")
                    if hdmi_game_engine: # 新增：遊戲結束後更新 HDMI 待機畫面
                        hdmi_game_engine.show_hdmi_standby_screen(title="準備就緒", line1="按按鈕重新開始")
                    if led_controller: 
                        led_controller.reset_rainbow_animation_state() # 為下一次待機準備彩虹
                    
                    waiting_for_button = True
                    print("\n系統已返回待機狀態，等待按鈕按下...")
            
            # 處理 Pygame 事件以保持視窗回應 (主要由 HdmiGameEngine 內部處理，但以防萬一)
            # 也確保在遊戲引擎未運行時，主迴圈仍能處理 QUIT 事件
            if pygame.get_init():
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        print("Pygame QUIT 事件觸發主迴圈退出。")
                        running_main_loop[0] = False
            
            if not running_main_loop[0]: # 如果信號或事件要求退出
                break
            
            # 在非等待按鈕且非 LED 更新的快速迴圈中，稍作延遲
            if not waiting_for_button:
                 time.sleep(0.01)

    except KeyboardInterrupt:
        print("\n主程式被使用者中斷 (Ctrl+C)。")
    except SystemExit as e:
        print(f"程式因 sys.exit({e.code}) 退出。") # 處理 sys.exit
    except Exception as e:
        print(f"主程式運行過程中發生未預期錯誤: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n主迴圈結束或發生錯誤/退出，正在執行最終清理...")
        
        # 首先清理各個模組的資源
        # 確保 initialized_systems 存在並且是一個字典
        if 'initialized_systems' in locals() and isinstance(initialized_systems, dict):
            cleanup_systems(initialized_systems) 
        else:
            print("警告: initialized_systems 未正確初始化，可能部分模組資源未清理。")

        # 然後執行全域性的 GPIO 清理
        # 只有在 GPIO 模式被設定過的情況下才執行 cleanup
        gpio_mode_was_set = False
        try:
            # GPIO.getmode() 只有在模式設定後才返回值，否則可能引發異常或返回 None 取決於 RPi.GPIO 版本
            # 更安全的方式是使用一個旗標，或者依賴 RPi.GPIO 在未設定模式時 cleanup() 的行為 (通常是安全的)
            # 但為了明確，我們可以假設 initialize_systems 設定了模式
            # 或者在 initialize_systems 成功後設定一個全域旗標
            if GPIO.getmode() is not None: # 檢查模式是否已設定
                 gpio_mode_was_set = True
        except RuntimeError: # GPIO.getmode() might raise RuntimeError if no mode set
            pass # gpio_mode_was_set 保持 False
        except Exception: # 其他可能的異常
            pass # gpio_mode_was_set 保持 False

        if gpio_mode_was_set:
            try:
                GPIO.cleanup()
                print("GPIO (來自 main.py) 已清理。")
            except Exception as e:
                print(f"GPIO 清理時發生錯誤: {e}")
        else:
            print("GPIO 模式似乎未曾設定，跳過 GPIO 清理。")

        # 最後執行 Pygame 的退出
        if pygame.get_init():
            try:
                pygame.quit()
                print("Pygame (來自 main.py) 已退出。")
            except Exception as e:
                print(f"Pygame 退出時發生錯誤: {e}")
        else:
            print("Pygame 未初始化，跳過 Pygame 退出。")
            
        print("程式完全結束。")

if __name__ == "__main__":
    main()

