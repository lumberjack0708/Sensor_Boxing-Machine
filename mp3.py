import os
os.system("amixer cset numid=3 1")  # 強制切換到 3.5mm 耳機孔

import pygame
import random

os.environ["SDL_AUDIODRIVER"] = "alsa"  # 強制使用 ALSA

# 建立音樂清單
music_list = [
    "/home/pi/RandomGenerate/supercarloverdreamv2.mp3",
    "/home/pi/RandomGenerate/lovechacha.mp3"
]

# 隨機選取一首
mp3_path = random.choice(music_list)

# 檢查檔案是否存在
if not os.path.isfile(mp3_path):
    print(f"找不到檔案：{mp3_path}")
else:
    try:
        pygame.mixer.init()
        print("音效裝置初始化成功")
        os.system("amixer set Master 100%")  # 設定主音量為最大
    except Exception as e:
        print(f"音效裝置初始化失敗：{e}")
    pygame.mixer.music.load(mp3_path)
    pygame.mixer.music.set_volume(1)  # 設定 pygame 音量
    pygame.mixer.music.play()
    print(f"正在隨機播放：{os.path.basename(mp3_path)}")

    # 等待音樂播放結束
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
