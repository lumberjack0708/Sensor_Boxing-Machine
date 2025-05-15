from xpt2046 import Touch
from gpiozero import Button, DigitalOutputDevice
import board
import busio
from time import sleep
from drawpoint import Draw_test
# touch callback
def touchscreen_press(coor):
    if coor!= None:
        y,x = coor
        return(320-x,240-y)

cs = DigitalOutputDevice(7,active_high=False,initial_value=None)
clk = board.SCLK_1		# same as writing 21
mosi = board.MOSI_1	# same as writing 20
miso = board.MISO_1	# same as writing 19
irq = Button(26)

spi = busio.SPI(clk, mosi, miso)	# auxiliary SPI

xpt = Touch(spi, cs=cs, int_pin=irq, int_handler=touchscreen_press,wait_time = 0.01)
draw_T = Draw_test((0,255,0),5)
#while True:
#    draw_T.Draw_Point(touchscreen_press(xpt.get_touch()))
#draw_T.Draw_Button((10,10),'test',20)
#draw_T.Draw_Button((10,200),'tessdsdt',20)
Question = 'Is Steven the most\nhandsome teacher in world?'
title = 'Question'
def no(x):
    global Question
    global title
    title = 'Answer'
    Question = 'Wrong'
def yes(x):
    global Question
    global title
    title = 'Answer'
    Question = 'Correct'
def render_view():
    draw_T.Draw_Lebel((10,20),title,20)
    draw_T.Draw_Lebel((10,100),Question,20)
    draw_T.Draw_Button((280,180),'X',40,fun=no)
    draw_T.Draw_Button((10,180),'O',40,fun=yes)
render_view()
while True:
    draw_T.Draw_Read(touchscreen_press(xpt.get_touch()),render = render_view)