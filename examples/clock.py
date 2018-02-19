#!/usr/bin/env python2
#
# Draws a clock to the Adafruit SSD1306
#
# Author:  Daniel Mikusa <dan@mikusa.com>
#   Date:  2018-02-18
#
# To run with the default font:
#  python clock.py
#
# To run with a custom font:
#  FONT=path/to/my/font.ttf python clock.py
#
from datetime import datetime

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from PIL import ImageOps

import threading
import time
import signal
import os
import Adafruit_SSD1306


def find_optimal_font_size(draw, time, font_path,
                           width, height, initial_size=10, padding=2):
    # iterate through until we find the largest font
    #   that fits within (width x height)
    font_size = initial_size
    font = ImageFont.truetype(font_path, font_size)
    (w, h) = draw.textsize(time, font=font)
    while w < (width - 2 * padding) and h < (height - 2 * padding):
        font_size += 1
        font = ImageFont.truetype(font_path, font_size)
        (w, h) = draw.textsize(time, font=font)
    return font_size - 1  # return previous because we've overshot by one


def draw_img(width, height, time, font_path=None):
    # Create blank image for drawing.
    # Make sure to create image with mode '1' for 1-bit color.
    image = Image.new('1', (width, height))

    # Get drawing object to draw on image.
    draw = ImageDraw.Draw(image)

    # Draw a black filled box to clear the image.
    draw.rectangle((0, 0, width, height), outline=0, fill=0)

    # Load default font.
    if font_path is None:
        font = ImageFont.load_default()
    else:
        # Alternatively load specific font & size.
        #
        # Some nice choices are...
        #  - https://www.dafont.com/vcr-osd-mono.font
        #  - https://www.dafont.com/alarm-clock.font
        #
        font_size = find_optimal_font_size(draw, time,
                                           font_path, width, height)
        font = ImageFont.truetype(font_path, font_size)

    # Center the text
    (w, h) = draw.textsize(time, font=font)
    x = (width - w) / 2
    y = (height - h) / 2

    # Write the time
    draw.text((x, y), time,  font=font, fill=255)

    return image


def init_ssd1306():
    # Raspberry Pi pin configuration:
    RST = 24

    # Beaglebone Black pin configuration:
    # RST = 'P9_12'

    # 128x32 display with hardware I2C:
    disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST)

    # 128x64 display with hardware I2C:
    # disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST)

    # Initialize library.
    disp.begin()

    # Clear display.
    disp.clear()
    disp.display()

    return disp


class UpdateTimer(threading.Thread):
    def __init__(self, display):
        threading.Thread.__init__(self)
        self.display = display
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def run(self):
        font_path = os.environ.get('FONT', None)
        while not self.stopped():
            # timestr = datetime.now().strftime("%H:%M")  # 24-hour
            timestr = datetime.now().strftime("%I:%M %p")  # AM/PM
            img = ImageOps.flip(
                ImageOps.mirror(
                    draw_img(disp.width, disp.height, timestr, font_path)))
            disp.image(img)
            disp.display()
            time_left = 60 - datetime.now().second + 1
            # could use time.sleep for the whole interval
            #   but this makes it easier to stop this thread
            while time_left > 0:
                time.sleep(5.0)
                time_left -= 5
                if time_left < 0 or self.stopped():
                    time_left = 0


if __name__ == '__main__':
    disp = init_ssd1306()
    t = UpdateTimer(None)
    try:
        t.start()
        signal.pause()
    except (KeyboardInterrupt, SystemExit):
        t.stop()
