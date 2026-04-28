from lib import display
from lib.hydra.config import Config
from lib.userinput import UserInput
from font import vga1_8x16 as font
import time

cfg = Config()
tft = display.Display(use_tiny_buf=True)
kb = UserInput()

tft.fill(cfg.palette[2])
tft.text("HELLO Z SYNC", 8, 20, cfg.palette[8], font=font)
tft.text("Plik z serwera", 8, 42, cfg.palette[8], font=font)
tft.text("ESC/Q = exit", 8, 64, cfg.palette[8], font=font)
tft.show()

while True:
    keys = [str(k).upper() for k in kb.get_new_keys()]
    if "ESC" in keys or "Q" in keys:
        break
    time.sleep_ms(100)
