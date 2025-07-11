# ----------------------------------------------------------------------------
# FakeDataProvider.py: Emulates a real sensor for testing purposes
# ----------------------------------------------------------------------------

import time       # Used for timing and delays
import math       # Used to generate sine/cosine waveforms for fake data

# Choose how many values the fake sensor should return:
# DIM = 2: simulate [Voltage, Current]
# DIM = 3: simulate [Voltage1, Voltage2, Current]
DIM = 3

class DataProvider:
    """ Fake sensor data provider for simulation/testing. Mimics INA219 behavior. """

    def __init__(self, i2c, settings):
        """ Initialize provider with user settings (doesn't use I2C here) """
        self._settings = settings
        self.reset()

    def reset(self):
        """ Reset internal start timestamp to None """
        self._start = None

    def get_dim(self):
        """ Return the number of data channels (2 or 3) """
        return DIM

    def get_units(self):
        """ Return units for each data channel """
        if DIM == 2:
            return ['V', 'mA']          # Voltage, Current
        else:
            return ['V', 'V', 'mA']     # Voltage1, Voltage2, Current

    def get_fmt(self):
        """ Return string format for logging each sample """
        if DIM == 2:
            return "{1:.2f},{2:.1f}"     # e.g., 5.00, 100.0
        else:
            return "{1:.2f},{2:.1f},{3:.1f}"  # e.g., 1.25, 5.10, 100.0

    def get_data(self):
        """
        Generate a fake data sample using sine/cosine waves.
        Simulates real-time sampling by sleeping briefly.
        """
        time.sleep(0.01)  # simulate real sensor read delay
        t = time.monotonic()

        # Save starting time on first run
        if not self._start:
            self._start = t

        # Stop after 60 seconds if duration == 0 (unlimited mode)
        if self._settings.duration == 0 and t > self._start + 60:
            raise StopIteration

        # Return either 2 or 3 values depending on DIM
        if DIM == 2:
            return (
                5 + t / 10 + math.sin(t),      # fake voltage: ~5V + slow variation
                25 + t / 10 + math.cos(t)      # fake current: ~25mA + slow variation
            )
        else:
            return (
                1 + t / 100 + math.sin(t),     # fake low voltage
                5 + t / 10 + math.sin(t),      # main voltage
                25 + t / 10 + math.cos(t)      # current
            )
