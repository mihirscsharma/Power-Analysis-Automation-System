# ----------------------------------------------------------------------------
# Touchpad.py: provide key-events using a MPR121-based 4x3 touchpad

import time
import adafruit_mpr121  # Adafruit library to interface with MPR121 capacitive touch controller

class KeyEventProvider:
    """Provides key events from a capacitive touchpad (MPR121)."""

    DEBOUNCE_TIME = 0.200  # Minimum time between valid touches (200ms)

    # --- Keymaps: Button index → key label mappings ---

    # Portrait orientation: used if settings.tp_orient == 'P'
    KEYMAP_READY_P = {0: 'START', 4: 'CONFIG', 6: 'TOGGLE', 8: 'EXIT'}
    KEYMAP_ACTIVE_P = {8: 'STOP', 6: 'TOGGLE'}
    KEYMAP_CONFIG_P = {
        0: 'NEXT', 4: '0', 8: 'CLR',
        1: '7',    5: '8', 9: '9',
        2: '4',    6: '5', 10: '6',
        3: '1',    7: '2', 11: '3'
    }
    KEYMAP_SHIFT_P = {0: 'NEXT', 4: 'SHIFT', 8: 'CLR', 5: '0', 9: '.'}

    # Landscape orientation: used if settings.tp_orient == 'L'
    KEYMAP_READY_L = {8: 'START', 4: 'CONFIG', 6: 'TOGGLE', 0: 'EXIT'}
    KEYMAP_ACTIVE_L = {0: 'STOP', 6: 'TOGGLE'}
    KEYMAP_CONFIG_L = {
        11: '1', 10: '2', 9: '3', 8: 'NEXT',
         7: '4',  6: '5', 5: '6', 4: '0',
         3: '7',  2: '8', 1: '9', 0: 'CLR'
    }
    KEYMAP_SHIFT_L = {8: 'NEXT', 4: 'SHIFT', 0: 'CLR', 2: '0', 1: '.'}

    def __init__(self, i2c, settings):
        """Initialize the MPR121 device and load correct keymap"""
        self._settings = settings
        self._mpr121 = adafruit_mpr121.MPR121(i2c)  # Connect MPR121 over I2C
        self._last_key = (-1, time.monotonic())  # For debounce checking

        # Load keymaps depending on keypad orientation
        if settings.tp_orient == 'L':  # Landscape
            self.KEYMAP_READY = self.KEYMAP_READY_L
            self.KEYMAP_ACTIVE = self.KEYMAP_ACTIVE_L
            self.KEYMAP_CONFIG = self.KEYMAP_CONFIG_L
            self.KEYMAP_SHIFT = self.KEYMAP_SHIFT_L
        else:  # Portrait (default)
            self.KEYMAP_READY = self.KEYMAP_READY_P
            self.KEYMAP_ACTIVE = self.KEYMAP_ACTIVE_P
            self.KEYMAP_CONFIG = self.KEYMAP_CONFIG_P
            self.KEYMAP_SHIFT = self.KEYMAP_SHIFT_P

    def _get_key(self):
        """Internal method: return key index if touched, else None (with debounce)"""
        touched = self._mpr121.touched_pins  # List of bools for all 12 pads
        if True not in touched:
            return None

        index = touched.index(True)
        now = time.monotonic()

        # Debounce: ignore repeated presses within 200 ms
        if index == self._last_key[0] and now < (self._last_key[1] + self.DEBOUNCE_TIME):
            return None
        else:
            self._last_key = (index, now)
            return index

    def wait_for_key(self, keymap):
        """Block until a valid key from the given keymap is pressed"""
        normal_keymap = keymap
        shift = False

        while True:
            index = self._get_key()
            if index not in keymap:
                continue  # Ignore invalid keys or no touch

            if keymap[index] != 'SHIFT':
                return keymap[index]  # Return mapped key
            else:
                # Toggle between normal and shift layout
                shift = not shift
                keymap = self.KEYMAP_SHIFT if shift else normal_keymap

    def is_key_pressed(self, keymap):
        """Check once whether a key is pressed; return key if valid or None"""
        index = self._get_key()
        return keymap[index] if index in keymap else None
