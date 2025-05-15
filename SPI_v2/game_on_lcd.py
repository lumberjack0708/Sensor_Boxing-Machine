# RandomGenerate/SPI_v2/game_on_lcd.py
import digitalio
import board
from PIL import Image # ImageDraw, ImageFont are used internally by methods
from adafruit_rgb_display import ili9341
import pygame
import random
import sys
import os

# SensorHandler 類別的匯入是為了類型提示，實際的實例會由外部傳入
# from .sensor_handler import SensorHandler # 僅用於類型提示

class LcdGameController:
    """控制 ILI9341 LCD 顯示並運行適配版小遊戲的類別。"""

    # --- 靜態或類別層級的常數 (原 spi.py 中的全域遊戲參數) ---
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    GROUND_COLOR = (140, 120, 100)
    FPS = 30
    PLAYER_GRAVITY = 0.8
    JUMP_STRENGTH = -10
    OBSTACLE_SPEED_INITIAL = 2.0
    # PIXELS_PER_POINT = 70.0 # 距離得分，遊戲內分數主要來自跳過障礙物
    INITIAL_MILEAGE_DEFAULT = 350 # 如果未提供，則使用此預設初始里程

    # 障礙物生成頻率參數
    OBSTACLE_INITIAL_SPAWN_TIME_AVG = 180
    OBSTACLE_MIN_SPAWN_TIME_AVG = 80
    OBSTACLE_SCORE_TO_REACH_MIN_SPAWN_TIME = 1000
    OBSTACLE_SPAWN_TIME_RANDOM_RANGE = 40
    OBSTACLE_ABSOLUTE_MIN_SPAWN_TIME = 45

    def __init__(self, cs_pin_board, dc_pin_board, rst_pin_board, backlight_pin_board=None,
                 baudrate=48000000, rotation=270, player_img_path='player.png', obstacle_img_path='obstacle.png',
                 sensor_handler_instance=None, piezo_jump_threshold=0.1):
        """
        初始化 LCD 顯示器和遊戲資源。
        參數:
            cs_pin_board: Chip Select pin (e.g., board.CE0)
            dc_pin_board: Data/Command pin (e.g., board.D25)
            rst_pin_board: Reset pin (e.g., board.D24)
            backlight_pin_board (optional): Backlight control pin (e.g., board.D27)
            baudrate (int): SPI baudrate.
            rotation (int): Display rotation (0, 90, 180, 270).
            player_img_path (str): 玩家圖片檔案路徑。
            obstacle_img_path (str): 障礙物圖片檔案路徑。
            sensor_handler_instance: 可選的 SensorHandler 實例，用於拍擊跳躍。
            piezo_jump_threshold (float): 拍擊跳躍的電壓閾值。
        """
        print("正在初始化 LcdGameController...")
        self.disp = None
        self.game_screen_width = 0
        self.game_screen_height = 0
        self.clock = pygame.time.Clock()

        # 儲存 SensorHandler 實例和相關閾值
        self.sensor_handler = sensor_handler_instance
        self.piezo_jump_threshold = piezo_jump_threshold
        if self.sensor_handler and hasattr(self.sensor_handler, 'is_initialized') and self.sensor_handler.is_initialized:
            print(f"LcdGameController: 已連結 SensorHandler，拍擊跳躍閾值: {self.piezo_jump_threshold}V")
        else:
            print("LcdGameController: 未提供有效 SensorHandler，拍擊跳躍功能將不可用。")
            self.sensor_handler = None # 確保無效時設為 None

        try:
            cs_pin = digitalio.DigitalInOut(cs_pin_board)
            dc_pin = digitalio.DigitalInOut(dc_pin_board)
            reset_pin = digitalio.DigitalInOut(rst_pin_board)
            
            self.backlight_controller = None
            if backlight_pin_board:
                self.backlight_controller = digitalio.DigitalInOut(backlight_pin_board)
                self.backlight_controller.switch_to_output()
                self.backlight_controller.value = True # 開啟背光

            spi_bus = board.SPI()
            self.disp = ili9341.ILI9341(
                spi_bus,
                rotation=rotation,
                cs=cs_pin,
                dc=dc_pin,
                rst=reset_pin,
                baudrate=baudrate,
            )
            if self.disp.rotation % 180 == 90: # Landscape
                self.game_screen_width = self.disp.height
                self.game_screen_height = self.disp.width
            else: # Portrait
                self.game_screen_width = self.disp.width
                self.game_screen_height = self.disp.height
            print(f"ILI9341 Display initialized: {self.game_screen_width}x{self.game_screen_height}")
        except Exception as e:
            print(f"ILI9341 Display 初始化失敗: {e}")
            self.disp = None # 確保 disp 在失敗時為 None
            # 可以在此處引發異常，讓呼叫者知道初始化失敗
            raise RuntimeError(f"Failed to initialize ILI9341 display: {e}")

        if not pygame.get_init():
            pygame.init()
            print("Pygame 在 LcdGameController 中初始化。")
        
        self._load_game_assets(player_img_path, obstacle_img_path)
        self._initialize_game_state_vars()
        print("LcdGameController 初始化完畢。")

    def _load_game_assets(self, player_img_path, obstacle_img_path):
        """載入並縮放遊戲圖片和字型。"""
        print("正在載入遊戲資源...")
        try:
            player_image_orig = pygame.image.load(player_img_path).convert_alpha()
            obstacle_image_orig = pygame.image.load(obstacle_img_path).convert_alpha()

            player_w = max(18, int(self.game_screen_width * 0.075))
            player_h = max(22, int(self.game_screen_height * 0.13))
            self.player_image = pygame.transform.scale(player_image_orig, (player_w, player_h))

            scale_factor_h = self.game_screen_height / 300.0
            self.obstacle_height_options_scaled = {
                30: max(10, int(30 * scale_factor_h)),
                45: max(15, int(45 * scale_factor_h))
            }
            obstacle_base_w_scaled = max(8, int(20 * (self.game_screen_width / 800.0)))
            self.obstacle_images_scaled = {}
            for original_h, scaled_h_val in self.obstacle_height_options_scaled.items():
                self.obstacle_images_scaled[original_h] = pygame.transform.scale(obstacle_image_orig, (obstacle_base_w_scaled, scaled_h_val))
            
            self.obstacle_original_height_keys = [30, 45] # 與 scaled map 的鍵對應
            print("圖片資源載入並縮放完成。")

        except pygame.error as e:
            print(f"警告：無法載入或縮放圖片 '{e}'。遊戲外觀可能受影響。")
            # 創建預留位置圖片 (可選)
            self.player_image = pygame.Surface((max(18, int(self.game_screen_width * 0.075)), max(22, int(self.game_screen_height * 0.13))), pygame.SRCALPHA)
            pygame.draw.rect(self.player_image, (0,200,0), self.player_image.get_rect())
            self.obstacle_height_options_scaled = {30:15, 45:22}
            self.obstacle_images_scaled = {}
            self.obstacle_original_height_keys = [30, 45]
            for _k, _h in self.obstacle_height_options_scaled.items():
                surf = pygame.Surface((10,_h), pygame.SRCALPHA)
                pygame.draw.rect(surf, (200,0,0), surf.get_rect())
                self.obstacle_images_scaled[_k] = surf

        try:
            font_path = None
            font_size_small = max(10, int(self.game_screen_height / 22))
            font_size_large = max(14, int(self.game_screen_height / 17))
            common_fonts = ["Microsoft YaHei.ttf", "wqy-microhei.ttc", "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc", "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf"]
            for f_name in common_fonts:
                if os.path.exists(f_name):
                    font_path = f_name
                    break
            if font_path:
                self.font_small = pygame.font.Font(font_path, font_size_small)
                self.font_large = pygame.font.Font(font_path, font_size_large)
            else:
                try:
                    self.font_small = pygame.font.SysFont("dejavusans", font_size_small)
                    self.font_large = pygame.font.SysFont("dejavusans", font_size_large)
                except pygame.error:
                    self.font_small = pygame.font.Font(None, font_size_small + 2)
                    self.font_large = pygame.font.Font(None, font_size_large + 2)
            print(f"使用字型: {font_path if font_path else 'DejaVuSans/Pygame Default'}")
        except pygame.error as e:
            print(f"字型載入錯誤: {e}。將使用 Pygame 預設字型。")
            self.font_small = pygame.font.Font(None, 12)
            self.font_large = pygame.font.Font(None, 18)

    def _initialize_game_state_vars(self):
        """初始化遊戲過程中會變動的狀態變數。"""
        self.player_y_velocity = 0
        self.player_x_start_offset = int(self.game_screen_width * 0.1)
        self.player_rect = self.player_image.get_rect()
        self.player_rect.x = self.player_x_start_offset
        self.ground_height = self.game_screen_height - int(self.game_screen_height * 0.12)
        self.player_rect.bottom = self.ground_height
        self.is_jumping = False
        self.obstacles = []
        self.score = 0
        # self.score_float = 0.0 # 距離得分已移除
        self.obstacle_speed = self.OBSTACLE_SPEED_INITIAL
        self.last_speed_increase_milestone = 0
        self.current_mileage = self.INITIAL_MILEAGE_DEFAULT
        self.obstacle_timer = 0
        self.obstacle_spawn_time = self.OBSTACLE_INITIAL_SPAWN_TIME_AVG
        self.game_active = False
        self.game_over_reason = None
        # 遊戲畫布
        self.game_canvas = pygame.Surface((self.game_screen_width, self.game_screen_height))

    def _reset_game(self, initial_mileage_val):
        """重置遊戲狀態以開始新的一局。"""
        self._initialize_game_state_vars() # 重新初始化大部分變數
        self.current_mileage = initial_mileage_val # 設定本次遊戲的初始里程
        if not self.obstacles: # 確保遊戲開始時至少有一個障礙物
            self.obstacles.append(self._create_obstacle())
        self.game_active = True
        self.game_over_reason = None
        pygame.event.clear() # 清除事件佇列
        print(f"遊戲已重置，初始情緒: {initial_mileage_val}")

    def _create_obstacle(self):
        """創建新的障礙物。"""
        original_height_key = random.choice(self.obstacle_original_height_keys)
        current_obstacle_image = self.obstacle_images_scaled[original_height_key]
        obstacle_rect = current_obstacle_image.get_rect()
        obstacle_rect.x = self.game_screen_width
        obstacle_rect.bottom = self.ground_height
        return {"rect": obstacle_rect, "height_key": original_height_key, "scored": False, "image": current_obstacle_image}

    def _display_stats(self):
        """在遊戲畫布上顯示分數和剩餘里程。"""
        score_text = self.font_small.render(f"價值:{self.score}", True, self.BLACK)
        self.game_canvas.blit(score_text, (5, int(self.game_screen_height * 0.08)))
        mileage_text = self.font_small.render(f"情緒:{self.current_mileage}", True, self.BLACK)
        self.game_canvas.blit(mileage_text, (5, int(self.game_screen_height * 0.02)))

    def _game_over_screen(self):
        """在遊戲畫布上顯示遊戲結束畫面，並更新到 LCD。"""
        self.game_canvas.fill(self.WHITE)
        title_text_str = ""
        if self.game_over_reason == "collision": title_text_str = "你很菜"
        elif self.game_over_reason == "mileage_zero": title_text_str = "恭喜脫離苦海"
        else: title_text_str = "遊戲結束"

        title_rendered = self.font_large.render(title_text_str, True, self.BLACK)
        score_rendered = self.font_small.render(f"獲得價值: {self.score}", True, self.BLACK)
        mileage_rendered = self.font_small.render(f"剩餘情緒: {self.current_mileage}", True, self.BLACK)
        instr_rendered = self.font_small.render("按 R 重玩 / Q 離開", True, (80,80,80))

        text_y = int(self.game_screen_height * 0.15)
        line_h_L = title_rendered.get_height()
        line_h_S = score_rendered.get_height()
        pad = int(self.game_screen_height * 0.03)

        self.game_canvas.blit(title_rendered, (self.game_screen_width // 2 - title_rendered.get_width() // 2, text_y))
        text_y += line_h_L + pad
        self.game_canvas.blit(score_rendered, (self.game_screen_width // 2 - score_rendered.get_width() // 2, text_y))
        text_y += line_h_S + pad
        self.game_canvas.blit(mileage_rendered, (self.game_screen_width // 2 - mileage_rendered.get_width() // 2, text_y))
        text_y += line_h_S + pad * 2
        self.game_canvas.blit(instr_rendered, (self.game_screen_width // 2 - instr_rendered.get_width() // 2, text_y))

        pil_img_data = pygame.image.tostring(self.game_canvas, 'RGB')
        pil_img = Image.frombytes('RGB', (self.game_screen_width, self.game_screen_height), pil_img_data)
        if self.disp: self.disp.image(pil_img)

        waiting = True
        action = "QUIT" # 預設為退出
        while waiting:
            for evt in pygame.event.get():
                if evt.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if evt.type == pygame.KEYDOWN:
                    if evt.key == pygame.K_r: action = "RESTART"; waiting = False
                    if evt.key == pygame.K_q: action = "QUIT"; waiting = False
            self.clock.tick(self.FPS)
        return action

    def play_game(self, initial_mileage):
        """運行一局遊戲直到結束或退出。"""
        if not self.disp: 
            print("錯誤: LCD 未初始化，無法開始遊戲。")
            return

        self._reset_game(initial_mileage)
        running_this_session = True

        print("開始 LCD 遊戲會話...")
        while running_this_session:
            piezo_triggered_jump = False # 新增：標記是否由拍擊觸發跳躍
            if self.game_active and not self.is_jumping and self.sensor_handler:
                if self.sensor_handler.check_any_piezo_trigger(threshold=self.piezo_jump_threshold):
                    piezo_triggered_jump = True
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running_this_session = False
                    self.game_over_reason = "quit_event" # 標記退出原因
                    # pygame.quit() # 由最外層的 main.py 處理最終的 quit
                    # sys.exit()
                    break # 跳出事件迴圈
                if self.game_active:
                    if event.type == pygame.KEYDOWN:
                        if (event.key == pygame.K_SPACE or event.key == pygame.K_UP) and not self.is_jumping:
                            self.is_jumping = True
                            self.player_y_velocity = self.JUMP_STRENGTH
            
            if not running_this_session: # 如果 PYGAME.QUIT 事件觸發了退出
                break

            # 處理拍擊跳躍 (如果在事件迴圈外檢測，確保只觸發一次)
            if piezo_triggered_jump and self.game_active and not self.is_jumping:
                self.is_jumping = True
                self.player_y_velocity = self.JUMP_STRENGTH
                print("LcdGameController: 偵測到拍擊，觸發跳躍！") # 除錯訊息

            if self.game_active:
                # --- 遊戲邏輯更新 ---
                if self.is_jumping:
                    self.player_y_velocity += self.PLAYER_GRAVITY
                    self.player_rect.y += self.player_y_velocity
                    if self.player_rect.bottom >= self.ground_height:
                        self.player_rect.bottom = self.ground_height
                        self.is_jumping = False
                        self.player_y_velocity = 0
                
                # 速度增加邏輯 (基於分數)
                current_score_milestone = self.score // 10
                if current_score_milestone > self.last_speed_increase_milestone:
                    self.obstacle_speed = min(self.obstacle_speed + 0.1, self.OBSTACLE_SPEED_INITIAL + 1.5)
                    self.last_speed_increase_milestone = current_score_milestone

                # 障礙物生成與移動
                self.obstacle_timer += 1
                if self.obstacle_timer > self.obstacle_spawn_time:
                    self.obstacles.append(self._create_obstacle())
                    self.obstacle_timer = 0
                    prog = min(1.0, self.score / self.OBSTACLE_SCORE_TO_REACH_MIN_SPAWN_TIME)
                    curr_avg_spawn = self.OBSTACLE_INITIAL_SPAWN_TIME_AVG - prog * (self.OBSTACLE_INITIAL_SPAWN_TIME_AVG - self.OBSTACLE_MIN_SPAWN_TIME_AVG)
                    spawn_low = max(self.OBSTACLE_ABSOLUTE_MIN_SPAWN_TIME, int(curr_avg_spawn - self.OBSTACLE_SPAWN_TIME_RANDOM_RANGE / 2))
                    spawn_high = max(spawn_low + 1, int(curr_avg_spawn + self.OBSTACLE_SPAWN_TIME_RANDOM_RANGE / 2))
                    self.obstacle_spawn_time = random.randint(spawn_low, spawn_high)

                new_obstacles = []
                for obs_data in self.obstacles:
                    obs_data['rect'].x -= int(self.obstacle_speed)
                    if not obs_data['scored'] and obs_data['rect'].right < self.player_rect.left:
                        points = 0
                        if obs_data['height_key'] == 30: points = random.randint(3, 5)
                        elif obs_data['height_key'] == 45: points = random.randint(6, 8)
                        self.score += points
                        obs_data['scored'] = True
                    if obs_data['rect'].right > 0:
                        new_obstacles.append(obs_data)
                self.obstacles = new_obstacles

                # 碰撞檢測
                for obs_data in self.obstacles:
                    if self.player_rect.colliderect(obs_data['rect']):
                        self.game_active = False
                        self.game_over_reason = "collision"
                        break
                
                if self.game_active: # 里程耗盡檢測
                    self.current_mileage = initial_mileage - self.score # 使用傳入的 initial_mileage
                    if self.current_mileage <= 0:
                        self.current_mileage = 0
                        self.game_active = False
                        self.game_over_reason = "mileage_zero"

                # --- 繪圖到遊戲畫布 ---
                self.game_canvas.fill(self.WHITE)
                pygame.draw.rect(self.game_canvas, self.GROUND_COLOR, (0, self.ground_height, self.game_screen_width, self.game_screen_height - self.ground_height))
                self.game_canvas.blit(self.player_image, self.player_rect)
                for obs_data in self.obstacles:
                    self.game_canvas.blit(obs_data['image'], obs_data['rect'])
                self._display_stats()

                # 更新到 LCD
                pil_img_data = pygame.image.tostring(self.game_canvas, 'RGB')
                pil_img = Image.frombytes('RGB', (self.game_screen_width, self.game_screen_height), pil_img_data)
                if self.disp: self.disp.image(pil_img)

            else: # game_active is False (遊戲結束)
                action = self._game_over_screen() # 顯示結束畫面並獲取使用者操作
                if action == "RESTART":
                    self._reset_game(initial_mileage) # 使用相同的初始里程重置
                    # game_active 已經在 _reset_game 中設為 True
                elif action == "QUIT":
                    running_this_session = False # 結束此遊戲會話
            
            self.clock.tick(self.FPS)
        
        print(f"LCD 遊戲會話結束 (原因: {self.game_over_reason or '未知'}).")

    def cleanup(self):
        """清理資源，例如關閉 LCD 背光。"""
        print("正在清理 LcdGameController 資源...")
        if self.backlight_controller and hasattr(self.backlight_controller, 'value'):
            self.backlight_controller.value = False # 關閉背光
            print("LCD 背光已關閉。")
        # Pygame 的 quit 通常由主應用程式在最後處理

# --- 腳本執行 (測試用) ---
if __name__ == "__main__":
    print("LcdGameController 測試開始...")
    try:
        # 為了測試 SensorHandler 的整合，我們需要一個模擬的 SensorHandler
        class MockSensorHandlerForLcdGame:
            def __init__(self, is_ready=True, channels_exist=True):
                self.is_initialized = is_ready
                self.adc_channels = {} if not channels_exist else {'A0': 'mock'} # 簡單標記通道存在
                print(f"MockSensorHandlerForLcdGame initialized: ready={is_ready}, channels={bool(self.adc_channels)}")

            def check_any_piezo_trigger(self, threshold):
                # 模擬隨機觸發，或根據外部輸入觸發
                # print(f"MockSensor: checking trigger, threshold {threshold}")
                # return random.choice([True, False, False]) # 1/3 的機率觸發
                # 為了手動測試，可以提示使用者
                # val = input("模擬拍擊? (y/N): ")
                # return val.lower() == 'y'
                return False # 預設不觸發，以免自動跳躍

        mock_sensor = MockSensorHandlerForLcdGame(is_ready=True)
        # 如果要測試 sensor_handler 未就緒的情況：
        # mock_sensor = MockSensorHandlerForLcdGame(is_ready=False)

        game_controller = LcdGameController(
            cs_pin_board=board.CE0, 
            dc_pin_board=board.D25, 
            rst_pin_board=board.D24, 
            backlight_pin_board=board.D27,
            sensor_handler_instance=mock_sensor, # 傳入模擬的 sensor_handler
            piezo_jump_threshold=0.1
        )
        
        if game_controller.disp: # 確保顯示器初始化成功
            session_mileage = 300
            print(f"\n將以 {session_mileage} 的初始情緒開始遊戲...")
            print("在遊戲中，除了空白鍵/向上鍵，嘗試模擬拍擊 (如果測試代碼支援)。")
            input("按 Enter 鍵開始遊戲測試...")
            game_controller.play_game(session_mileage)
            
            # 可以再玩一次
            # session_mileage_2 = 150
            # print(f"\n將以 {session_mileage_2} 的初始情緒再玩一次...")
            # input("按 Enter 鍵開始第二次遊戲測試...")
            # game_controller.play_game(session_mileage_2)

    except RuntimeError as e:
        print(f"執行 LcdGameController 測試時發生錯誤: {e}")
    except KeyboardInterrupt:
        print("\n遊戲測試被使用者中斷。")
    except Exception as e:
        print(f"\n執行測試時發生未預期錯誤: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'game_controller' in locals() and game_controller:
            game_controller.cleanup()
        if pygame.get_init():
            pygame.quit()
        print("LcdGameController 測試結束。") 