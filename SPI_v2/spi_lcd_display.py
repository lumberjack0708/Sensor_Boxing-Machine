import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
from adafruit_rgb_display import ili9341
import os
import pygame # 仍然需要 pygame.font 來載入字型，或者直接用 PIL 的 ImageFont

class SpiLcdDisplay:
    """控制 ILI9341 SPI LCD 顯示器，用於顯示遊戲結果等文字訊息。"""

    # --- 顯示常數 ---
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    DEFAULT_BG_COLOR = WHITE

    def __init__(self, cs_pin_board, dc_pin_board, rst_pin_board, backlight_pin_board=None,
                 baudrate=48000000, rotation=270):
        """
        初始化 SPI LCD 顯示器。
        參數:
            cs_pin_board: Chip Select pin (e.g., board.CE0)
            dc_pin_board: Data/Command pin (e.g., board.D25)
            rst_pin_board: Reset pin (e.g., board.D24)
            backlight_pin_board (optional): Backlight control pin (e.g., board.D27)
            baudrate (int): SPI baudrate.
            rotation (int): Display rotation (0, 90, 180, 270).
        """
        print("正在初始化 SpiLcdDisplay...")
        self.disp = None
        self.width = 0
        self.height = 0
        self.is_initialized = False
        self.rotation = rotation

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
                self.width = self.disp.height
                self.height = self.disp.width
            else: # Portrait
                self.width = self.disp.width
                self.height = self.disp.height
            
            self._load_font()
            self.is_initialized = True
            print(f"SpiLcdDisplay 初始化成功: {self.width}x{self.height}")
            self.clear_display() # 初始清屏

        except Exception as e:
            print(f"SpiLcdDisplay 初始化失敗: {e}")
            self.disp = None
            # raise RuntimeError(f"Failed to initialize ILI9341 display: {e}") # 可選擇是否拋出

    def _load_font(self):
        """載入用於顯示文字的字型。"""
        # 優先使用 PIL 的 ImageFont，因為它更適合靜態文字渲染
        font_size_small = max(10, int(self.height / 20))
        font_size_medium = max(14, int(self.height / 15))
        font_size_large = max(18, int(self.height / 12))
        font_path_pil = None
        
        common_font_files = ["wqy-microhei.ttc", "DroidSansFallbackFull.ttf", "DejaVuSans.ttf"]
        font_search_paths = ["/usr/share/fonts/truetype/wqy/", 
                               "/usr/share/fonts/truetype/droid/", 
                               "/usr/share/fonts/truetype/dejavu/"]

        for fname in common_font_files:
            if os.path.exists(fname):
                font_path_pil = fname
                break
            for path_prefix in font_search_paths:
                if os.path.exists(os.path.join(path_prefix, fname)):
                    font_path_pil = os.path.join(path_prefix, fname)
                    break
            if font_path_pil: break
        
        try:
            if font_path_pil:
                self.font_small_pil = ImageFont.truetype(font_path_pil, font_size_small)
                self.font_medium_pil = ImageFont.truetype(font_path_pil, font_size_medium)
                self.font_large_pil = ImageFont.truetype(font_path_pil, font_size_large)
                print(f"SpiLcdDisplay 使用 PIL 字型: {font_path_pil}")
            else:
                print("SpiLcdDisplay: 找不到指定的 TTF 字型，將使用預設點陣字型。")
                self.font_small_pil = ImageFont.load_default()
                self.font_medium_pil = ImageFont.load_default() # 預設可能只有一種大小
                self.font_large_pil = ImageFont.load_default()
        except Exception as e:
            print(f"SpiLcdDisplay: PIL 字型載入錯誤: {e}。將使用預設點陣字型。")
            self.font_small_pil = ImageFont.load_default()
            self.font_medium_pil = ImageFont.load_default()
            self.font_large_pil = ImageFont.load_default()

    def clear_display(self, color=None):
        """清除整個 LCD 螢幕。"""
        if not self.is_initialized or not self.disp:
            return
        bg_color_to_use = color if color is not None else self.DEFAULT_BG_COLOR
        image = Image.new("RGB", (self.width, self.height), bg_color_to_use)
        self.disp.image(image)

    def display_message(self, lines, text_color=BLACK, bg_color=None, font_size='medium', text_align='center', v_align='center'):
        """
        在 LCD 上顯示多行文字訊息。
        參數:
            lines (list of str): 要顯示的文字行列表。
            text_color (tuple): 文字顏色 (R, G, B)。
            bg_color (tuple, optional): 背景顏色。預設為 self.DEFAULT_BG_COLOR。
            font_size (str): 'small', 'medium', or 'large'。
            text_align (str): 'left', 'center', 'right'。
            v_align (str): 'top', 'center', 'bottom'。
        """
        if not self.is_initialized or not self.disp:
            print("錯誤: SpiLcdDisplay 未初始化，無法顯示訊息。")
            return

        bg_color_to_use = bg_color if bg_color is not None else self.DEFAULT_BG_COLOR
        image = Image.new("RGB", (self.width, self.height), bg_color_to_use)
        draw = ImageDraw.Draw(image)

        if font_size == 'large': current_font = self.font_large_pil
        elif font_size == 'small': current_font = self.font_small_pil
        else: current_font = self.font_medium_pil

        total_text_height = 0
        line_heights = []
        max_text_width = 0

        for line in lines:
            try:
                # 使用 textbbox 獲取精確的邊界框
                bbox = draw.textbbox((0,0), line, font=current_font)
                text_w = bbox[2] - bbox[0]
                text_h = bbox[3] - bbox[1]
            except AttributeError: # Pillow < 8.0.0 (textsize)
                text_w, text_h = draw.textsize(line, font=current_font)
            
            line_heights.append(text_h)
            total_text_height += text_h
            if text_w > max_text_width: max_text_width = text_w
        
        # 考慮行間距 (例如，行高的 20%)
        line_spacing = int(current_font.getbbox("A")[3] * 0.2) if hasattr(current_font, 'getbbox') else 2
        total_text_height += (len(lines) - 1) * line_spacing

        # 計算起始 Y 位置
        if v_align == 'top':
            current_y = 10 # 頂部留白
        elif v_align == 'bottom':
            current_y = self.height - total_text_height - 10 # 底部留白
        else: # center
            current_y = (self.height - total_text_height) // 2

        # 逐行繪製
        for i, line_text in enumerate(lines):
            try:
                bbox_line = draw.textbbox((0,0), line_text, font=current_font)
                text_w_line = bbox_line[2] - bbox_line[0]
            except AttributeError:
                text_w_line, _ = draw.textsize(line_text, font=current_font)

            if text_align == 'left':
                pos_x = 5 # 左側留白
            elif text_align == 'right':
                pos_x = self.width - text_w_line - 5 # 右側留白
            else: # center
                pos_x = (self.width - text_w_line) // 2
            
            draw.text((pos_x, current_y), line_text, font=current_font, fill=text_color)
            current_y += line_heights[i] + line_spacing

        self.disp.image(image)

    def display_game_results(self, score, final_mileage, reason_key):
        """以特定格式顯示遊戲結果。"""
        title = "遊戲結束"
        if reason_key == "collision": title = "你很菜"
        elif reason_key == "mileage_zero": title = "恭喜脫離苦海"
        elif reason_key == "quit_event": title = "已退出"

        lines_to_display = [
            title,
            f"價值: {score}",
            f"情緒: {final_mileage}"
        ]
        self.display_message(lines_to_display, font_size='medium', text_align='center', v_align='center')

    def show_standby_message(self, message="等待操作..."):
        """顯示待機訊息。"""
        self.clear_display()
        self.display_message([message], font_size='medium', text_align='center', v_align='center')

    def cleanup(self):
        """清理資源，例如關閉 LCD 背光。"""
        print("正在清理 SpiLcdDisplay 資源...")
        if self.is_initialized:
            self.clear_display(color=(0,0,0)) # 關閉前清成黑色
        if self.backlight_controller and hasattr(self.backlight_controller, 'value'):
            self.backlight_controller.value = False # 關閉背光
            print("LCD 背光已關閉。")

# --- 腳本執行 (測試用) ---
if __name__ == "__main__":
    print("SpiLcdDisplay 測試開始...")
    lcd = None
    try:
        lcd = SpiLcdDisplay(
            cs_pin_board=board.CE0, 
            dc_pin_board=board.D25, 
            rst_pin_board=board.D24, 
            backlight_pin_board=board.D27 # D27是樹莓派上的物理腳位22旁GPIO27
        )
        
        if lcd.is_initialized:
            print("LCD 初始化成功，開始測試訊息顯示...")
            lcd.display_message(["你好,", "SPI LCD!"], font_size='large', text_color=(255,0,0))
            pygame.time.wait(3000) # Pygame time 依賴 pygame.init()

            lcd.display_game_results(score=125, final_mileage=88, reason_key="collision")
            pygame.time.wait(3000)

            lcd.display_game_results(score=350, final_mileage=0, reason_key="mileage_zero")
            pygame.time.wait(3000)

            lcd.show_standby_message("系統準備就緒")
            pygame.time.wait(3000)
            
            lcd.display_message(["多行測試:", "第一行置中", "第二行也置中", "這是第三行"], font_size='small', v_align='center', text_align='center')
            pygame.time.wait(3000)
            
            lcd.display_message(["靠左測試", "文字在左邊"], font_size='medium', text_align='left', v_align='top', bg_color=(50,50,50), text_color=(200,200,0))
            pygame.time.wait(3000)

        else:
            print("LCD 初始化失敗，無法執行測試。")

    except RuntimeError as e:
        print(f"執行 SpiLcdDisplay 測試時發生錯誤: {e}")
    except KeyboardInterrupt:
        print("\nLCD 測試被使用者中斷。")
    finally:
        if lcd:
            lcd.cleanup()
        # Pygame 的 init/quit 應由主應用程式管理，但若測試需要 wait，則需確保初始化
        # if pygame.get_init(): pygame.quit() # 如果測試中有 pygame.init()
        print("SpiLcdDisplay 測試結束。") 