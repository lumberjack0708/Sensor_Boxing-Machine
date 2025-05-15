import pygame
import random
import sys

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
    print("請確保 'player.png', 'obstacle_image_short.png', 'obstacle_image_tall.png' 檔案存在於腳本目錄中。")
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
    pygame.display.flip()

    waiting_for_input = True
    while waiting_for_input:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return True # Restart
                if event.key == pygame.K_q:
                    return False # Quit
        clock.tick(FPS)


def reset_game():
    """重置遊戲狀態"""
    global player_y_velocity, is_jumping, obstacles, score, score_float, obstacle_speed, last_speed_increase_milestone, current_mileage, player_rect
    # player_y 的直接賦值不再需要，因為 player_rect.bottom 會被設定
    player_rect.x = player_x
    player_rect.bottom = ground_height # 重設玩家位置
    player_y_velocity = 0
    is_jumping = False
    obstacles = []
    score = 0
    score_float = 0.0
    obstacle_speed = 5
    last_speed_increase_milestone = 0
    current_mileage = INITIAL_MILEAGE
    obstacles.append(create_obstacle())


# 遊戲主迴圈
running = True
game_active = True
obstacle_timer = 0
# 初始 obstacle_spawn_time，後續會在遊戲中動態調整
obstacle_spawn_time = INITIAL_SPAWN_TIME_AVG 
obstacles.append(create_obstacle())

# 修改 game 函數以接受一個參數作為該次遊戲的起始里程
def game(starting_mileage_for_session: int = INITIAL_MILEAGE): # 使用 INITIAL_MILEAGE 作為預設值
    """遊戲主迴圈"""
    # current_mileage 需要是全域的，因為它會被 display_stats 和 game_over_screen 讀取，並在此處修改
    global running, game_active, player_rect, is_jumping, player_y_velocity, score, obstacle_speed, last_speed_increase_milestone,  obstacles, obstacle_timer, obstacle_spawn_time, score_float, current_mileage
    
    # 注意：當 game() 被呼叫時（例如從 if __name__ == "__main__":），
    # 全域的 score 應該是 0。reset_game() 會確保這一點。
    # 第一次計算 current_mileage 時，它將是 starting_mileage_for_session - 0。

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if game_active:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and not is_jumping:
                        is_jumping = True
                        player_y_velocity = jump_strength
            else: 
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        reset_game() # reset_game 會將 current_mileage 設回 INITIAL_MILEAGE
                        game_active = True
                    if event.key == pygame.K_q:
                        running = False

        if game_active:
            # --- 遊戲邏輯 ---
            # ... (玩家跳躍, 距離得分, 速度增加, 障礙物生成, 跳過障礙物得分等邏輯不變) ...
            # 玩家跳躍
            if is_jumping:
                player_y_velocity += player_gravity
                player_rect.y += player_y_velocity # 直接修改 player_rect.y
                if player_rect.bottom >= ground_height: # 檢查底部是否觸地
                    player_rect.bottom = ground_height
                    is_jumping = False
                    player_y_velocity = 0
            # player_rect.y 的賦值已在跳躍邏輯中處理

            # 根據移動距離增加分數
            score_float += obstacle_speed / PIXELS_PER_POINT
            score = int(score_float)

            # 每10分增加速度 (基於新的計分方式)
            current_milestone_val = score // 10 # 使用不同的變數名以避免與全域 current_mileage 混淆
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
                    # 根據儲存的數字高度鍵來決定分數
                    if obs_data['height'] == 30: 
                        points_to_add = random.randint(5, 7)
                    elif obs_data['height'] == 45: 
                        points_to_add = random.randint(8, 10)
                    
                    score += points_to_add
                    obs_data['scored'] = True

                if obs_data['rect'].right > 0:
                    new_obstacles.append(obs_data)
            obstacles = new_obstacles

            # 碰撞檢測
            for obs_data in obstacles:
                if player_rect.colliderect(obs_data['rect']):
                    game_active = False 
            
            if game_active: # 再次檢查 game_active，因為碰撞可能已將其設為 False
                # 使用傳入的 starting_mileage_for_session 來計算當前的里程
                current_mileage = starting_mileage_for_session - score
                if current_mileage <= 0:
                    current_mileage = 0 # 確保里程數不顯示為負
                    game_active = False

            # --- 繪圖 ---
            screen.fill(WHITE)
            pygame.draw.rect(screen, GROUND_COLOR, (0, ground_height, SCREEN_WIDTH, SCREEN_HEIGHT - ground_height))
            
            # 繪製玩家圖片
            screen.blit(player_image, player_rect)

            # 繪製障礙物圖片
            for obs_data in obstacles:
                screen.blit(obs_data['image'], obs_data['rect'])

            display_stats()

        else: 
            if game_over_screen():
                reset_game()
                game_active = True
            else:
                running = False

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    # 現在您可以傳遞一個值給 game() 來設定該次遊戲的初始里程
    # 例如，以 500 的里程開始遊戲
    game(500)
    # 如果不傳遞參數，則會使用預設值 INITIAL_MILEAGE (350)
    # game()