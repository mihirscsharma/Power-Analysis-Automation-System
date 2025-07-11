# ----------------------------------------------------------------------------
# ActiveState.py: Handles real-time measurement display, logging, and user input

#ActiveState is a state class in the app’s internal state machine.

#It controls:

#Collecting data from the sensor

#Displaying values and plots on the OLED

#Logging data

#Handling keypad events (e.g., stop/toggle)

#Running everything asynchronously using asyncio


# ----------------------------------------------------------------------------

import gc
import time
import sys
import asyncio
from View import ValuesView, PlotView              # for rendering to OLED
from Data import DataAggregator                    # collects min/mean/max
from Scales import *                               # unit scaling utilities

class ActiveState:
    """Manages 'active' state: live measurement collection + display."""

    def __init__(self, app):
        """Initialize ActiveState with app context."""
        self._app = app
        self._settings = app.settings
        self._logger = app.logger
        self._dim = app.data_provider.get_dim()  # number of data values (e.g., 2 or 3)

        self._stop = False          # global flag to stop tasks
        self._new_sample = False    # becomes True when a new sample is available

        # Set up display views
        if self._app.display:
            # View 0: live voltage/current/power
            self._views = [ValuesView(app.display, app.border,
                                      app.data_provider.get_units()),
                           # View 1: elapsed time
                           ValuesView(app.display, app.border, ['s', 's'])]

            # Add optional sparkline plots (one per unit)
            if self._settings.plots:
                for unit in app.data_provider.get_units():
                    plot = PlotView(app.display, app.border, [unit])
                    self._views.append(plot)
                    app.results.plots.append(plot)

    def _get_data(self):
        """Reads data from sensor with optional oversampling."""
        if self._settings.oversample < 2:
            return (time.monotonic(), self._app.data_provider.get_data())

        d_sum = [0 for _ in range(self._dim)]
        for _ in range(self._settings.oversample):
            data = self._app.data_provider.get_data()
            for i in range(self._dim):
                d_sum[i] += data[i]
        averaged = [d_sum[i] / self._settings.oversample for i in range(self._dim)]
        return time.monotonic(), averaged

    async def _check_key(self):
        """Monitor touchpad keys during measurement."""
        if not self._app.key_events:
            return

        while not self._stop:
            key = self._app.key_events.is_key_pressed(self._app.key_events.KEYMAP_ACTIVE)
            if key == 'TOGGLE' and self._app.display:
                self._cur_view = (self._cur_view + 1) % len(self._views)
            elif key == 'STOP':
                self._stop = True
                return
            await asyncio.sleep(0.1)

    def _update_views(self):
        """Updates the display contents based on current values."""
        if self._app.display and self._settings.update:
            # Update plots if enabled
            if self._new_sample and self._settings.plots:
                for i, value in enumerate(self.data_v):
                    self._views[2 + i].set_values([value])

            # View 0: values, View 1: elapsed time
            if self._new_sample and self._cur_view == 0:
                self._views[self._cur_view].set_values(
                    self.data_v, time.monotonic() - self._start_t)
            elif self._cur_view == 1:
                self._views[self._cur_view].set_values(
                    [(time.monotonic() - self._start_t) / self._dur_fac,
                     self._settings.duration], -1)

    async def _show_view(self):
        """Controls screen refresh timing and rendering."""
        if not (self._app.display and self._settings.update):
            return

        cur_view = self._cur_view
        update_time = 0.33  # estimated OLED refresh time (sec)

        while not self._stop:
            await asyncio.sleep(self._settings.update / 1000)
            gap = self._next_sample_t - time.monotonic()

            # Skip updating screen if a sample is due soon
            if gap < update_time and update_time < self._int_t:
                await asyncio.sleep(gap + 0.01)

            s = time.monotonic()
            self._update_views()

            if (self._new_sample or
                not self._app.key_events or
                self._cur_view == 1 or
                cur_view != self._cur_view):
                self._views[self._cur_view].show()
                cur_view = self._cur_view
                update_time = time.monotonic() - s

            self._new_sample = False

            # Auto-rotate through views if no keypad
            if not self._app.key_events:
                self._cur_view = (self._cur_view + 1) % len(self._views)

    def run(self):
        """Synchronous wrapper to initialize and launch async _run()."""
        self._stop = False
        self._int_fac = int_fac(self._settings.int_scale)
        self._dur_fac = dur_fac(self._settings.int_scale)
        self._int_t = self._settings.interval * self._int_fac  # seconds

        # Reset views
        if self._app.display:
            self._cur_view = 0
            self._views[0].clear_values()
            self._views[0].show()

            d_scale = dur_scale(self._settings.int_scale)
            self._views[1].set_units([d_scale, d_scale])

            if self._settings.plots:
                for i in range(self._dim):
                    self._views[2 + i].reset()

        gc.collect()
        asyncio.run(self._run())

    async def _run(self):
        """Async loop that performs sampling, logging, and screen updates."""
        key_task = asyncio.create_task(self._check_key())
        view_task = asyncio.create_task(self._show_view())

        self._logger.open()
        self._logger.log_settings()
        m_data = DataAggregator(self._dim)

        self._app.data_provider.reset()
        try:
            self._app.data_provider.get_data()
        except:
            print("\n#data-provider timed out")
            return

        if self._settings.duration:
            end_t = time.monotonic() + self._settings.duration * self._dur_fac
        else:
            end_t = sys.maxsize

        data_t_last = 0
        self._start_t = time.monotonic()
        samples = 0

        # Main sampling loop
        while not self._stop and time.monotonic() < end_t:
            if data_t_last > 0:
                sleep_t = max(self._int_t - (time.monotonic() - data_t_last), 0)
                self._next_sample_t = time.monotonic() + sleep_t
                while sleep_t:
                    if sleep_t > 1:
                        await asyncio.sleep(1)
                        if self._stop:
                            break
                        sleep_t -= 1
                    else:
                        await asyncio.sleep(sleep_t)
                        break
                if self._stop:
                    break

            try:
                data_t_last = time.monotonic()
                self.data_t, self.data_v = self._get_data()
                self._new_sample = True
                self._logger.log_values(self.data_t, self.data_v)
                m_data.add(self.data_v)
                samples += 1
            except StopIteration:
                self._stop = True
                break

        # Save final results
        self._app.results.time = self.data_t - self._start_t
        self._app.results.samples = samples
        self._app.results.values = m_data.get()

        self._logger.log_summary(samples)
        self._logger.close()
        self._stop = True
        await asyncio.gather(key_task, view_task)