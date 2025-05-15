import pygame
import os
import random
import time

class MusicPlayer:
    """音樂播放器模組，用於遊戲中的背景音樂播放控制。"""
    
    def __init__(self, music_directories=None, default_volume=0.5):
        """
        初始化音樂播放器。
        
        參數:
            music_directories (dict): 包含不同場景音樂的字典，格式為 {'default': [路徑列表], 'game': [路徑列表], ...}
            default_volume (float): 預設音量，範圍 0.0 到 1.0
        """
        # 初始化 pygame mixer
        if not pygame.mixer.get_init():
            pygame.mixer.init()
            print("已初始化 pygame mixer")
        
        # 設定預設音樂目錄和播放列表
        self.music_directories = music_directories or {
            'default': [
                "/home/pi/RandomGenerate/supercarloverdreamv2.mp3",
                "/home/pi/RandomGenerate/lovechacha.mp3"
            ],
            # 可以依需求添加其他類別的音樂，例如：
            'game': [
                "/home/pi/RandomGenerate/supercarloverdreamv2.mp3",
                "/home/pi/RandomGenerate/lovechacha.mp3"
            ],
            'game_over': [
                "/home/pi/RandomGenerate/supercarloverdreamv2.mp3"
            ]
        }
        
        # 檢查音樂檔案是否存在
        for category, paths in self.music_directories.items():
            valid_paths = []
            for path in paths:
                if os.path.isfile(path):
                    valid_paths.append(path)
                else:
                    print(f"警告: 找不到音樂檔案 '{path}'")
            self.music_directories[category] = valid_paths
        
        # 目前播放的音樂類別和檔案路徑
        self.current_category = None
        self.current_music_path = None
        
        # 設定音量
        self.set_volume(default_volume)
        
        # 播放狀態
        self.is_playing = False
        
        print("音樂播放器初始化完成")
    
    def set_volume(self, volume):
        """
        設定音樂播放音量。
        
        參數:
            volume (float): 音量值，範圍 0.0 到 1.0
        """
        # 確保音量在有效範圍內
        volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(volume)
        print(f"音樂音量設定為: {volume}")
    
    def play_random_music(self, category='default', loop=True):
        """
        從指定類別中隨機選擇一首音樂並播放。
        
        參數:
            category (str): 音樂類別名稱，對應 music_directories 的鍵
            loop (bool): 是否循環播放
        
        返回:
            bool: 是否成功開始播放
        """
        if category not in self.music_directories or not self.music_directories[category]:
            print(f"警告: 類別 '{category}' 中沒有可用的音樂檔案")
            return False
        
        # 隨機選擇一首音樂
        music_path = random.choice(self.music_directories[category])
        
        return self.play_music(music_path, category, loop)
    
    def play_music(self, music_path, category=None, loop=True):
        """
        播放指定路徑的音樂檔案。
        
        參數:
            music_path (str): 音樂檔案路徑
            category (str): 音樂類別名稱 (僅用於記錄)
            loop (bool): 是否循環播放
        
        返回:
            bool: 是否成功開始播放
        """
        if not os.path.isfile(music_path):
            print(f"錯誤: 找不到音樂檔案 '{music_path}'")
            return False
        
        try:
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.play(-1 if loop else 0)  # -1 表示無限循環
            
            self.current_music_path = music_path
            self.current_category = category
            self.is_playing = True
            
            print(f"正在播放: {os.path.basename(music_path)}")
            return True
        except Exception as e:
            print(f"播放音樂時發生錯誤: {e}")
            return False
    
    def stop(self):
        """停止播放音樂。"""
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
            self.is_playing = False
            print("已停止播放音樂")
    
    def pause(self):
        """暫停音樂播放。"""
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
            self.is_playing = False
            print("已暫停音樂播放")
    
    def unpause(self):
        """恢復暫停的音樂播放。"""
        pygame.mixer.music.unpause()
        self.is_playing = pygame.mixer.music.get_busy()
        if self.is_playing:
            print("已恢復音樂播放")
    
    def fade_out(self, time_ms=500):
        """
        淡出並停止音樂播放。
        
        參數:
            time_ms (int): 淡出時間(毫秒)
        """
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.fadeout(time_ms)
            self.is_playing = False
            print(f"音樂在 {time_ms}ms 內淡出")
    
    def is_music_playing(self):
        """
        檢查音樂是否正在播放。
        
        返回:
            bool: 音樂是否正在播放
        """
        return pygame.mixer.music.get_busy()
    
    def switch_to_category(self, category, loop=True):
        """
        切換到指定類別的隨機音樂。
        
        參數:
            category (str): 音樂類別名稱
            loop (bool): 是否循環播放
        
        返回:
            bool: 是否成功切換
        """
        if self.current_category == category and self.is_playing:
            print(f"已經在播放 '{category}' 類別的音樂")
            return True
        
        # 停止當前音樂
        self.stop()
        
        # 播放新類別的音樂
        return self.play_random_music(category, loop)
    
    def cleanup(self):
        """清理資源，在程式結束時調用。"""
        self.stop()
        # pygame.mixer.quit() # 通常不需要在這裡退出，由主程式管理

# --- 測試代碼 (當直接運行此模組時執行) ---
if __name__ == "__main__":
    print("測試音樂播放器模組...")
    
    # 創建音樂播放器實例
    player = MusicPlayer()
    
    # 測試播放隨機音樂
    print("\n測試 1: 播放隨機音樂")
    player.play_random_music(loop=False)
    
    # 等待一段時間
    print("等待 3 秒...")
    time.sleep(3)
    
    # 測試暫停和恢復
    print("\n測試 2: 暫停和恢復")
    player.pause()
    print("等待 2 秒...")
    time.sleep(2)
    player.unpause()
    
    # 等待一段時間
    print("等待 3 秒...")
    time.sleep(3)
    
    # 測試切換音樂類別
    print("\n測試 3: 切換音樂類別")
    player.switch_to_category('game')
    
    # 等待一段時間
    print("等待 3 秒...")
    time.sleep(3)
    
    # 測試停止音樂
    print("\n測試 4: 停止音樂")
    player.stop()
    
    print("\n音樂播放器測試完成") 