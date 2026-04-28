from lib import display
from lib.hydra.config import Config
from lib.userinput import UserInput
from font import vga1_8x16 as font
import time

cfg = Config()
tft = display.Display(use_tiny_buf=True)
kb = UserInput()

text = "SYNC NOTES"

def draw():
    tft.fill(cfg.palette[2])
    tft.text("Notes demo", 8, 8, cfg.palette[8], font=font)
    tft.text(text[:28], 8, 32, cfg.palette[8], font=font)
    tft.text("ESC/Q = exit", 8, 104, cfg.palette[8], font=font)
    tft.show()

draw()

while True:
    keys = [str(k).upper() for k in kb.get_new_keys()]
    if "ESC" in keys or "Q" in keys:
        break
    if keys:
        text = "KEY: " + ",".join(keys)[:22]
        draw()
    time.sleep_ms(100)
