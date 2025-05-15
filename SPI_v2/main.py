import time
import RPi.GPIO as GPIO
# import board # 由 system_configurator 內部處理

# 從新模組匯入初始化函式和控制器類別 (儘管類別主要由 configurator 內部使用)
from .system_configurator import initialize_systems, cleanup_systems, BUTTON_PIN # 直接從設定檔取用 BUTTON_PIN
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

# ===== 主程式 =====
def main():
    """應用程式主入口點，處理主事件迴圈和遊戲狀態。"""
    print("\n=== 互動式解壓小遊戲 v2.0 ===")
    print("正在啟動系統...")
    
    # 初始化所有系統元件
    try:
        initialized_systems = initialize_systems()
        
        # 檢查初始化是否成功
        if not initialized_systems['success']:
            print("警告: 系統部分初始化失敗，但將嘗試繼續執行...")
        
        # 從初始化結果中獲取各個模組實例
        led_controller = initialized_systems['led_controller']
        sensor_handler = initialized_systems['sensor_handler']
        emotion_calculator = initialized_systems['emotion_calculator']
        lcd_game_controller = initialized_systems['lcd_game_controller']
        music_player = initialized_systems['music_player']  # 獲取音樂播放器實例
        
        # 設定信號處理以優雅地處理 Ctrl+C
        def signal_handler(sig, frame):
            print("\n接收到中斷信號，正在清理資源...")
            running[0] = False  # 通知主迴圈退出
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # 使用列表儲存狀態，以便在回調函數中修改
        running = [True]
        waiting_for_button = [True]
        rainbow_j_offset = [0]
        
        # 啟動默認背景音樂
        if music_player:
            music_player.play_random_music(category='default', loop=True)
        
        print("\n系統已就緒，等待按鈕按下以開始測量情緒...")
        
        # 主事件迴圈
        try:
            while running[0]:
                current_time = time.time()
                
                # 待機時的彩虹動畫更新
                if waiting_for_button[0]:
                    led_controller.update_rainbow_cycle_frame(rainbow_j_offset[0])
                    rainbow_j_offset[0] = (rainbow_j_offset[0] + 1) % 256
                    time.sleep(0.05)  # 控制動畫速度
                
                # 檢查按鈕狀態
                if waiting_for_button[0] and GPIO.input(BUTTON_PIN) == GPIO.HIGH:
                    print("\n按鈕已按下，開始測量情緒...")
                    waiting_for_button[0] = False
                    
                    # 按鈕閃爍提示
                    led_controller.show_flash_pattern()
                    
                    # 暫停背景音樂
                    if music_player:
                        music_player.fade_out(500)  # 淡出當前音樂
                    
                    # 獲取情緒指數
                    emotion_index = get_player_emotion_index(
                        sensor_handler, 
                        emotion_calculator
                    )
                    
                    if emotion_index > 0:
                        print(f"\n測量完成！負面情緒指數: {emotion_index}")
                        
                        # 切換到遊戲音樂
                        if music_player:
                            music_player.switch_to_category('game', loop=True)
                        
                        # 啟動 LCD 遊戲
                        if lcd_game_controller:
                            print("\n啟動 LCD 遊戲...")
                            # 重設彩虹動畫狀態
                            led_controller.reset_rainbow_animation_state()
                            lcd_game_controller.play_game(emotion_index)
                            
                            # 遊戲結束後播放結束音樂
                            if music_player:
                                music_player.switch_to_category('game_over', loop=False)
                                time.sleep(2)  # 播放一小段結束音樂
                                music_player.switch_to_category('default', loop=True)  # 切回默認音樂
                        else:
                            print("錯誤: LCD 遊戲控制器未初始化，無法啟動遊戲")
                    else:
                        print("\n情緒指數太低，未達到啟動遊戲的標準。請再試一次。")
                        
                        # 切回默認音樂
                        if music_player:
                            music_player.switch_to_category('default', loop=True)
                    
                    # 返回等待按鈕狀態
                    waiting_for_button[0] = True
                    print("\n系統已返回待機狀態，等待按鈕按下...")
                
                # 處理 Pygame 事件以防止事件隊列積累
                if pygame.get_init():
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            running[0] = False
                
                # 在不是動畫更新的情況下添加短暫延遲以降低 CPU 使用率
                if not waiting_for_button[0]:
                    time.sleep(0.01)
        
        finally:
            print("\n主迴圈結束，正在清理資源...")
            # 清理資源
            cleanup_systems(initialized_systems)
            
            # 保證 Pygame 退出
            if pygame.get_init():
                pygame.quit()
    
    except Exception as e:
        print(f"程式運行過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n程式結束。")

if __name__ == "__main__":
    main()

