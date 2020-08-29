import time
import neopixel
from adafruit_featherwing import minitft_featherwing
from adafruit_hid.gamepad import Gamepad
from adafruit_display_shapes.rect import Rect
from adafruit_display_shapes.circle import Circle
from adafruit_display_shapes.triangle import Triangle
from adafruit_display_shapes.polygon import Polygon
import displayio
import usb_hid
import board

minitft = minitft_featherwing.MiniTFTFeatherWing()
gp = Gamepad(usb_hid.devices)
display = minitft.display

joystick_mode = False
joy_y = 0
joy_x = 0
delta = -6          # Change to joystick position for each button press
washout = 0.9       # Rate at which joystick returns to neutral (lower is faster)

pixel = neopixel.NeoPixel(
    board.NEOPIXEL, 1, brightness=0.5, auto_write=False, pixel_order=neopixel.GRB
)

pixel_index = 0

canvas = displayio.Group(max_size=25)
scale = displayio.Group(max_size=5)
pointer = displayio.Group(max_size=2, x=102, y=35)
display.show(canvas)

select = Rect(25, 28, 23, 23, fill=0x0, outline=0xFFFFFF, stroke=1)
up = Triangle(25, 23, 35, 7, 47, 23, fill=0x0, outline=0xFFFFFF)
down = Triangle(24, 55, 36, 72, 47, 55, fill=0x0, outline=0xFFFFFF)
left = Triangle(0, 39, 19, 28, 19, 50, fill=0x0, outline=0xFFFFFF)
right = Triangle(53, 28, 53, 50, 72, 39, fill=0x0, outline=0xFFFFFF)
a = Rect(150, -1, 11, 35, fill=0x0, outline=0xFFFFFF, stroke=1)
b = Rect(150, 45, 11, 36, fill=0x0, outline=0xFFFFFF, stroke=1)

### ONLY FOR JOYSTICK SIMULATION
points = [ (0, 6), (12, 6), (6, 6), (6, 0), (6, 12), (6, 6), ]
points_abs = [ (102, 41), (114, 41), (108, 41), (108, 35), (108, 47), (108, 41), ]
joystick_zero = Polygon(points_abs, outline=0xA9A9A9)
joystick_pointer = Polygon(points, outline=0xFFFFFF)
pointer_background = Rect(83, 10, 50, 60, fill=0x404040, outline=0xA9A9A9, stroke=1)

canvas.append(up)
canvas.append(down)
canvas.append(left)
canvas.append(right)
canvas.append(a)
canvas.append(b)
canvas.append(select)

### ONLY FOR JOYSTICK SIMULATION
scale.append(pointer_background)
scale.append(joystick_zero)
pointer.append(joystick_pointer)

canvas.append(scale)
scale.append(pointer)

def wheel(pos):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        r = g = b = 0
    elif pos < 85:
        r = int(pos * 3)
        g = int(255 - pos * 3)
        b = 0
    elif pos < 170:
        pos -= 85
        r = int(255 - pos * 3)
        g = 0
        b = int(pos * 3)
    else:
        pos -= 170
        r = 0
        g = int(pos * 3)
        b = int(255 - pos * 3)
    return (g, r, b)

def map_joystick_pointer(joy_x, joy_y):
    # Maps the actual joystick coordinates to a 
    # display position 
    x_offset = 102
    y_offset = 35
    x_pos = joy_x * 0.197 + x_offset
    y_pos = joy_y * 0.236 + y_offset
    return x_pos, y_pos

def limit(joy_x, joy_y, delta_x, delta_y):
    # Returns true if the predicted movement will
    # exceed position limits (-127 > x > 127)
    if (joy_y + delta_y < -127) or (joy_y + delta_y > 127):
        return True
    if (joy_x + delta_x < -127) or (joy_x + delta_x > 127):
        return True
    else:
        return False 


while True:
    buttons = minitft.buttons

    if not joystick_mode:
        joystick_pointer.fill = 0xA0A0A0

    if (not buttons.up) and (not buttons.down):
            if joy_y > 1 or joy_y < -1:
                joy_y = joy_y * washout
    if (not buttons.left) and (not buttons.right):        
            if joy_x > 1 or joy_x < -1:
                joy_x = joy_x * washout  

    for i, button in enumerate(buttons):
        gamepad_button_num = i + 1
        if not button:
            shape = canvas[i]
            shape.fill=0x707070
            gp.release_buttons(gamepad_button_num)

        else:
            shape = canvas[i]
            shape.fill=0xFF00FF

            if buttons.a:
                joystick_mode = not joystick_mode
                if joystick_mode:
                    joystick_pointer.outline = 0xFF00FF
                    pointer_background.outline = 0xFF00FF
                else:
                    joystick_pointer.outline = 0xA9A9A9
                    pointer_background.outline = 0xA9A9A9
                ### inhibit changes for a short period
                time.sleep(0.3)

            if joystick_mode:
                gp.press_buttons(gamepad_button_num)

                if buttons.left:
                    if not limit(joy_x, joy_y, delta, 0):
                        joy_x = joy_x + delta
                if buttons.right:
                    if not limit(joy_x, joy_y, abs(delta), 0):
                        joy_x = joy_x + abs(delta)
                if buttons.down:
                    if not limit(joy_x, joy_y, 0, abs(delta)):
                        joy_y = joy_y + abs(delta)
                if buttons.up:  
                    if not limit(joy_x, joy_y, 0, delta):
                        joy_y = joy_y + delta 

                gp.move_joysticks(x=int(joy_x), y=int(joy_y))         

            else:
                if buttons.left:
                    pixel_index = pixel_index + 10
                if buttons.right:
                    pixel_index = pixel_index - 10
                if buttons.down & (pixel.brightness > 0):
                    pixel.brightness = pixel.brightness - 0.05
                if buttons.up & (pixel.brightness < 1):  
                    pixel.brightness = pixel.brightness + 0.05   

    # Display housekeeping
    display_pos = map_joystick_pointer(joy_x, joy_y)
    pointer.x = int(display_pos[0])
    pointer.y = int(display_pos[1])
    
    # Neopixel housekeeping
    pixel[0] = wheel(pixel_index & 255)
    pixel.show()
    time.sleep(0.05) 
