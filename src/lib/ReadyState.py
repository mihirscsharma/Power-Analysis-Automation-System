# ----------------------------------------------------------------------------
# ReadyState.py: Handle ready-state, i.e. display last results and enter
#                config or run-state depending on button input
# ----------------------------------------------------------------------------

import board       # Used to detect if we're running under Blinka (PC simulation)
import time        # For delays and timing
from View import ResultView  # Imports the view class to show results on the display

class ReadyState:
    """Manage the 'ready' state — display results and handle next action."""

    def __init__(self, app):
        """Constructor: Initialize result views."""
        self._app = app         # Reference to main app controller
        self._views = []        # List of views to display results (e.g., voltage, current)

        # Get the measurement units from the data provider (e.g., ['V', 'A'])
        units = app.data_provider.get_units()

        # Create one ResultView per unit (for showing last results)
        for unit in units:
            self._views.append(ResultView(app.display, app.border, unit))

    def run(self, active, config):
        """
        Main loop during ready-state.

        Displays last results and waits for user to choose:
        - START: begin new measurement
        - CONFIG: enter settings menu
        - EXIT: exit app (only on PC)
        - Other: toggle view
        """
        if not self._app.display:
            # If no display is attached, skip ready state
            return active

        # If plots are enabled and the number of values matches views,
        # extend the view list to include plot views from last session
        if (self._app.settings.plots and self._app.settings.update and
            len(self._views) == len(self._app.results.values)):
            self._views.extend(self._app.results.plots)

        # Show all results on the result views
        cur_view = 0                      # Start with the first view
        n_views = len(self._views)       # Total number of views
        for index, result in enumerate(self._app.results.values):
            self._views[index].set_values(*result)  # Set the data to each view
        self._views[cur_view].show()     # Display the first view

        # Main key-handling loop
        while True:
            if not self._app.key_events:
                # If there are no buttons (e.g., in Blinka on PC)

                # If running under Blinka and 'exit' flag is set, quit
                if hasattr(board, '__blinka__') and self._app.settings.exit:
                    return None
                else:
                    # Otherwise, auto-cycle views every 2 seconds
                    key = 'VIEW'
                    time.sleep(2)
            else:
                # Wait for a button press using the KEYMAP_READY mapping
                key = self._app.key_events.wait_for_key(
                    self._app.key_events.KEYMAP_READY
                )

            # Handle the pressed key
            if key == 'START':
                return active       # Go to ActiveState (start measurement)
            elif key == 'CONFIG':
                return config       # Go to ConfigState (change settings)
            elif key == 'EXIT':
                if hasattr(board, '__blinka__'):
                    return None     # Exit program (only allowed under Blinka)
                else:
                    continue        # Ignore EXIT key on physical devices
            else:
                # Rotate to the next view (wrap around)
                cur_view = (cur_view + 1) % n_views
                self._views[cur_view].show()
                time.sleep(0.1)     # Small delay to debounce button
