import pygame
import os
import random

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
    pygame.mixer.init()
    pygame.mixer.music.load(mp3_path)
    pygame.mixer.music.set_volume(1)  # 設定音量
    pygame.mixer.music.play()
    print(f"正在隨機播放：{os.path.basename(mp3_path)}")

    # 等待音樂播放結束
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
