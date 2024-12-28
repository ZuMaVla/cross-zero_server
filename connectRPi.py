from sense_hat import SenseHat
sense = SenseHat()

def set_pixel(x, y, color):
    global virtual_display, flat_pixels
    virtual_display[y][x] = color
    flat_pixels = [pixel for row in virtual_display for pixel in row]
    
virtual_display = [[(0, 0, 0) for _ in range(8)] for _ in range(8)]
set_pixel(3, 3, (255, 0, 0))
sense.set_pixels(flat_pixels)
