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
    PLAYER_GRAVITY = 0.8
    JUMP_STRENGTH = -15 # 可以微調跳躍高度
    OBSTACLE_SPEED_INITIAL = 5.0
    INITIAL_MILEAGE_DEFAULT = 350

    OBSTACLE_INITIAL_SPAWN_TIME_AVG = 120 # 幀
    OBSTACLE_MIN_SPAWN_TIME_AVG = 60
    OBSTACLE_SCORE_TO_REACH_MIN_SPAWN_TIME = 1000
    OBSTACLE_SPAWN_TIME_RANDOM_RANGE = 30
    OBSTACLE_ABSOLUTE_MIN_SPAWN_TIME = 40

    def __init__(self, screen_width=800, screen_height=600, 
                 player_img_path='player.png', obstacle_img_path='obstacle.png',
                 sensor_handler_instance=None, piezo_jump_threshold=0.1):
        """
        初始化 HDMI 遊戲引擎。
        參數:
            screen_width (int): HDMI 螢幕寬度。
            screen_height (int): HDMI 螢幕高度。
            player_img_path (str): 玩家圖片檔案路徑。
            obstacle_img_path (str): 障礙物圖片檔案路徑。
            sensor_handler_instance: 可選的 SensorHandler 實例，用於拍擊跳躍。
            piezo_jump_threshold (float): 拍擊跳躍的電壓閾值。
        """
        print("正在初始化 HdmiGameEngine...")
        if not pygame.get_init():
            pygame.init()
            print("Pygame 在 HdmiGameEngine 中初始化。")
        
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("互動式解壓小遊戲")
        self.clock = pygame.time.Clock()

        self.sensor_handler = sensor_handler_instance
        self.piezo_jump_threshold = piezo_jump_threshold
        if self.sensor_handler and hasattr(self.sensor_handler, 'is_initialized') and self.sensor_handler.is_initialized:
            print(f"HdmiGameEngine: 已連結 SensorHandler，拍擊跳躍閾值: {self.piezo_jump_threshold}V")
        else:
            print("HdmiGameEngine: 未提供有效 SensorHandler，拍擊跳躍功能將不可用。")
            self.sensor_handler = None

        self._load_game_assets(player_img_path, obstacle_img_path)
        self._initialize_game_state_vars()
        self.is_initialized = True
        print("HdmiGameEngine 初始化完畢。")

    def _load_game_assets(self, player_img_path, obstacle_img_path):
        """載入並縮放遊戲圖片和字型。"""
        print("正在載入遊戲資源 (HDMI)...")
        # 玩家圖片
        try:
            player_image_orig = pygame.image.load(player_img_path).convert_alpha()
            player_w = max(30, int(self.screen_width * 0.05))
            player_h = max(40, int(self.screen_height * 0.1))
            self.player_image = pygame.transform.scale(player_image_orig, (player_w, player_h))
        except pygame.error as e:
            print(f"警告：無法載入玩家圖片 '{player_img_path}': {e}。將使用預留位置。")
            self.player_image = pygame.Surface((max(30, int(self.screen_width * 0.05)), max(40, int(self.screen_height * 0.1))), pygame.SRCALPHA)
            pygame.draw.rect(self.player_image, (0,200,0), self.player_image.get_rect())

        # 障礙物圖片
        try:
            obstacle_image_orig = pygame.image.load(obstacle_img_path).convert_alpha()
            # 障礙物高度選項與縮放 (可根據 HDMI 螢幕調整)
            self.obstacle_height_options_scaled = {
                50: max(20, int(50 * (self.screen_height / 480.0))), # 假設原始設計基於較低解析度
                75: max(30, int(75 * (self.screen_height / 480.0)))
            }
            obstacle_base_w_scaled = max(15, int(30 * (self.screen_width / 800.0)))
            self.obstacle_images_scaled = {}
            for original_h, scaled_h_val in self.obstacle_height_options_scaled.items():
                self.obstacle_images_scaled[original_h] = pygame.transform.scale(obstacle_image_orig, (obstacle_base_w_scaled, scaled_h_val))
            self.obstacle_original_height_keys = list(self.obstacle_height_options_scaled.keys())
        except pygame.error as e:
            print(f"警告：無法載入障礙物圖片 '{obstacle_img_path}': {e}。將使用預留位置。")
            self.obstacle_height_options_scaled = {50:30, 75:45}
            self.obstacle_images_scaled = {}
            self.obstacle_original_height_keys = list(self.obstacle_height_options_scaled.keys())
            for _k, _h in self.obstacle_height_options_scaled.items():
                surf = pygame.Surface((20,_h), pygame.SRCALPHA)
                pygame.draw.rect(surf, (200,0,0), surf.get_rect())
                self.obstacle_images_scaled[_k] = surf
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
            if font_path:
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
        self.obstacles = []
        self.score = 0
        self.obstacle_speed = self.OBSTACLE_SPEED_INITIAL
        self.last_speed_increase_milestone = 0
        self.current_mileage = self.INITIAL_MILEAGE_DEFAULT # 會由 run_game 傳入的值覆寫
        self.obstacle_timer = 0
        self.obstacle_spawn_time = self.OBSTACLE_INITIAL_SPAWN_TIME_AVG
        self.game_active = False
        self.game_over_reason = None # e.g., "collision", "mileage_zero", "quit_event"

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
        elif self.game_over_reason == "mileage_zero": title_text_str = "恭喜脫離苦海"
        
        title_rendered = self.font_large.render(title_text_str, True, self.BLACK)
        score_rendered = self.font_medium.render(f"獲得價值: {self.score}", True, self.BLACK)
        mileage_rendered = self.font_medium.render(f"剩餘情緒: {self.current_mileage}", True, self.BLACK)
        instr_rendered = self.font_small.render("按 R 重玩 / Q 離開遊戲", True, (80,80,80))

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
                    if evt.key == pygame.K_r: 
                        action_taken = "RESTART"
                        waiting_for_input = False
                    if evt.key == pygame.K_q: 
                        action_taken = "QUIT"
                        waiting_for_input = False
            self.clock.tick(self.FPS) # 保持時鐘滴答
        return action_taken

    def run_game(self, initial_mileage):
        """
        在 HDMI 螢幕上運行一局遊戲直到結束或退出。
        返回:
            dict: 包含遊戲結果, e.g., {'score': self.score, 'final_mileage': self.current_mileage, 'reason': self.game_over_reason}
        """
        if not self.is_initialized:
            print("錯誤: HdmiGameEngine 未初始化，無法開始遊戲。")
            return {'score': 0, 'final_mileage': initial_mileage, 'reason': 'engine_not_initialized'}

        self._reset_game(initial_mileage)
        running_this_session = True

        print("開始 HDMI 遊戲會話...")
        while running_this_session:
            piezo_triggered_jump = False
            if self.game_active and not self.is_jumping and self.sensor_handler:
                if self.sensor_handler.check_any_piezo_trigger(threshold=self.piezo_jump_threshold):
                    piezo_triggered_jump = True
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running_this_session = False
                    self.game_active = False # 確保遊戲結束
                    self.game_over_reason = "quit_event"
                    break 
                if self.game_active:
                    if event.type == pygame.KEYDOWN:
                        if (event.key == pygame.K_SPACE or event.key == pygame.K_UP) and not self.is_jumping:
                            self.is_jumping = True
                            self.player_y_velocity = self.JUMP_STRENGTH
            
            if not running_this_session: break

            if piezo_triggered_jump and self.game_active and not self.is_jumping:
                self.is_jumping = True
                self.player_y_velocity = self.JUMP_STRENGTH
                print("HdmiGameEngine: 偵測到拍擊，觸發跳躍！")

            if self.game_active:
                # 遊戲邏輯更新
                if self.is_jumping:
                    self.player_y_velocity += self.PLAYER_GRAVITY
                    self.player_rect.y += self.player_y_velocity
                    if self.player_rect.bottom >= self.ground_height:
                        self.player_rect.bottom = self.ground_height
                        self.is_jumping = False
                        self.player_y_velocity = 0
                
                current_score_milestone = self.score // 10
                if current_score_milestone > self.last_speed_increase_milestone:
                    self.obstacle_speed = min(self.obstacle_speed + 0.2, self.OBSTACLE_SPEED_INITIAL + 3.0)
                    self.last_speed_increase_milestone = current_score_milestone

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
                if user_choice == "RESTART":
                    self._reset_game(initial_mileage) 
                elif user_choice == "QUIT" or user_choice == "QUIT_VIA_WINDOW_CLOSE":
                    running_this_session = False
                    if user_choice == "QUIT_VIA_WINDOW_CLOSE": self.game_over_reason = "quit_event"
            
            self.clock.tick(self.FPS)
        
        print(f"HDMI 遊戲會話結束 (原因: {self.game_over_reason or '未知'}).")
        return {'score': self.score, 'final_mileage': self.current_mileage, 'reason': self.game_over_reason}

    def cleanup(self):
        """清理 Pygame 資源。通常由主程式在最後統一處理 pygame.quit()。"""
        print("HdmiGameEngine 正在清理 (通常無特定操作，pygame.quit() 由主程式管理)。")
        # pygame.quit() 應該在應用程式最末端呼叫，此處可留空或僅作日誌

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