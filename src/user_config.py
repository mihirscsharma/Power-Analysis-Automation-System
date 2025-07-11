# user_config.py: Configuration for ESP32 + INA260 + OLED + Touchpad + Serial logging

from INA260DataProvider import DataProvider       # Sensor: INA260
from SerialLogger import DataLogger               # Logger: USB Serial

import board

# --- I2C Pin Overrides 
PIN_SDA = board.IO21     # Your board's SDA pin
PIN_SCL = board.IO22     # Your board's SCL pin

# --- Display Settings ---
DEF_DISPLAY = 'ssd1306'  # Force SSD1306 OLED
DEF_TP_ORIENT = 'P'      # Touchpad orientation: 'P' (portrait) or 'L' (landscape)

