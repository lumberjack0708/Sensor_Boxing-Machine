import pygame
import random
import sys
import RPi.GPIO as GPIO # 新增：匯入 RPi.GPIO 函式庫

# 初始化 Pygame
pygame.init()

# 螢幕設定
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 300
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
# pygame.display.set_caption("小恐龍")

# 顏色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GROUND_COLOR = (140, 120, 100) # 地板顏色

# 遊戲參數
FPS = 60
clock = pygame.time.Clock()
player_gravity = 1
jump_strength = -16
player_y_velocity = 0
ground_height = SCREEN_HEIGHT - 50
obstacle_speed = 5
score = 0
score_float = 0.0 # 用於精確累積分數
PIXELS_PER_POINT = 60.0 # 每移動多少像素獲得1分 (可調整)
last_speed_increase_milestone = 0 # 用於追蹤上次速度增加時的分數里程碑

INITIAL_MILEAGE = 350 # 設定初始總里程數 (可調整)
current_mileage = INITIAL_MILEAGE # 目前剩餘里程數

# 障礙物生成頻率參數
INITIAL_SPAWN_TIME_AVG = 120
MIN_SPAWN_TIME_AVG = 50
SCORE_TO_REACH_MIN_SPAWN_TIME = 2000
SPAWN_TIME_RANDOM_RANGE = 30
ABSOLUTE_MIN_SPAWN_TIME = 30

# 載入圖片 (請確保圖片檔案存在於正確的路徑)
try:
    player_image = pygame.image.load('player.png').convert_alpha() # 替換 'player_image.png' 為您的玩家圖片檔案
    # 為不同高度的障礙物準備不同的圖片
    obstacle_image_short = pygame.image.load('obstacle.png').convert_alpha() # 替換為矮障礙物圖片
    obstacle_image_tall = pygame.image.load('obstacle.png').convert_alpha() # 替換為高障礙物圖片
    
    # 根據障礙物高度選項映射到對應的圖片
    # 假設 obstacle_height_options 中的第一個值對應矮圖片，第二個對應高圖片
    obstacle_images = {
        30: obstacle_image_short, # 假設 30 是矮障礙物的高度
        45: obstacle_image_tall   # 假設 45 是高障礙物的高度
    }
except pygame.error as e:
    print(f"無法載入圖片: {e}")
    print("請確保 'player.png', 'obstacle.png' 檔案存在於腳本目錄中。")
    # pygame.quit()
    # sys.exit()

# 字型
try:
    font = pygame.font.SysFont("Microsoft YaHei", 18)
    game_over_font = pygame.font.SysFont("Microsoft YaHei", 34)
except pygame.error:
    print("警告：指定的系統字型 'Microsoft YaHei' 未找到，將退回使用預設字型。中文可能無法正確顯示。")
    print("建議：請安裝 '微軟雅黑' 字型，或下載一個中文字型 .ttf 檔案並在程式碼中指定路徑。")
    font = pygame.font.Font(None, 36)
    game_over_font = pygame.font.Font(None, 72)


# 玩家 (小恐龍)
player_x = 50
player_rect = player_image.get_rect() # 從圖片獲取矩形
player_rect.x = player_x
player_rect.bottom = ground_height # 將玩家底部與地面對齊
is_jumping = False

# 障礙物列表
obstacles = []
obstacle_height_options = [30, 45] # 這些值現在將用於選擇圖片和計分邏輯

def create_obstacle():
    """創建新的障礙物"""
    obstacle_height_key = random.choice(obstacle_height_options) # 選擇一個高度鍵 (30 或 45)
    current_obstacle_image = obstacle_images[obstacle_height_key]
    
    obstacle_rect = current_obstacle_image.get_rect()
    obstacle_rect.x = SCREEN_WIDTH
    obstacle_rect.bottom = ground_height # 將障礙物底部與地面對齊
    
    # "height" 仍然儲存數字高度用於計分邏輯
    return {"rect": obstacle_rect, "height": obstacle_height_key, "scored": False, "image": current_obstacle_image}

def display_stats():
    """顯示分數和剩餘里程"""
    score_text = font.render(f"當前情緒價值: {score}", True, BLACK)
    screen.blit(score_text, (10, 40))
    mileage_text = font.render(f"剩餘負面情緒: {current_mileage}", True, BLACK)
    screen.blit(mileage_text, (10, 10))

def game_over_screen():
    """顯示遊戲結束畫面"""
    screen.fill(WHITE)
    game_over_text = game_over_font.render("你已成功離開令人傷心欲絕的城市", True, BLACK)
    residual_negative_emotions = font.render(f"剩餘負面情緒: {current_mileage}", True, BLACK)
    final_score_text = font.render(f"你獲得了: {score}情緒價值", True, BLACK)

    screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, SCREEN_HEIGHT // 3 - game_over_text.get_height() // 2))
    screen.blit(residual_negative_emotions, (SCREEN_WIDTH // 2 - residual_negative_emotions.get_width() // 2, SCREEN_HEIGHT // 2 - residual_negative_emotions.get_height() // 2))
    screen.blit(final_score_text, (SCREEN_WIDTH // 2 - final_score_text.get_width() // 2, SCREEN_HEIGHT * 2 // 3 - final_score_text.get_height() // 2))
    
    # 新增提示文字，告知使用者如何退出
    quit_instruction_text = font.render("按 Q 離開遊戲", True, BLACK)
    screen.blit(quit_instruction_text, (SCREEN_WIDTH // 2 - quit_instruction_text.get_width() // 2, SCREEN_HEIGHT * 5 // 6 - quit_instruction_text.get_height() // 2))
    
    pygame.display.flip()

    waiting_for_input = True
    while waiting_for_input:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "FORCE_QUIT" 
            if event.type == pygame.KEYDOWN:
                # 移除：按下 'R' 重新開始的邏輯
                # if event.key == pygame.K_r:
                #     return "RESTART" 
                if event.key == pygame.K_q:
                    return "QUIT"    
        clock.tick(FPS)

def reset_game():
    """重置遊戲狀態"""
    global player_y_velocity, is_jumping, obstacles, score, score_float, obstacle_speed, last_speed_increase_milestone, current_mileage, player_rect, game_active, obstacle_timer, obstacle_spawn_time
    
    player_rect.x = player_x
    player_rect.bottom = ground_height # 重設玩家位置
    player_y_velocity = 0
    is_jumping = False
    obstacles = []
    score = 0
    score_float = 0.0
    obstacle_speed = 5 # 重設回初始速度
    last_speed_increase_milestone = 0
    current_mileage = INITIAL_MILEAGE # 重設里程
    
    # 重設障礙物生成相關變數
    obstacle_timer = 0
    obstacle_spawn_time = INITIAL_SPAWN_TIME_AVG 
    obstacles.append(create_obstacle()) # 立即生成一個障礙物

    game_active = True # 將遊戲狀態設為活躍


# 遊戲主迴圈的全域變數初始化
running = True
game_active = True # 遊戲開始時是活躍的
obstacle_timer = 0
# 初始 obstacle_spawn_time，後續會在遊戲中動態調整
obstacle_spawn_time = INITIAL_SPAWN_TIME_AVG 
if 'player_image' in globals(): # 確保圖片已載入才創建第一個障礙物
    obstacles.append(create_obstacle())
else:
    print("錯誤：玩家圖片未載入，無法初始化第一個障礙物。遊戲可能無法正常開始。")


# 修改 game 函數以接受一個參數作為該次遊戲的起始里程
def game(starting_mileage_for_session: int = INITIAL_MILEAGE): # 使用 INITIAL_MILEAGE 作為預設值
    """遊戲主迴圈"""
    # current_mileage 需要是全域的，因為它會被 display_stats 和 game_over_screen 讀取，並在此處修改
    global running, game_active, player_rect, is_jumping, player_y_velocity, score, obstacle_speed, last_speed_increase_milestone,  obstacles, obstacle_timer, obstacle_spawn_time, score_float, current_mileage
    
    # 修改：GPIO 設定
    PIEZO_PINS = [4, 17, 27, 22] # 新增：定義四個壓電薄膜感測器的 GPIO 腳位 (BCM 模式)
                                 # 請根據您的實際接線修改這些腳位號碼

    gpio_ready = False # 在 try 區塊外初始化 gpio_ready
    # 提醒：RPi.GPIO 僅在 Raspberry Pi 上運作
    try:
        GPIO.setwarnings(False) # 忽略 GPIO 警告
        GPIO.setmode(GPIO.BCM)  # 使用 BCM 編號系統
        for pin in PIEZO_PINS: # 修改：為每個壓電薄膜感測器腳位進行設定
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # 設定為輸入，啟用上拉電阻
        gpio_ready = True
        print("GPIO pins for piezo sensors initialized successfully.") # 可選：成功初始化的確認訊息
    except Exception as e:
        print(f"GPIO 初始化失敗: {e}. GPIO 跳躍功能將不可用。")
        # gpio_ready 將保持 False

    # 遊戲開始時，根據傳入的參數設定里程
    current_mileage = starting_mileage_for_session
    # 重設分數等其他相關遊戲狀態，確保每次 game() 呼叫都是一個新的開始
    score = 0
    score_float = 0.0
    obstacle_speed = 5 
    last_speed_increase_milestone = 0
    player_rect.x = player_x
    player_rect.bottom = ground_height
    is_jumping = False
    player_y_velocity = 0
    obstacles = []
    obstacle_timer = 0
    obstacle_spawn_time = INITIAL_SPAWN_TIME_AVG
    if 'player_image' in globals():
        obstacles.append(create_obstacle())
    game_active = True


    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if game_active:
            # --- 遊戲邏輯 ---
            
            # 修改：壓電薄膜跳躍邏輯
            if gpio_ready and not is_jumping:
                jump_triggered_by_piezo = False
                for pin in PIEZO_PINS:
                    if GPIO.input(pin) == GPIO.LOW: # 假設壓電薄膜觸發時，對應的 GPIO 腳位為低電位
                        jump_triggered_by_piezo = True
                        break # 任何一個感測器觸發即可跳躍
                
                if jump_triggered_by_piezo:
                    is_jumping = True
                    player_y_velocity = jump_strength
            
            # 玩家跳躍
            if is_jumping:
                player_y_velocity += player_gravity
                player_rect.y += player_y_velocity 
                if player_rect.bottom >= ground_height: 
                    player_rect.bottom = ground_height
                    is_jumping = False
                    player_y_velocity = 0

            # 根據移動距離增加分數 (此處的分數增加邏輯與里程減少是分開的)
            # score_float += obstacle_speed / PIXELS_PER_POINT 
            # score = int(score_float)
            # 注意：原有的 score 增加邏輯是基於像素移動，現在改為成功躲避障礙物時增加

            # 每10分增加速度 (基於新的計分方式 - 躲避障礙物得分)
            current_milestone_val = score // 10 
            if current_milestone_val > last_speed_increase_milestone:
                obstacle_speed += 0.5
                last_speed_increase_milestone = current_milestone_val

            # 移動和生成障礙物
            obstacle_timer += 1
            if obstacle_timer > obstacle_spawn_time:
                obstacles.append(create_obstacle())
                obstacle_timer = 0
                
                progress = min(1.0, score / SCORE_TO_REACH_MIN_SPAWN_TIME)
                current_avg_spawn = INITIAL_SPAWN_TIME_AVG - progress * (INITIAL_SPAWN_TIME_AVG - MIN_SPAWN_TIME_AVG)
                
                spawn_time_lower_candidate = int(current_avg_spawn - SPAWN_TIME_RANDOM_RANGE / 2)
                spawn_time_upper_candidate = int(current_avg_spawn + SPAWN_TIME_RANDOM_RANGE / 2)

                actual_lower_bound = max(ABSOLUTE_MIN_SPAWN_TIME, spawn_time_lower_candidate)
                actual_upper_bound = max(actual_lower_bound + 1, spawn_time_upper_candidate) 
                
                obstacle_spawn_time = random.randint(actual_lower_bound, actual_upper_bound)

            new_obstacles = []
            for obs_data in obstacles:
                obs_data['rect'].x -= obstacle_speed

                if not obs_data['scored'] and obs_data['rect'].right < player_rect.left:
                    points_to_add = 0
                    if obs_data['height'] == 30: 
                        points_to_add = random.randint(5, 7)
                    elif obs_data['height'] == 45: 
                        points_to_add = random.randint(8, 10)
                    
                    score += points_to_add # 分數因成功躲避障礙物而增加
                    obs_data['scored'] = True

                if obs_data['rect'].right > 0:
                    new_obstacles.append(obs_data)
            obstacles = new_obstacles

            # 碰撞檢測
            for obs_data in obstacles:
                if player_rect.colliderect(obs_data['rect']):
                    game_active = False 
            
            if game_active: 
                # 里程根據分數減少 (情緒價值增加，負面情緒減少)
                current_mileage = starting_mileage_for_session - score 
                if current_mileage <= 0:
                    current_mileage = 0 
                    game_active = False # 負面情緒耗盡，遊戲結束

            # --- 繪圖 ---
            screen.fill(WHITE)
            pygame.draw.rect(screen, GROUND_COLOR, (0, ground_height, SCREEN_WIDTH, SCREEN_HEIGHT - ground_height))
            
            screen.blit(player_image, player_rect)

            for obs_data in obstacles:
                screen.blit(obs_data['image'], obs_data['rect'])

            display_stats()

        else: # if not game_active (遊戲結束時)
            action = game_over_screen() 
            # 因為 game_over_screen 不再回傳 "RESTART"，所以以下 if action == "RESTART" 分支不會被執行
            if action == "RESTART": 
                reset_game() 
                # game() 函式會從 game_over_screen 返回後結束，
                # 若要重新開始，需要在 if __name__ == "__main__": 區塊中重新呼叫 game()
                # 或者修改 reset_game() 和此處的邏輯以允許在 game() 內部循環
                # 但目前的設定是結束當前 game() 實例
            elif action == "QUIT" or action == "FORCE_QUIT":
                running = False 

        pygame.display.flip()
        clock.tick(FPS)

    if gpio_ready: 
        GPIO.cleanup() 
    # pygame.quit() # pygame.quit() 和 sys.exit() 應該在主程式完全結束時呼叫
    # sys.exit()    # 如果 game() 函式是主迴圈，則在此處呼叫是合適的

if __name__ == "__main__":
    # 遊戲可以多次執行，例如：
    # game(INITIAL_MILEAGE) # 第一次遊戲
    # print("遊戲結束，準備下一次遊戲...")
    # game(500) # 第二次遊戲，以不同里程開始

    # 或者只執行一次
    game(INITIAL_MILEAGE) # 使用預設的初始里程

    pygame.quit() # 確保在所有遊戲邏輯結束後退出 Pygame
    sys.exit()    # 退出程式
