import digitalio
import board
from PIL import Image, ImageDraw
from adafruit_rgb_display import ili9341

# 設定顯示器腳位
cs_pin = digitalio.DigitalInOut(board.CE0)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = digitalio.DigitalInOut(board.D24)
backlight = digitalio.DigitalInOut(board.D27)
backlight.switch_to_output()
backlight.value = True
BAUDRATE = 24000000

# 初始化 SPI 與螢幕
spi = board.SPI()
disp = ili9341.ILI9341(
    spi,
    rotation=270,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
)

# 計算螢幕尺寸
if disp.rotation % 180 == 90:
    height = disp.width
    width = disp.height
else:
    width = disp.width
    height = disp.height

# 讀取同資料夾下的照片（絕對路徑）
image = Image.open("/home/pi/RandomGenerate/SPI/image20250401v3.jpg")  # ← 絕對路徑圖片位置

# 縮放圖片以符合螢幕
image_ratio = image.width / image.height
screen_ratio = width / height
if screen_ratio < image_ratio:
    scaled_width = image.width * height // image.height
    scaled_height = height
else:
    scaled_width = width
    scaled_height = image.height * width // image.width
image = image.resize((scaled_width, scaled_height), Image.BICUBIC)

# 裁切並置中圖片
x = scaled_width // 2 - width // 2
y = scaled_height // 2 - height // 2
image = image.crop((x, y, x + width, y + height))

# 顯示圖片
disp.image(image)