import pygame
import random
import sys
import os

# SensorHandler 類別的匯入是為了類型提示，實際的實例會由外部傳入
# from .sensor_handler import SensorHandler # 僅用於類型提示

class HdmiGameEngine:
    """在 HDMI 外接螢幕上運行 Pygame 小遊戲的引擎。"""

    # --- 遊戲參數 ---
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    GROUND_COLOR = (140, 120, 100)
    FPS = 60 # HDMI螢幕通常可以跑到更高FPS
    PLAYER_GRAVITY = 0.6
    JUMP_STRENGTH = -19
    OBSTACLE_SPEED_INITIAL = 5.0
    INITIAL_MILEAGE_DEFAULT = 350

    JUMP_BUFFER_DURATION_MS = 180 # 原為 120ms, 增加緩衝時間

    OBSTACLE_INITIAL_SPAWN_TIME_AVG = 120 # 幀
    OBSTACLE_MIN_SPAWN_TIME_AVG = 60
    OBSTACLE_SCORE_TO_REACH_MIN_SPAWN_TIME = 1000
    OBSTACLE_SPAWN_TIME_RANDOM_RANGE = 30
    OBSTACLE_ABSOLUTE_MIN_SPAWN_TIME = 40

    def __init__(self, screen_width=1280, screen_height=720, 
                 player_img_path='player.png', obstacle_img_path='obstacle.png',
                 sensor_handler_instance=None, piezo_jump_threshold=0.1,
                 led_controller_instance=None):
        """
        初始化 HDMI 遊戲引擎。
        參數:
            screen_width (int): HDMI 螢幕寬度。
            screen_height (int): HDMI 螢幕高度。
            player_img_path (str): 玩家圖片檔案路徑。
            obstacle_img_path (str): 障礙物圖片檔案路徑。
            sensor_handler_instance: 可選的 SensorHandler 實例，用於拍擊跳躍。
            piezo_jump_threshold (float): 拍擊跳躍的電壓閾值。
            led_controller_instance: 可選的 LedController 實例，用於遊戲中的燈效。
        """
        print("正在初始化 HdmiGameEngine...")
        if not pygame.get_init():
            pygame.init()
            print("Pygame 在 HdmiGameEngine 中初始化。")
        
        # 建議用較低解析度全螢幕（例如 1280x720）
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.FULLSCREEN)
        pygame.display.set_caption("互動式解壓小遊戲")
        self.clock = pygame.time.Clock()

        self.sensor_handler = sensor_handler_instance
        self.piezo_jump_threshold = piezo_jump_threshold
        if self.sensor_handler and hasattr(self.sensor_handler, 'is_initialized') and self.sensor_handler.is_initialized:
            print(f"HdmiGameEngine: 已連結 SensorHandler，拍擊跳躍閾值: {self.piezo_jump_threshold}V")
        else:
            print("HdmiGameEngine: 未提供有效 SensorHandler，拍擊跳躍功能將不可用。")
            self.sensor_handler = None
        
        self.led_controller = led_controller_instance
        if self.led_controller and hasattr(self.led_controller, 'is_on') and self.led_controller.is_on:
            print("HdmiGameEngine: 已連結 LedController。")
        else:
            print("HdmiGameEngine: 未提供有效 LedController，遊戲中 LED 燈效將不可用。")
            self.led_controller = None

        self._load_game_assets(player_img_path, obstacle_img_path)
        self._initialize_game_state_vars()
        self.is_initialized = True
        print("HdmiGameEngine 初始化完畢。")

    def _load_game_assets(self, player_img_path, obstacle_img_path):
        print("正在載入遊戲資源 (HDMI)...")
        scale_factor = 1.5  # 放大 1.5 倍

        # 玩家圖片
        try:
            player_image_orig = pygame.image.load(player_img_path).convert_alpha()
            orig_w, orig_h = player_image_orig.get_width(), player_image_orig.get_height()
            target_h = int(self.screen_height * 0.13 * scale_factor)
            scale_ratio = target_h / orig_h
            target_w = int(orig_w * scale_ratio)
            self.player_image = pygame.transform.smoothscale(player_image_orig, (target_w, target_h))
        except Exception as e:
            print(f"警告：無法載入玩家圖片 '{player_img_path}': {e}。將使用預留位置。")
            target_h = int(self.screen_height * 0.13 * scale_factor)
            target_w = int(target_h * 0.75)
            self.player_image = pygame.Surface((target_w, target_h), pygame.SRCALPHA)
            pygame.draw.rect(self.player_image, (0,200,0), self.player_image.get_rect())

        # 障礙物圖片
        try:
            obstacle_image_orig = pygame.image.load(obstacle_img_path).convert_alpha()
            orig_w, orig_h = obstacle_image_orig.get_width(), obstacle_image_orig.get_height()
            self.obstacle_height_options_scaled = {
                50: int(self.screen_height * 0.07 * scale_factor),
                75: int(self.screen_height * 0.12 * scale_factor)
            }
            self.obstacle_images_scaled = {}
            for key, target_h in self.obstacle_height_options_scaled.items():
                scale_ratio = target_h / orig_h
                target_w = int(orig_w * scale_ratio)
                self.obstacle_images_scaled[key] = pygame.transform.smoothscale(obstacle_image_orig, (target_w, target_h))
            self.obstacle_original_height_keys = list(self.obstacle_height_options_scaled.keys())
        except Exception as e:
            print(f"警告：無法載入障礙物圖片 '{obstacle_img_path}': {e}。將使用預留位置。")
            self.obstacle_height_options_scaled = {
                50: int(self.screen_height * 0.07 * scale_factor),
                75: int(self.screen_height * 0.12 * scale_factor)
            }
            self.obstacle_images_scaled = {}
            self.obstacle_original_height_keys = list(self.obstacle_height_options_scaled.keys())
            for key, target_h in self.obstacle_height_options_scaled.items():
                target_w = int(target_h * 0.5)
                surf = pygame.Surface((target_w, target_h), pygame.SRCALPHA)
                pygame.draw.rect(surf, (200,0,0), surf.get_rect())
                self.obstacle_images_scaled[key] = surf
        print("圖片資源載入並縮放完成 (HDMI)。")

        # 字型
        try:
            font_path = None
            font_size_small = max(18, int(self.screen_height / 30))
            font_size_medium = max(24, int(self.screen_height / 22))
            font_size_large = max(36, int(self.screen_height / 15))
            common_fonts = ["Microsoft YaHei.ttf", "wqy-microhei.ttc", "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc", "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf"]
            for f_name in common_fonts:
                if os.path.exists(f_name):
                    font_path = f_name
                    break
            if (font_path):
                self.font_small = pygame.font.Font(font_path, font_size_small)
                self.font_medium = pygame.font.Font(font_path, font_size_medium)
                self.font_large = pygame.font.Font(font_path, font_size_large)
            else:
                self.font_small = pygame.font.SysFont("dejavusans", font_size_small)
                self.font_medium = pygame.font.SysFont("dejavusans", font_size_medium)
                self.font_large = pygame.font.SysFont("dejavusans", font_size_large)
            print(f"使用字型 (HDMI): {font_path if font_path else 'DejaVuSans/Pygame Default'}")
        except pygame.error as e:
            print(f"字型載入錯誤 (HDMI): {e}。將使用 Pygame 預設字型。")
            self.font_small = pygame.font.Font(None, 24)
            self.font_medium = pygame.font.Font(None, 30)
            self.font_large = pygame.font.Font(None, 48)

    def _initialize_game_state_vars(self):
        """初始化遊戲過程中會變動的狀態變數。"""
        self.player_y_velocity = 0
        self.player_x_start_offset = int(self.screen_width * 0.1)
        self.player_rect = self.player_image.get_rect()
        self.player_rect.x = self.player_x_start_offset
        self.ground_height = self.screen_height - int(self.screen_height * 0.15)
        self.player_rect.bottom = self.ground_height
        self.is_jumping = False
        self.jump_buffer_expires_at = 0 # 跳躍緩衝計時器，儲存過期時間戳
        self.obstacles = []
        self.score = 0
        self.obstacle_speed = self.OBSTACLE_SPEED_INITIAL
        self.last_speed_increase_milestone = 0
        self.current_mileage = self.INITIAL_MILEAGE_DEFAULT # 會由 run_game 傳入的值覆寫
        self.obstacle_timer = 0
        self.obstacle_spawn_time = self.OBSTACLE_INITIAL_SPAWN_TIME_AVG
        self.game_active = False
        self.game_over_reason = None # e.g., "collision", "mileage_zero", "quit_event"
        self.player_speed = 6.0  # 初始速度，可自行調整
        self.player_speed_max = 20.0  # 最大速度

    def _reset_game(self, initial_mileage_val):
        """重置遊戲狀態以開始新的一局。"""
        self._initialize_game_state_vars()
        self.current_mileage = initial_mileage_val
        if not self.obstacles: 
            self.obstacles.append(self._create_obstacle())
        self.game_active = True
        self.game_over_reason = None
        pygame.event.clear()
        print(f"HDMI 遊戲已重置，初始情緒: {initial_mileage_val}")

    def _create_obstacle(self):
        """創建新的障礙物。"""
        original_height_key = random.choice(self.obstacle_original_height_keys)
        current_obstacle_image = self.obstacle_images_scaled[original_height_key]
        obstacle_rect = current_obstacle_image.get_rect()
        obstacle_rect.x = self.screen_width
        obstacle_rect.bottom = self.ground_height
        return {"rect": obstacle_rect, "height_key": original_height_key, "scored": False, "image": current_obstacle_image}

    def _display_stats_on_hdmi(self):
        """在 HDMI 螢幕上顯示分數和剩餘里程。"""
        score_text = self.font_small.render(f"價值: {self.score}", True, self.BLACK)
        self.screen.blit(score_text, (10, int(self.screen_height * 0.08)))
        mileage_text = self.font_small.render(f"情緒: {self.current_mileage}", True, self.BLACK)
        self.screen.blit(mileage_text, (10, int(self.screen_height * 0.02)))

    def _game_over_screen_on_hdmi(self):
        """在 HDMI 螢幕上顯示遊戲結束畫面，並等待使用者操作。"""
        self.screen.fill(self.WHITE)
        title_text_str = "遊戲結束"
        if self.game_over_reason == "collision": title_text_str = "你很菜"
        elif self.game_over_reason == "mileage_zero": title_text_str = "恭喜你成功離開這個令人傷心欲絕的城市"
        
        title_rendered = self.font_large.render(title_text_str, True, self.BLACK)
        score_rendered = self.font_medium.render(f"獲得價值: {self.score}", True, self.BLACK)
        mileage_rendered = self.font_medium.render(f"剩餘情緒: {self.current_mileage}", True, self.BLACK)
        instr_rendered = self.font_small.render("按 Q 鍵返回主選單", True, (80,80,80))

        text_y = int(self.screen_height * 0.25)
        line_h_L = title_rendered.get_height()
        line_h_M = score_rendered.get_height()
        pad = int(self.screen_height * 0.05)

        self.screen.blit(title_rendered, (self.screen_width // 2 - title_rendered.get_width() // 2, text_y))
        text_y += line_h_L + pad
        self.screen.blit(score_rendered, (self.screen_width // 2 - score_rendered.get_width() // 2, text_y))
        text_y += line_h_M + pad
        self.screen.blit(mileage_rendered, (self.screen_width // 2 - mileage_rendered.get_width() // 2, text_y))
        text_y += line_h_M + pad * 2
        self.screen.blit(instr_rendered, (self.screen_width // 2 - instr_rendered.get_width() // 2, text_y))
        
        pygame.display.flip() # 更新 HDMI 顯示

        waiting_for_input = True
        action_taken = "QUIT" # 預設
        while waiting_for_input:
            for evt in pygame.event.get():
                if evt.type == pygame.QUIT:
                    action_taken = "QUIT_VIA_WINDOW_CLOSE"
                    waiting_for_input = False
                if evt.type == pygame.KEYDOWN:
                    if evt.key == pygame.K_q: 
                        action_taken = "QUIT"
                        waiting_for_input = False
            self.clock.tick(self.FPS) 
        
        # 在返回前新增一個簡短的過場提示
        if action_taken == "QUIT" or action_taken == "QUIT_VIA_WINDOW_CLOSE":
            self.screen.fill(self.WHITE)
            returning_text = self.font_medium.render("正在返回主選單...", True, self.BLACK)
            self.screen.blit(returning_text, (self.screen_width // 2 - returning_text.get_width() // 2, self.screen_height // 2 - returning_text.get_height() // 2))
            pygame.display.flip()
            pygame.time.wait(1000) # 顯示1秒

        return action_taken

    def _execute_pre_game_sequence(self, emotion_index):
        """在 HDMI 螢幕上執行遊戲開始前的序列：顯示情緒指數和倒數。"""
        if not self.is_initialized: return

        # 階段1: 顯示情緒指數
        self.screen.fill(self.WHITE)
        line1_text = f"情緒壓力指數: {emotion_index}"
        line2_text = "遊戲即將開始..."
        l1_rendered = self.font_medium.render(line1_text, True, self.BLACK)
        l2_rendered = self.font_small.render(line2_text, True, self.BLACK)
        y_start = self.screen_height // 2 - (l1_rendered.get_height() + l2_rendered.get_height() + 10) // 2
        self.screen.blit(l1_rendered, (self.screen_width // 2 - l1_rendered.get_width() // 2, y_start))
        self.screen.blit(l2_rendered, (self.screen_width // 2 - l2_rendered.get_width() // 2, y_start + l1_rendered.get_height() + 10))
        pygame.display.flip()
        
        # 在這裡短暫等待，同時處理QUIT事件，防止視窗無響應
        wait_start_ticks = pygame.time.get_ticks()
        while pygame.time.get_ticks() - wait_start_ticks < 2000: # 顯示情緒指數2秒
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            self.clock.tick(15) # 低FPS保持響應

        # 階段2: 倒數計時
        for i in range(3, 0, -1):
            self.screen.fill(self.WHITE)
            countdown_text = self.font_large.render(str(i), True, self.BLACK)
            self.screen.blit(countdown_text, (self.screen_width // 2 - countdown_text.get_width() // 2, self.screen_height // 2 - countdown_text.get_height() // 2))
            pygame.display.flip()
            wait_start_ticks = pygame.time.get_ticks()
            while pygame.time.get_ticks() - wait_start_ticks < 1000: # 每秒更新
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                self.clock.tick(15)
        
        # 階段3: GO!
        self.screen.fill(self.WHITE)
        go_text = self.font_large.render("GO!", True, (0, 128, 0)) 
        self.screen.blit(go_text, (self.screen_width // 2 - go_text.get_width() // 2, self.screen_height // 2 - go_text.get_height() // 2))
        pygame.display.flip()
        wait_start_ticks = pygame.time.get_ticks()
        while pygame.time.get_ticks() - wait_start_ticks < 500: # GO 顯示半秒
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            self.clock.tick(15)
        print("HDMI 遊戲開始前序列完成。")

    def run_game(self, initial_mileage):
        """
        在 HDMI 螢幕上運行一局遊戲直到結束或退出。
        返回:
            dict: 包含遊戲結果, e.g., {'score': self.score, 'final_mileage': self.current_mileage, 'reason': self.game_over_reason}
        """
        if not self.is_initialized:
            print("錯誤: HdmiGameEngine 未初始化，無法開始遊戲。")
            return {'score': 0, 'final_mileage': initial_mileage, 'reason': 'engine_not_initialized'}

        # 先執行遊戲開始前序列 (顯示情緒、倒數)
        self._execute_pre_game_sequence(initial_mileage) # 注意: 這裡傳 initial_mileage 是為了顯示，但可能應該是 emotion_index
                                                       # 假設 initial_mileage 就是 get_player_emotion_index 返回的值

        self._reset_game(initial_mileage) # 重置遊戲狀態，並在此處清除事件佇列
        running_this_session = True
        
        if self.led_controller: # 遊戲開始時的 LED 效果
            from led_controller import Color # 確保 Color 可用
            # 可以選擇一個更動感的遊戲中效果，或者讓 main.py 控制
            # 這裡我們設定一個遊戲中的基礎色，例如脈動藍
            # 為了簡單，先設定靜態顏色，之後可以擴展為脈衝
            self.led_controller.static_color(Color(0, 25, 75)) 
            print("HdmiGameEngine: 設定遊戲中 LED 燈效。")

        print("開始 HDMI 遊戲會話...")
        while running_this_session:
            current_ticks = pygame.time.get_ticks() # 獲取當前時間戳

            for event in pygame.event.get():
                # print(event)  # debug: 印出所有事件
                if event.type == pygame.QUIT:
                    running_this_session = False
                    self.game_active = False 
                    self.game_over_reason = "quit_event"
                    break 
                if self.game_active:
                    if event.type == pygame.KEYDOWN:
                        if (event.key == pygame.K_SPACE or event.key == pygame.K_UP):
                            if not self.is_jumping: # 如果在地上，立即跳
                                self.is_jumping = True
                                self.player_y_velocity = self.JUMP_STRENGTH
                                self.jump_buffer_expires_at = 0 # 清除跳躍緩衝
                                print('跳躍')
                            else: # 如果在空中，設定跳躍緩衝
                                self.jump_buffer_expires_at = current_ticks + self.JUMP_BUFFER_DURATION_MS
            
            if not running_this_session: break

            if self.game_active:
                if self.is_jumping:
                    self.player_y_velocity += self.PLAYER_GRAVITY
                    self.player_rect.y += self.player_y_velocity
                    if self.player_rect.bottom >= self.ground_height:
                        self.player_rect.bottom = self.ground_height
                        self.is_jumping = False
                        self.player_y_velocity = 0
                        print(f"DEBUG: Landed! is_jumping: {self.is_jumping}. Buffer expires at: {self.jump_buffer_expires_at}, Now: {current_ticks}")
                        # 檢查並執行緩衝的跳躍
                        if self.jump_buffer_expires_at > current_ticks: # 注意這裡用 current_ticks，而不是重新 get_ticks()
                            self.is_jumping = True
                            self.player_y_velocity = self.JUMP_STRENGTH
                            print('跳躍')
                            print(f"DEBUG: Buffered jump executed! Velo: {self.player_y_velocity}")
                        self.jump_buffer_expires_at = 0 # 無論如何都清除緩衝
                
                current_score_milestone = self.score // 10
                if current_score_milestone > self.last_speed_increase_milestone:
                    # 讓加速度隨分數提升而增加（例如線性或指數）
                    # 這裡用線性：增量 = 0.2 + 0.01 * 分數里程碑
                    speed_increment = 0.2 + 0.15 * current_score_milestone
                    self.obstacle_speed = min(
                        self.obstacle_speed + speed_increment,
                        self.OBSTACLE_SPEED_INITIAL + 3.0 + 0.5 * current_score_milestone  # 最高速也隨分數提升
                    )
                    self.last_speed_increase_milestone = current_score_milestone
                    # 玩家速度也同步加快
                    player_speed_increment = 0.1 + 0.05 * current_score_milestone
                    self.player_speed = min(self.player_speed + player_speed_increment, self.player_speed_max + 0.2 * current_score_milestone)

                self.obstacle_timer += 1
                if self.obstacle_timer > self.obstacle_spawn_time:
                    self.obstacles.append(self._create_obstacle())
                    self.obstacle_timer = 0
                    prog = min(1.0, self.score / self.OBSTACLE_SCORE_TO_REACH_MIN_SPAWN_TIME)
                    curr_avg_spawn = self.OBSTACLE_INITIAL_SPAWN_TIME_AVG - prog * (self.OBSTACLE_INITIAL_SPAWN_TIME_AVG - self.OBSTACLE_MIN_SPAWN_TIME_AVG)
                    spawn_low = max(self.OBSTACLE_ABSOLUTE_MIN_SPAWN_TIME, int(curr_avg_spawn - self.OBSTACLE_SPAWN_TIME_RANDOM_RANGE / 2))
                    spawn_high = max(spawn_low + 5, int(curr_avg_spawn + self.OBSTACLE_SPAWN_TIME_RANDOM_RANGE / 2))
                    self.obstacle_spawn_time = random.randint(spawn_low, spawn_high)

                new_obstacles = []
                for obs_data in self.obstacles:
                    obs_data['rect'].x -= int(self.obstacle_speed)
                    if not obs_data['scored'] and obs_data['rect'].right < self.player_rect.left:
                        points = 0
                        if obs_data['height_key'] == self.obstacle_original_height_keys[0]: points = random.randint(3, 5)
                        elif obs_data['height_key'] == self.obstacle_original_height_keys[1]: points = random.randint(6, 8)
                        self.score += points
                        obs_data['scored'] = True
                    if obs_data['rect'].right > 0:
                        new_obstacles.append(obs_data)
                self.obstacles = new_obstacles

                for obs_data in self.obstacles:
                    if self.player_rect.colliderect(obs_data['rect']):
                        self.game_active = False
                        self.game_over_reason = "collision"
                        break
                
                if self.game_active:
                    self.current_mileage = initial_mileage - self.score
                    if self.current_mileage <= 0:
                        self.current_mileage = 0
                        self.game_active = False
                        self.game_over_reason = "mileage_zero"

                # 玩家橫向位置固定在左側
                self.player_rect.x = self.player_x_start_offset

                # 繪圖到 HDMI 螢幕
                self.screen.fill(self.WHITE)
                pygame.draw.rect(self.screen, self.GROUND_COLOR, (0, self.ground_height, self.screen_width, self.screen_height - self.ground_height))
                self.screen.blit(self.player_image, self.player_rect)
                for obs_data in self.obstacles:
                    self.screen.blit(obs_data['image'], obs_data['rect'])
                self._display_stats_on_hdmi()
                pygame.display.flip()

            else: # game_active is False (遊戲結束)
                user_choice = self._game_over_screen_on_hdmi()
                if user_choice == "QUIT" or user_choice == "QUIT_VIA_WINDOW_CLOSE":
                    running_this_session = False
                    if user_choice == "QUIT_VIA_WINDOW_CLOSE": self.game_over_reason = "quit_event"
                else:
                    running_this_session = False
            
            self.clock.tick(self.FPS)
            # print('Window focused:', pygame.key.get_focused())  # debug: 印出視窗焦點狀態
        
        # 遊戲會話結束，main.py 會根據結果設定 LED，這裡可以先清除或恢復預設
        if self.led_controller:
            self.led_controller.clear() # 清除遊戲中的特定燈效
            print("HdmiGameEngine: 清除遊戲中 LED 燈效。")

        print(f"HDMI 遊戲會話結束 (原因: {self.game_over_reason or '未知'}).")
        return {'score': self.score, 'final_mileage': self.current_mileage, 'reason': self.game_over_reason}

    def show_hdmi_standby_screen(self, title="互動式解壓遊戲", line1="按按鈕開始"):
        """在 HDMI 螢幕上顯示待機或提示訊息。"""
        if not self.is_initialized:
            print("錯誤: HdmiGameEngine 未初始化，無法顯示待機畫面。")
            return

        self.screen.fill(self.WHITE)
        
        title_rendered = self.font_large.render(title, True, self.BLACK)
        line1_rendered = self.font_medium.render(line1, True, self.BLACK)
        
        text_y = int(self.screen_height * 0.3)
        line_h_L = title_rendered.get_height()
        line_h_M = line1_rendered.get_height()
        pad = int(self.screen_height * 0.05)

        self.screen.blit(title_rendered, (self.screen_width // 2 - title_rendered.get_width() // 2, text_y))
        text_y += line_h_L + pad
        self.screen.blit(line1_rendered, (self.screen_width // 2 - line1_rendered.get_width() // 2, text_y))
        
        pygame.display.flip()
        print(f"HDMI 螢幕已更新為待機畫面: '{title} - {line1}'")

    def show_measuring_emotion_screen(self, duration=3):
        """在 HDMI 螢幕上顯示正在測量情緒的提示，並帶有簡單動畫。"""
        if not self.is_initialized:
            print("錯誤: HdmiGameEngine 未初始化，無法顯示測量畫面。")
            return

        print("HDMI 螢幕：顯示測量情緒畫面...")
        base_line1_text = "正在偵測您的負面情緒"
        line2_text = f"請在 {duration} 秒內盡情釋放！"
        l2_rendered = self.font_small.render(line2_text, True, (50, 50, 50))

        start_time = pygame.time.get_ticks() # 使用 Pygame 的時間
        animation_dots = 0
        dot_update_interval = 300 # 每 300ms 更新一次點
        last_dot_update = start_time

        while (pygame.time.get_ticks() - start_time) < (duration * 1000):
            # 處理基本的 Pygame 事件，以保持視窗響應，並允許退出
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    # 如果在測量時關閉視窗，也應當能終止
                    if hasattr(self, 'running_this_session'): # 如果在 run_game 內部被間接調用
                        self.running_this_session = False 
                        self.game_active = False
                        self.game_over_reason = "quit_event"
                    pygame.quit() # 直接退出pygame，因為這是一個阻塞畫面
                    sys.exit() # 結束程式
                # 可以添加一個按鍵提前結束測量的邏輯，但目前不需要
            
            current_time_ticks = pygame.time.get_ticks()
            if current_time_ticks - last_dot_update > dot_update_interval:
                animation_dots = (animation_dots + 1) % 4 # 0, 1, 2, 3 個點
                last_dot_update = current_time_ticks

            self.screen.fill(self.WHITE)
            animated_line1_text = base_line1_text + "." * animation_dots
            l1_rendered = self.font_medium.render(animated_line1_text, True, self.BLACK)
            
            y_pos = self.screen_height // 2 - (l1_rendered.get_height() + l2_rendered.get_height() + 10) // 2
            self.screen.blit(l1_rendered, (self.screen_width // 2 - l1_rendered.get_width() // 2, y_pos))
            y_pos += l1_rendered.get_height() + 10
            self.screen.blit(l2_rendered, (self.screen_width // 2 - l2_rendered.get_width() // 2, y_pos))
            
            pygame.display.flip()
            self.clock.tick(self.FPS) # 以遊戲的FPS運行，或者一個較低的值如20FPS

        print("HDMI 螢幕：測量情緒畫面顯示完畢。")
        # 測量畫面結束後，main.py 會繼續執行 get_player_emotion_index，然後是 pre_game_countdown

    def cleanup(self):
        """清理 Pygame 資源。通常由主程式在最後統一處理 pygame.quit()。"""
        print("HdmiGameEngine 正在清理 (通常無特定操作，pygame.quit() 由主程式管理)。")
        self.player_image = None
        self.obstacle_images_scaled = None
        self.obstacles = []
        pygame.display.quit()  # 關閉顯示，釋放 VRAM
        # pygame.quit() 應該在應用程式最末端呼叫

# --- 腳本執行 (測試用) ---
if __name__ == "__main__":
    print("HdmiGameEngine 測試開始...")
    game_engine = None
    try:
        # 模擬 SensorHandler
        class MockSensorHandlerForHdmiGame:
            def __init__(self, is_ready=True):
                self.is_initialized = is_ready
                self.adc_channels = {'A0': 'mock'} if is_ready else {}
            def check_any_piezo_trigger(self, threshold):
                # print("MockSensor: checking trigger")
                # return random.choice([True, False, False, False]) # 模擬拍擊
                return False # 預設不觸發，避免自動跳

        mock_sensor = MockSensorHandlerForHdmiGame(is_ready=True)
        
        game_engine = HdmiGameEngine(
            screen_width=800, screen_height=600,
            sensor_handler_instance=mock_sensor,
            piezo_jump_threshold=0.2
        )
        
        if game_engine.is_initialized:
            initial_test_mileage = 200
            print(f"\n將以 {initial_test_mileage} 的初始情緒開始遊戲測試...")
            input("按 Enter 鍵開始 HDMI 遊戲測試 (pygame 視窗會開啟)... ")
            
            results = game_engine.run_game(initial_test_mileage)
            print("遊戲結果:", results)
            
            # 測試第二次遊玩
            # input("按 Enter 鍵開始第二次 HDMI 遊戲測試... ")
            # results2 = game_engine.run_game(100)
            # print("第二次遊戲結果:", results2)

    except Exception as e:
        print(f"執行 HdmiGameEngine 測試時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if game_engine:
            game_engine.cleanup()
        if pygame.get_init(): # 確保 pygame 被關閉
            pygame.quit()
        print("HdmiGameEngine 測試結束。")