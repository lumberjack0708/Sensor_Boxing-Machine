import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
from adafruit_rgb_display import ili9341

nothing = lambda nothing:print('screen')
class Draw_test():
    def __init__(self,color,radius):
        
        self.color = color
        self.radius = radius
        self.cs_pin = digitalio.DigitalInOut(board.CE0)
        self.dc_pin = digitalio.DigitalInOut(board.D25)
        self.reset_pin = digitalio.DigitalInOut(board.D24)
        self.backlight = digitalio.DigitalInOut(board.D27)
        self.backlight.switch_to_output()
        self.backlight.value = True
        self.BAUDRATE = 24000000
        self.spi = board.SPI()
        self.disp = ili9341.ILI9341(
            self.spi,
            rotation=270,  # 2.2", 2.4", 2.8", 3.2" ILI9341
            cs=self.cs_pin,
            dc=self.dc_pin,
            rst=self.reset_pin,
            baudrate=self.BAUDRATE,
        )
        if self.disp.rotation % 180 == 90:
            self.height = self.disp.width  # we swap height/width to rotate it to landscape!
            self.width = self.disp.height
        else:
            self.width = self.disp.width  # we swap height/width to rotate it to landscape!
            self.height = self.disp.height
        self.screen_event = [[nothing for i in range(self.height)] for i in range(self.width)]
        self.image = Image.new("RGB", (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)

    def Draw_Point(self,coor):
        if coor!= None:
            X,Y = coor
            self.draw.ellipse((X-self.radius,Y-self.radius,X+self.radius,Y+self.radius),fill=self.color)
            self.disp.image(self.image)
    def Draw_Button(self,coor,text,fontSize=20,color=(0,0,0),background=(255,255,255),
                    fun=lambda x:print('init Button')):
        fnt = ImageFont.truetype("Pillow/Tests/fonts/FreeMono.ttf", fontSize)
        
        self.draw.rectangle((coor, coor[0]+len(text)*fontSize, coor[1]+int(fontSize*1.5)), outline=1, fill=background)
        self.draw.text((coor[0]+len(text)*int(fontSize/5),coor[1]+int(fontSize/3)),text,font=fnt,fill=color)
        self.disp.image(self.image)
        for x in range(coor[0],coor[0]+len(text)*fontSize):
            for y in range(coor[1],coor[1]+int(fontSize*1.5)):
                try:
                    self.screen_event[x][y] = fun
                except:
                    pass
    def Draw_Lebel(self,coor,text,fontSize=20,color=(255,255,255)):
        fnt = ImageFont.truetype("Pillow/Tests/fonts/FreeMono.ttf", fontSize)
        self.draw.text(coor,text,font=fnt,fill=color)
        self.disp.image(self.image)
    def Draw_Read(self,coor,render):
        if coor!= None:
            X,Y = coor
            self.screen_event[X][Y](0)
            self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=(0, 0, 0))
            self.disp.image(self.image)
            render()
            