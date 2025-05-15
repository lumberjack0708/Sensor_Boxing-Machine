import digitalio
import board
from PIL import Image, ImageDraw, ImageFont # Pillow for image manipulation
from adafruit_rgb_display import ili9341
import pygame
import random
import sys
import os
import RPi.GPIO as GPIO

# --- ILI9341 Display Setup ---
cs_pin = digitalio.DigitalInOut(board.CE0)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = digitalio.DigitalInOut(board.D24) # 確保此腳位正確
backlight = digitalio.DigitalInOut(board.D27) # 可選，用於背光控制
backlight.switch_to_output()
backlight.value = True

BAUDRATE = 48000000  # 嘗試 24000000, 48000000, 或 64000000
spi = board.SPI()

disp = ili9341.ILI9341(
    spi,
    rotation=270,  # 根據您的螢幕方向調整 (常見為 90 或 270 for landscape)
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
)

# 獲取螢幕尺寸 (Pygame Surface 和遊戲邏輯將使用這些尺寸)
if disp.rotation % 180 == 90: # Landscape
    GAME_SCREEN_WIDTH = disp.height
    GAME_SCREEN_HEIGHT = disp.width
else: # Portrait
    GAME_SCREEN_WIDTH = disp.width
    GAME_SCREEN_HEIGHT = disp.height

print(f"ILI9341 Display configured for: {GAME_SCREEN_WIDTH}x{GAME_SCREEN_HEIGHT}")

# --- Pygame Initialization ---
pygame.init()
pygame.display.set_mode((1, 1), pygame.HIDDEN)  # 不彈出視窗
game_canvas = pygame.Surface((GAME_SCREEN_WIDTH, GAME_SCREEN_HEIGHT))
clock = pygame.time.Clock()  # 全域定義

# --- Game Logic Adapted from jump.py ---

# 顏色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GROUND_COLOR = (140, 120, 100)

# 遊戲參數 (已為小螢幕調整)
FPS = 30 # 降低 FPS 以適應 SPI 傳輸速度
player_gravity = 1
jump_strength = -16
player_y_velocity = 0
ground_height = GAME_SCREEN_HEIGHT - int(GAME_SCREEN_HEIGHT * 0.12) # 地面高度約為螢幕高度的 88%
obstacle_speed_initial = 240  # supplemental explanation: 初始速度為原本的30倍
obstacle_speed = obstacle_speed_initial
score = 0
score_float = 0.0
PIXELS_PER_POINT = 1800.0  # supplemental explanation: 分數增長速度為原本的1/30
last_speed_increase_milestone = 0

INITIAL_MILEAGE = 350 # 預設初始總里程數
current_mileage = INITIAL_MILEAGE

# 障礙物生成頻率 (已調整)
INITIAL_SPAWN_TIME_AVG = 180 # 影格數
MIN_SPAWN_TIME_AVG = 80
SCORE_TO_REACH_MIN_SPAWN_TIME = 1000 # 調整達到最小生成時間所需分數
SPAWN_TIME_RANDOM_RANGE = 40
ABSOLUTE_MIN_SPAWN_TIME = 45 # 絕對最小生成時間 (影格數)

# 載入並縮放圖片
try:
    # 取得目前檔案所在資料夾的絕對路徑
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    player_image_path = os.path.join(BASE_DIR, 'player.png')
    obstacle_image_path = os.path.join(BASE_DIR, 'obstacle.png')

    player_image = pygame.image.load(player_image_path).convert_alpha()
    obstacle_image = pygame.image.load(obstacle_image_path).convert_alpha()

    PLAYER_WIDTH = int(GAME_SCREEN_WIDTH * 0.075)
    PLAYER_HEIGHT = int(GAME_SCREEN_HEIGHT * 0.13)
    player_image = pygame.transform.scale(player_image, (PLAYER_WIDTH, PLAYER_HEIGHT))

    OBSTACLE_WIDTH = int(GAME_SCREEN_WIDTH * 0.03)
    OBSTACLE_HEIGHT_SHORT = int(GAME_SCREEN_HEIGHT * 0.1)
    OBSTACLE_HEIGHT_TALL = int(GAME_SCREEN_HEIGHT * 0.15)
    obstacle_images = {
        30: pygame.transform.scale(obstacle_image, (OBSTACLE_WIDTH, OBSTACLE_HEIGHT_SHORT)),
        45: pygame.transform.scale(obstacle_image, (OBSTACLE_WIDTH, OBSTACLE_HEIGHT_TALL)),
    }

except pygame.error as e:
    print(f"警告：無法載入或縮放圖片 '{e}'。將使用預留位置矩形。")
    # 創建預留位置圖片
    PLAYER_WIDTH = max(18, int(GAME_SCREEN_WIDTH * 0.075))
    PLAYER_HEIGHT = max(22, int(GAME_SCREEN_HEIGHT * 0.13))
    player_image = pygame.Surface((PLAYER_WIDTH, PLAYER_HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(player_image, (0, 200, 0), player_image.get_rect()) # 綠色

    obstacle_height_options_scaled = {30: 15, 45: 22} # 預設縮放後高度
    OBSTACLE_BASE_WIDTH_SCALED = 10
    obstacle_images_scaled = {}
    for original_h, scaled_h_val in obstacle_height_options_scaled.items():
        surf = pygame.Surface((OBSTACLE_BASE_WIDTH_SCALED, scaled_h_val), pygame.SRCALPHA)
        pygame.draw.rect(surf, (200, 0, 0), surf.get_rect()) # 紅色
        obstacle_images_scaled[original_h] = surf


# 嘗試自動尋找可用中文字型
common_ch_fonts = [
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/arphic/ukai.ttc",
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf"
]
ch_font_path = None
for f in common_ch_fonts:
    if os.path.exists(f):
        ch_font_path = f
        break

if ch_font_path:
    font = pygame.font.Font(ch_font_path, int(GAME_SCREEN_HEIGHT / 22))
    game_over_font = pygame.font.Font(ch_font_path, int(GAME_SCREEN_HEIGHT / 12))
else:
    font = pygame.font.Font(None, int(GAME_SCREEN_HEIGHT / 22))
    game_over_font = pygame.font.Font(None, int(GAME_SCREEN_HEIGHT / 12))
    print("警告：找不到中文字型，將使用預設字型，中文可能無法正常顯示。")

# 嘗試載入阿拉伯數字字型（如 DejaVu Sans Mono）
common_num_fonts = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
]
for f_name in common_num_fonts:
    if os.path.exists(f_name):
        num_font_path = f_name
        break

# 建立字型物件
if ch_font_path:
    ch_font = pygame.font.Font(ch_font_path, int(GAME_SCREEN_HEIGHT / 22))
else:
    ch_font = pygame.font.Font(None, int(GAME_SCREEN_HEIGHT / 22) + 2)

if num_font_path:
    num_font = pygame.font.Font(num_font_path, int(GAME_SCREEN_HEIGHT / 22))
else:
    num_font = pygame.font.Font(None, int(GAME_SCREEN_HEIGHT / 22) + 2)

# 玩家
player_x_start_offset = int(GAME_SCREEN_WIDTH * 0.1)
player_rect = player_image.get_rect()
player_rect.x = player_x_start_offset
player_rect.bottom = ground_height
is_jumping = False

# 障礙物列表
obstacles = []
# 使用原始高度作為鍵，但對應縮放後的圖片和高度值
# obstacle_height_options from jump.py was [30, 45]
obstacle_original_height_keys = [30, 45]

# GPIO4 (腳位7) 按鈕
BTN_PIN = 4  # GPIO4（腳位7）
GPIO.setmode(GPIO.BCM)
GPIO.setup(BTN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

def create_obstacle_adapted():
    """創建新的障礙物 (適配版)"""
    original_height_key = random.choice(obstacle_original_height_keys) # 選擇原始高度鍵 (30 或 45)
    current_obstacle_image = obstacle_images[original_height_key] # 使用縮放後的圖片
    
    obstacle_rect = current_obstacle_image.get_rect()
    obstacle_rect.x = GAME_SCREEN_WIDTH
    obstacle_rect.bottom = ground_height
    
    # "height_key" 儲存原始高度用於計分邏輯, "image" 是縮放後的圖片
    return {"rect": obstacle_rect, "height_key": original_height_key, "scored": False, "image": current_obstacle_image}

def display_stats_adapted(surface_to_draw_on):
    """在指定的 surface 上顯示分數和剩餘里程"""
    # 分數直接用中文字型
    score_text = ch_font.render(f"價值:", True, BLACK)
    score_num = num_font.render(str(score), True, BLACK)
    surface_to_draw_on.blit(score_text, (5, int(GAME_SCREEN_HEIGHT*0.08)))
    surface_to_draw_on.blit(score_num, (5 + score_text.get_width(), int(GAME_SCREEN_HEIGHT*0.08)))

    # 情緒
    emo_text = ch_font.render("情緒:", True, BLACK)
    emo_num = num_font.render(str(current_mileage), True, BLACK)
    surface_to_draw_on.blit(emo_text, (5, int(GAME_SCREEN_HEIGHT*0.02)))
    surface_to_draw_on.blit(emo_num, (5 + emo_text.get_width(), int(GAME_SCREEN_HEIGHT*0.02)))

def game_over_screen_adapted(surface_to_draw_on, display_controller):
    """在指定的 surface 上顯示遊戲結束畫面，並更新到 ILI9341"""
    surface_to_draw_on.fill(WHITE)
    
    line1_text_str = "成功離開城市!" if current_mileage <= 0 else "遊戲結束"
    game_over_text_l1 = game_over_font.render(line1_text_str, True, BLACK)
    # line2_text_str = "傷心城市" # 如果需要第二行
    # game_over_text_l2 = game_over_font.render(line2_text_str, True, BLACK)

    residual_emotions_text = font.render(f"剩餘情緒: {current_mileage}", True, BLACK)
    final_score_val_text = font.render(f"獲得價值: {score}", True, BLACK)
    restart_text = font.render("R-重玩 Q-離開", True, (80,80,80))

    text_y_start = GAME_SCREEN_HEIGHT // 4
    line_h = game_over_text_l1.get_height()
    
    surface_to_draw_on.blit(game_over_text_l1, (GAME_SCREEN_WIDTH // 2 - game_over_text_l1.get_width() // 2, text_y_start))
    # surface_to_draw_on.blit(game_over_text_l2, (GAME_SCREEN_WIDTH // 2 - game_over_text_l2.get_width() // 2, text_y_start + line_h + 2))
    text_y_start += line_h * 2
    surface_to_draw_on.blit(residual_emotions_text, (GAME_SCREEN_WIDTH // 2 - residual_emotions_text.get_width() // 2, text_y_start))
    text_y_start += residual_emotions_text.get_height() + int(line_h * 0.5)
    surface_to_draw_on.blit(final_score_val_text, (GAME_SCREEN_WIDTH // 2 - final_score_val_text.get_width() // 2, text_y_start))
    text_y_start += final_score_val_text.get_height() + line_h
    surface_to_draw_on.blit(restart_text, (GAME_SCREEN_WIDTH // 2 - restart_text.get_width() // 2, text_y_start))

    # 更新到 ILI9341 螢幕
    pil_img_data = pygame.image.tostring(surface_to_draw_on, 'RGB')
    pil_img = Image.frombytes('RGB', (GAME_SCREEN_WIDTH, GAME_SCREEN_HEIGHT), pil_img_data)
    display_controller.image(pil_img)

    waiting = True
    while waiting:
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evt.type == pygame.KEYDOWN:
                if evt.key == pygame.K_r:
                    return True # Restart
                if evt.key == pygame.K_q:
                    return False # Quit
        clock.tick(FPS) # 保持時脈

def reset_game_adapted(initial_mileage_val):
    """重置遊戲狀態 (適配版)"""
    global player_y_velocity, is_jumping, obstacles, score, score_float, obstacle_speed
    global last_speed_increase_milestone, current_mileage, player_rect
    global obstacle_timer, obstacle_spawn_time

    player_rect.x = player_x_start_offset
    player_rect.bottom = ground_height
    player_y_velocity = 0
    is_jumping = False
    obstacles = []
    score = 0
    score_float = 0.0
    obstacle_speed = obstacle_speed_initial
    last_speed_increase_milestone = 0
    current_mileage = initial_mileage_val # 使用傳入的初始里程
    
    obstacle_timer = 0
    obstacle_spawn_time = INITIAL_SPAWN_TIME_AVG
    if not obstacles: # 確保遊戲開始時至少有一個障礙物
        obstacles.append(create_obstacle_adapted())


# --- 主遊戲迴圈函式 (適配版) ---
def run_adapted_game(display_ctrl, game_session_mileage):
    global running, game_active, player_rect, is_jumping, player_y_velocity, score, obstacle_speed
    global last_speed_increase_milestone, obstacles, obstacle_timer, obstacle_spawn_time, score_float, current_mileage

    # 創建一個 Pygame Surface 用於離屏繪圖
    game_canvas = pygame.Surface((GAME_SCREEN_WIDTH, GAME_SCREEN_HEIGHT))

    reset_game_adapted(game_session_mileage) # 使用傳入的里程初始化遊戲

    # --- 新增：待命狀態 ---
    waiting_to_start = True
    running = True
    game_active = False
    last_btn_state = GPIO.LOW

    while running:
        if waiting_to_start:
            # 畫靜止畫面
            game_canvas.fill(WHITE)
            pygame.draw.rect(game_canvas, GROUND_COLOR, (0, ground_height, GAME_SCREEN_WIDTH, GAME_SCREEN_HEIGHT - ground_height))
            game_canvas.blit(player_image, player_rect)
            for obs_data in obstacles:
                game_canvas.blit(obs_data['image'], obs_data['rect'])
            display_stats_adapted(game_canvas)
            # 顯示提示文字
            tip_font = pygame.font.Font(None, max(16, int(GAME_SCREEN_HEIGHT/18)))
            tip_text = tip_font.render("請按下按鈕開始遊戲", True, (80,80,80))
            game_canvas.blit(tip_text, (GAME_SCREEN_WIDTH//2 - tip_text.get_width()//2, GAME_SCREEN_HEIGHT//2))
            # 更新到 ILI9341
            pil_image_data = pygame.image.tostring(game_canvas, 'RGB')
            pil_img = Image.frombytes('RGB', (GAME_SCREEN_WIDTH, GAME_SCREEN_HEIGHT), pil_image_data)
            display_ctrl.image(pil_img)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                        waiting_to_start = False
                        game_active = True
            # 新增：偵測 GPIO4 按鈕
            btn_state = GPIO.input(BTN_PIN)
            if btn_state == GPIO.HIGH and last_btn_state == GPIO.LOW:
                waiting_to_start = False
                game_active = True
            clock.tick(FPS)
            continue

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if game_active:
                if event.type == pygame.KEYDOWN:
                    if (event.key == pygame.K_SPACE or event.key == pygame.K_UP) and not is_jumping:
                        is_jumping = True
                        player_y_velocity = jump_strength
                # 這裡不要再偵測 GPIO 按鈕
                # game_over_screen_adapted 內部處理 R/Q

        if game_active:
            # 新增：每一幀都偵測 GPIO4 按鈕跳躍
            btn_state = GPIO.input(BTN_PIN)
            if btn_state == GPIO.HIGH and not is_jumping:
                is_jumping = True
                player_y_velocity = jump_strength
                print("跳躍")  # supplemental explanation: 按下按鈕時印出"跳躍"
            # --- 遊戲邏輯 (與 jump.py 類似，但參數已調整) ---
            if is_jumping:
                player_y_velocity += player_gravity
                player_rect.y += player_y_velocity
                if player_rect.bottom >= ground_height:
                    player_rect.bottom = ground_height
                    is_jumping = False
                    player_y_velocity = 0

            score_float += obstacle_speed / PIXELS_PER_POINT
            score = int(score_float)

            current_milestone_val = score // 10
            if current_milestone_val > last_speed_increase_milestone:
                obstacle_speed += 1.0
                last_speed_increase_milestone = current_milestone_val

            obstacle_timer += 1
            if obstacle_timer > obstacle_spawn_time:
                obstacles.append(create_obstacle_adapted())
                obstacle_timer = 0
                progress = min(1.0, score / SCORE_TO_REACH_MIN_SPAWN_TIME)
                current_avg_spawn = INITIAL_SPAWN_TIME_AVG - progress * (INITIAL_SPAWN_TIME_AVG - MIN_SPAWN_TIME_AVG)
                spawn_time_lower_candidate = int(current_avg_spawn - SPAWN_TIME_RANDOM_RANGE / 2)
                spawn_time_upper_candidate = int(current_avg_spawn + SPAWN_TIME_RANDOM_RANGE / 2)
                actual_lower_bound = max(ABSOLUTE_MIN_SPAWN_TIME, spawn_time_lower_candidate)
                actual_upper_bound = max(actual_lower_bound + 1, spawn_time_upper_candidate)
                obstacle_spawn_time = random.randint(actual_lower_bound, actual_upper_bound)

            new_obstacles_list = []
            for obs_data in obstacles:
                obs_data['rect'].x -= obstacle_speed
                if not obs_data['scored'] and obs_data['rect'].right < player_rect.left:
                    points = 0
                    if obs_data['height_key'] == 30:
                        points = random.randint(5, 7)
                    elif obs_data['height_key'] == 45:
                        points = random.randint(8, 10)
                    score += points
                    obs_data['scored'] = True
                if obs_data['rect'].right > 0:
                    new_obstacles_list.append(obs_data)
            obstacles = new_obstacles_list

            for obs_data in obstacles:
                if player_rect.colliderect(obs_data['rect']):
                    game_active = False
            
            if game_active:
                current_mileage = game_session_mileage - score
                if current_mileage <= 0:
                    current_mileage = 0
                    game_active = False

            # --- 在 game_canvas 上繪圖 ---
            game_canvas.fill(WHITE)
            pygame.draw.rect(game_canvas, GROUND_COLOR, (0, ground_height, GAME_SCREEN_WIDTH, GAME_SCREEN_HEIGHT - ground_height))
            game_canvas.blit(player_image, player_rect)
            for obs_data in obstacles:
                game_canvas.blit(obs_data['image'], obs_data['rect'])
            display_stats_adapted(game_canvas)

            # 將 Pygame Surface 轉成 PIL Image，顯示到 ILI9341
            pil_image_data = pygame.image.tostring(game_canvas, 'RGB')
            pil_img = Image.frombytes('RGB', (GAME_SCREEN_WIDTH, GAME_SCREEN_HEIGHT), pil_image_data)
            display_ctrl.image(pil_img)

        else: # game_active is False (遊戲結束)
            if game_over_screen_adapted(game_canvas, display_ctrl): # True 表示重新開始
                reset_game_adapted(game_session_mileage) # 重置時使用相同的初始里程
                game_active = True
            else: # False 表示退出
                running = False
        
        clock.tick(FPS)

    pygame.quit()

    # 在程式結束時
    GPIO.cleanup()


# --- 腳本執行 ---
if __name__ == "__main__":
    try:
        # 您可以從其他地方（例如 test.py 中的 Translate 邏輯）獲取初始里程
        # 這裡我們直接使用 jump.py 中的預設值或一個自訂值
        session_starting_mileage = INITIAL_MILEAGE # 或者您可以設定為例如 500
        
        print(f"在 ILI9341 ({GAME_SCREEN_WIDTH}x{GAME_SCREEN_HEIGHT}) 上開始遊戲，初始情緒: {session_starting_mileage}")
        run_adapted_game(disp, session_starting_mileage)
    
    except KeyboardInterrupt:
        print("遊戲被使用者中斷。")
    except Exception as e:
        print(f"執行時發生未預期錯誤: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'backlight' in globals() and backlight:
            backlight.value = False # 關閉背光
        pygame.quit()
        print("遊戲結束。")
