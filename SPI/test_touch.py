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
while True:
#    draw_T.Draw_Point(touchscreen_press(xpt.get_touch())) #draw
    print(touchscreen_press(xpt.get_touch()))