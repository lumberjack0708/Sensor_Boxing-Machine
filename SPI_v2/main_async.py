import asyncio
import time
import RPi.GPIO as GPIO
import pygame
import signal
import sys

from system_configurator import initialize_systems, cleanup_systems, BUTTON_PIN, MUSIC_DEFAULT_VOLUME, MUSIC_GAME_VOLUME
from game_interactions import get_player_emotion_index
from led_controller import LedController, Color

GAME_START_THRESHOLD = 10

async def async_sleep(secs):
    await asyncio.sleep(secs)

def setup_signal_handlers(loop, running_main_loop):
    def signal_handler(sig, frame):
        print(f"\n接收到中斷信號 ({sig})，正在準備退出主迴圈...")
        running_main_loop[0] = False
        if pygame.get_init():
            try:
                pygame.event.post(pygame.event.Event(pygame.QUIT))
            except Exception as e:
                print(f"在信號處理器中發送 pygame.QUIT 事件時發生錯誤: {e}")
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda s=sig: signal_handler(s, None))
        except NotImplementedError:
            signal.signal(sig, signal_handler)

async def main():
    print("\n=== 互動式解壓小遊戲 v2.1 (HDMI 版本, async) ===")
    print("正在啟動系統...")
    initialized_systems = None
    running_main_loop = [True]
    loop = asyncio.get_event_loop()
    setup_signal_handlers(loop, running_main_loop)
    try:
        initialized_systems = initialize_systems()
        if not initialized_systems.get('success', False):
            print("嚴重錯誤: 系統關鍵部分初始化失敗。請檢查上方日誌。程式即將退出。")
            if initialized_systems:
                cleanup_systems(initialized_systems)
            else:
                GPIO.cleanup()
                if pygame.get_init(): pygame.quit()
            sys.exit(1)
        led_controller = initialized_systems.get('led_controller')
        sensor_handler = initialized_systems.get('sensor_handler')
        emotion_calculator = initialized_systems.get('emotion_calculator')
        hdmi_game_engine = initialized_systems.get('hdmi_game_engine')
        spi_lcd_display = initialized_systems.get('spi_lcd_display')
        music_player = initialized_systems.get('music_player')
        if not all([led_controller, sensor_handler, emotion_calculator, hdmi_game_engine, spi_lcd_display]):
            print("警告: 部分核心模組未能成功初始化，程式功能可能受限或無法執行。")
        waiting_for_button = True
        rainbow_j_offset = 0
        if spi_lcd_display:
            spi_lcd_display.show_standby_message("按鈕啟動")
        else:
            print("SPI LCD 未初始化，無法顯示待機訊息。")
        if hdmi_game_engine:
            hdmi_game_engine.show_hdmi_standby_screen(title="互動解壓挑戰", line1="按按鈕開始")
        if led_controller:
            led_controller.reset_rainbow_animation_state()
            led_controller.static_color(Color(0, 25, 75))  # 啟動時靜態藍色
        print("\n系統已就緒，等待按鈕按下以開始測量情緒...")
        while running_main_loop[0]:
            if waiting_for_button:
                if led_controller:
                    led_controller.update_rainbow_cycle_frame(rainbow_j_offset)
                    rainbow_j_offset = (rainbow_j_offset + 1) % (256*5)
                await async_sleep(0.02)
                if GPIO.input(BUTTON_PIN) == GPIO.HIGH:
                    print("\n按鈕已按下！")
                    waiting_for_button = False
                    if led_controller:
                        print("LED：按鈕按下，執行戲院追逐彩虹燈效...")
                        await loop.run_in_executor(None, led_controller.theater_chase_rainbow, 40, 1, 20)
                    if spi_lcd_display: spi_lcd_display.display_message(["測量情緒中..."], font_size='large')
                    if hdmi_game_engine:
                        hdmi_game_engine.show_measuring_emotion_screen(duration=3)
                    emotion_index = 0
                    if sensor_handler and emotion_calculator:
                        emotion_index = await loop.run_in_executor(None, get_player_emotion_index, sensor_handler, emotion_calculator, 3)
                    else:
                        print("錯誤: 感測器或情緒計算器未初始化，無法獲取情緒指數。")
                        emotion_index = GAME_START_THRESHOLD + 1
                    if emotion_index >= GAME_START_THRESHOLD:
                        print(f"測量完成！負面情緒指數: {emotion_index}")
                        if spi_lcd_display: spi_lcd_display.display_message([f"情緒值: {emotion_index}", "準備開始遊戲"], font_size='medium')
                        game_results = None
                        if hdmi_game_engine:
                            print("啟動 HDMI 遊戲...")
                            game_results = hdmi_game_engine.run_game(emotion_index)
                            print(f"HDMI 遊戲結束。結果: {game_results}")
                        else:
                            print("錯誤: HDMI 遊戲引擎未初始化，無法啟動遊戲。")
                            game_results = {'score': 0, 'final_mileage': emotion_index, 'reason': 'engine_fail'}
                        if led_controller and game_results:
                            reason = game_results.get('reason')
                            print(f"LED：遊戲結束，原因: {reason}")
                            if reason == "mileage_zero":
                                await loop.run_in_executor(None, led_controller.color_wipe, Color(0, 255, 0), 25)
                                await async_sleep(0.5)
                                await loop.run_in_executor(None, led_controller.rainbow_effect, 20, 1)
                            elif reason == "collision":
                                await loop.run_in_executor(None, led_controller.color_wipe, Color(255, 0, 0), 25)
                                await async_sleep(0.5)
                                await loop.run_in_executor(None, led_controller.show_flash_pattern, Color(150,0,0), 4, 0.15, 0.1)
                            else:
                                await loop.run_in_executor(None, led_controller.color_wipe, Color(0,0,0), 10)
                        if spi_lcd_display and game_results:
                            spi_lcd_display.display_game_results(
                                game_results.get('score', 0),
                                game_results.get('final_mileage', 0),
                                game_results.get('reason', 'unknown')
                            )
                        await async_sleep(3)
                        if spi_lcd_display: spi_lcd_display.show_standby_message("按鈕啟動")
                        if hdmi_game_engine:
                            hdmi_game_engine.show_hdmi_standby_screen(title="準備就緒", line1="按按鈕重新開始")
                        if led_controller:
                            led_controller.reset_rainbow_animation_state()
                    else:
                        print(f"負面情緒指數 ({emotion_index}) 過低 (未達到 {GAME_START_THRESHOLD})。請再試一次。")
                        if spi_lcd_display: spi_lcd_display.display_message(["情緒不足", "請再試一次"], font_size='large')
                        await async_sleep(2)
                    waiting_for_button = True
                    print("\n系統已返回待機狀態，等待按鈕按下...")
            if pygame.get_init():
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        print("Pygame QUIT 事件觸發主迴圈退出。")
                        running_main_loop[0] = False
            if not running_main_loop[0]:
                break
            if not waiting_for_button:
                await async_sleep(0.01)
    except KeyboardInterrupt:
        print("\n主程式被使用者中斷 (Ctrl+C)。")
    except SystemExit as e:
        print(f"程式因 sys.exit({e.code}) 退出。")
    except Exception as e:
        print(f"主程式運行過程中發生未預期錯誤: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n主迴圈結束或發生錯誤/退出，正在執行最終清理...")
        if 'initialized_systems' in locals() and isinstance(initialized_systems, dict):
            cleanup_systems(initialized_systems)
        else:
            print("警告: initialized_systems 未正確初始化，可能部分模組資源未清理。")
        gpio_mode_was_set = False
        try:
            if GPIO.getmode() is not None:
                gpio_mode_was_set = True
        except RuntimeError:
            pass
        except Exception:
            pass
        if gpio_mode_was_set:
            try:
                GPIO.cleanup()
                print("GPIO (來自 main_async.py) 已清理。")
            except Exception as e:
                print(f"GPIO 清理時發生錯誤: {e}")
        else:
            print("GPIO 模式似乎未曾設定，跳過 GPIO 清理。")
        if pygame.get_init():
            try:
                pygame.quit()
                print("Pygame (來自 main_async.py) 已退出。")
            except Exception as e:
                print(f"Pygame 退出時發生錯誤: {e}")
        else:
            print("Pygame 未初始化，跳過 Pygame 退出。")
        # 確保 LED 關閉
        try:
            if 'led_controller' in locals() and led_controller:
                led_controller.clear()
                print("LED (來自 main_async.py) 已清除。")
        except Exception as e:
            print(f"LED 清除時發生錯誤: {e}")
        print("程式完全結束。")

if __name__ == "__main__":
    asyncio.run(main())
