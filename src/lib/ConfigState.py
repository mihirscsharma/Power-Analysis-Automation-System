import time
from View import ConfigView        # View class to display each config item on OLED
from Scales import *               # Utilities to handle time scaling (ms, s, m, etc.)

class ConfigState:
    """ Manages 'Config Mode' where users can change settings using the touchpad """

    # --- constructor   --------------------------------------------------------

    def __init__(self, app):
        """ Initialize config screen views based on what is configurable """

        self._app = app

        # Headings to be shown on the screen for each setting
        headings = ['Int-Scale:', 'Interval:', 'Duration:', 'Update:']

        # Corresponding units or labels to display next to the values
        units = [
            "",                                     # No unit for Int-Scale
            app.settings.int_scale,                # Unit for Interval (e.g. ms)
            dur_scale(app.settings.int_scale),     # Unit for Duration (derived from interval scale)
            'ms'                                    # Update interval is in milliseconds
        ]

        # List of setting names that will be updated in app.settings
        self._attr = ['int_scale', 'interval', 'duration', 'update']

        # Optionally add "Oversample" if it's enabled
        if app.settings.oversample > 0:
            headings.append('Oversample:')
            units.append('X')                      # Unit for oversampling is multiplier
            self._attr.append('oversample')

        # Add sensor-specific config values, if any
        try:
            config_data = app.data_provider.get_config_data()
            for heading, attribute, unit in config_data:
                headings.append(heading)
                units.append(unit)
                self._attr.append(attribute)
        except Exception as ex:
            # In case the data provider doesn’t support config views
            print(f"exception creating provider-specific config-views: {ex}")
            pass

        # Create a ConfigView object for each setting
        self._views = [
            ConfigView(app.display, app.border, headings[i], units[i])
            for i in range(len(headings))
        ]

        # Cache views for interval and duration — they need unit adjustments if scale changes
        self._int_view = self._views[1]    # Interval view
        self._dur_view = self._views[2]    # Duration view

    # --- update a setting   ----------------------------------------------------

    def _upd_value(self, nr):
        """ Display and allow editing of a setting (via touchpad) """

        # Get the current value of this setting from app.settings
        value = str(getattr(self._app.settings, self._attr[nr]))

        while True:
            # Show the current value on the OLED
            self._views[nr].set_value(value)
            self._views[nr].show()

            # Wait for a touchpad keypress
            key = self._app.key_events.wait_for_key(self._app.key_events.KEYMAP_CONFIG)

            # If "Next" key is pressed, save and return
            if key == 'NEXT':
                if nr == 0:
                    # For int_scale, save as string
                    setattr(self._app.settings, self._attr[nr], value)
                    self._int_view.set_unit(value)                  # Update interval unit display
                    self._dur_view.set_unit(dur_scale(value))       # Update duration unit display
                else:
                    # For other settings, convert to integer
                    setattr(self._app.settings, self._attr[nr], int(value))
                return

            # If "CLR" key is pressed, remove a digit or reset to default
            elif key == 'CLR':
                if nr == 0:
                    value = 'ms'                                    # default for int_scale
                elif len(value) > 1:
                    value = value[:-1]                              # remove last digit
                else:
                    value = '0'                                     # reset

            # If current value is zero and key is a digit, replace value
            elif value == '0':
                value = key

            # Special case: if editing the interval scale (int_scale), pick from INT_SCALES
            elif nr == 0:
                index = min(int(key), len(INT_SCALES)) - 1
                value = list(INT_SCALES.items())[index][0]

            # Otherwise, append digit to current value (for numbers like 150, 1000, etc.)
            else:
                value = value + key

    # --- loop during config-state   --------------------------------------------

    def run(self):
        """ Iterate over all config items and let the user update them """

        if not self._app.display:
            return
        else:
            # Loop over each setting and allow the user to modify it
            for i in range(len(self._views)):
                self._upd_value(i)
