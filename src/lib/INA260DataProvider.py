# ----------------------------------------------------------------------------
# INA260DataProvider.py: Read data from the INA260 sensor over I2C
# ----------------------------------------------------------------------------

import time
from adafruit_ina260 import ConversionTime, AveragingCount, INA260

# Optional feature: include power reading in output (3 values vs. 2)
WITH_POWER = False

# If no load is detected for this many seconds, stop measuring
NO_LOAD_TIMEOUT = 60

class DataProvider:
    """Provide voltage/current/power data from the INA260 sensor"""

    # Define output dimensions and format depending on WITH_POWER flag
    _dim   = 3 if WITH_POWER else 2
    _units = ['V', 'mA', 'mW']              # measurement units
    _fmt   = ["{1:.3f}", "{2:.3f}", "{3:.3f}"]  # format strings for CSV logging

    def __init__(self, i2c, settings):
        """Initialize the INA260 sensor and apply settings"""
        self._settings = settings

        # Set defaults if not already provided
        if not hasattr(self._settings, "ina260_count"):
            setattr(self._settings, "ina260_count", 16)  # averaging count
        if not hasattr(self._settings, "ina260_ctime"):
            setattr(self._settings, "ina260_ctime", 1)   # conversion time index

        # Initialize the INA260 chip using Adafruit library
        self._ina260 = INA260(i2c)

        self.reset()

    def _set_config_data(self):
        """Apply user configuration: averaging and conversion time"""

        # Validate and sanitize inputs
        if not hasattr(AveragingCount, f"COUNT_{self._settings.ina260_count}"):
            self._settings.ina260_count = 16
        if self._settings.ina260_ctime < 0 or self._settings.ina260_ctime > 7:
            self._settings.ina260_ctime = 1

        # Set averaging count (noise reduction, sampling time)
        self._ina260.averaging_count = getattr(
            AveragingCount, f"COUNT_{self._settings.ina260_count}"
        )

        # Define mapping of time index (0–7) to INA260 conversion time enums
        CONV_TIME = [
            ConversionTime.TIME_140_us,
            ConversionTime.TIME_204_us,
            ConversionTime.TIME_332_us,
            ConversionTime.TIME_588_us,
            ConversionTime.TIME_1_1_ms,
            ConversionTime.TIME_2_116_ms,
            ConversionTime.TIME_4_156_ms,
            ConversionTime.TIME_8_244_ms,
        ]

        # Set conversion time for both current and voltage channels
        ctime = CONV_TIME[self._settings.ina260_ctime]
        self._ina260.current_conversion_time = ctime
        self._ina260.voltage_conversion_time = ctime

    def get_config_data(self):
        """Returns config parameters to show on screen (ConfigState)"""
        return [
            ("AVG-Count", "ina260_count", ""),  # number of samples averaged
            ("Conv-Time", "ina260_ctime", ""),  # ADC conversion time
        ]

    def reset(self):
        """Reset state and apply new settings to INA260"""
        self._start = False
        self._set_config_data()

    def get_dim(self):
        """Return the number of data values produced per sample"""
        return DataProvider._dim

    def get_units(self):
        """Return measurement units for display/logging"""
        return DataProvider._units[:DataProvider._dim]

    def get_fmt(self):
        """Return format string for CSV-style logging"""
        return ','.join(DataProvider._fmt[:DataProvider._dim])

    def get_data(self):
        """Read one sample from INA260 and return it

        Will skip samples if below voltage/current thresholds.
        Ends measurement if values drop below threshold after start.
        """

        t_start = time.monotonic()  # start a timer to prevent infinite wait

        while True:
            # Read sensor data
            v = self._ina260.voltage           # in volts
            a = max(0, self._ina260.current)   # in mA (ensure non-negative)
            p = self._ina260.power             # in watts

            # Check if values exceed thresholds (start logging if so)
            if v >= self._settings.v_min and a >= self._settings.a_min:
                self._start = True
                return (v, a, 1000*p) if WITH_POWER else (v, a)

            elif self._start:
                # If logging already started, stop when load disappears
                raise StopIteration

            elif time.monotonic() - t_start > NO_LOAD_TIMEOUT:
                # If load never appears, give up after timeout
                raise StopIteration
