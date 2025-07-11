# ----------------------------------------------------------------------------
# View.py: Various views for the 128x64 OLED screen (text and plot rendering)
# ----------------------------------------------------------------------------

import displayio
import terminalio
from adafruit_display_text import label
from adafruit_bitmap_font import bitmap_font
from adafruit_display_shapes.rect import Rect
from adafruit_display_shapes.sparkline import Sparkline

# --- Base class for all views (text rendering, formatting, positioning) ----

class View:
  FONT_T = terminalio.FONT  # Tiny font
  FONT_S = bitmap_font.load_font("fonts/DejaVuSansMono-Bold-18-min.pcf")  # Small
  FONT_L = bitmap_font.load_font("fonts/DejaVuSansMono-Bold-32-min.pcf")  # Large
  FG_COLOR = 0xFFFFFF  # White foreground

  def __init__(self, display, border):
    """Initialize view with display and optional border"""
    self._display = display
    self._border = 1
    if display:
      self._group = displayio.Group()
      self._offset = border + 2 if border else 0

      # If display is larger than 128x64, center it
      off_w = (display.width - 128) / 2
      off_h = (display.height - 64) / 2

      # Define anchor positions for text
      self._pos_map = {
        'NW': ((0.0, 0.0), (self._offset + off_w, self._offset + off_h)),
        'NE': ((1.0, 0.0), (display.width - self._offset - off_w, self._offset + off_h)),
        'W':  ((0.0, 0.5), (self._offset + off_w, display.height / 2)),
        'E':  ((1.0, 0.5), (display.width - self._offset - off_w, display.height / 2)),
        'SW': ((0.0, 1.0), (self._offset + off_w, display.height - self._offset - off_h)),
        'SE': ((1.0, 1.0), (display.width - self._offset - off_w, display.height - self._offset - off_h)),
      }

      # Optional border around screen
      if border:
        rect = Rect(0, 0, display.width, display.height,
                    fill=None, outline=View.FG_COLOR, stroke=border)
        self._group.append(rect)

  def add(self, text, pos, font):
    """Add a label at a predefined position with a given font"""
    if self._display:
      t = label.Label(font, text=text, color=View.FG_COLOR,
                      anchor_point=self._pos_map[pos][0])
      t.anchored_position = self._pos_map[pos][1]
      self._group.append(t)
      return t
    return None

  def format(self, value, unit):
    """Format a float with appropriate precision and unit suffix"""
    if value < 10:
      fmt = "{0:4.2f}{1:s}"
      value = round(value, 2)
    elif value < 100:
      fmt = "{0:4.1f}{1:s}"
      value = round(value, 1)
    else:
      fmt = "{0:3.0f}{1:s}"
      value = round(value, 0)
    return fmt.format(value, unit)

  def show(self):
    """Show this view on the display"""
    if self._display:
      self._display.show(self._group)
      self._display.refresh()

# ----------------------------------------------------------------------------
# View to show live values (voltage, current, power)

class ValuesView(View):
  def __init__(self, display, border, units):
    """Create a view to show up to 3 current values"""
    super().__init__(display, border)
    if self._display:
      self._value = []
      if len(units) < 3:
        pos = ['NE', 'SE']
        font = View.FONT_L
        self._units = units
      else:
        pos = ['NE', 'E', 'SE']
        font = View.FONT_S
        self._units = units[:3]  # only use max 3 units

      for i, unit in enumerate(self._units):
        self._value.append(self.add(units[i], pos[i], font))

  def set_values(self, values, elapsed):
    """Update displayed values"""
    if self._display:
      for index, value in enumerate(values):
        if index == len(self._value):
          break
        self._value[index].text = self.format(value, self._units[index])
      # Elapsed time could be shown here on large screens (TODO)

  def clear_values(self):
    """Clear the value display (reset to units)"""
    if self._display:
      for index in range(len(self._value)):
        self._value[index].text = self._units[index]

  def set_units(self, units):
    """Update the units shown with values"""
    if self._display:
      self._units = units

# ----------------------------------------------------------------------------
# View to show result summary (min, mean, max)

class ResultView(View):
  def __init__(self, display, border, unit):
    """Create a result view showing min/mean/max"""
    super().__init__(display, border)
    self._unit = unit

    if self._display:
      self._label_min = self.add('min:', 'NW', View.FONT_S)
      self._value_min = self.add('0.00', 'NE', View.FONT_S)

      self._label_mean = self.add('mean:', 'W', View.FONT_S)
      self._value_mean = self.add('0.00', 'E', View.FONT_S)

      self._label_max = self.add('max:', 'SW', View.FONT_S)
      self._value_max = self.add('0.00', 'SE', View.FONT_S)

  def set_values(self, min, mean, max):
    """Update result values"""
    if self._display:
      self._value_min.text = self.format(min, self._unit)
      self._value_mean.text = self.format(mean, self._unit)
      self._value_max.text = self.format(max, self._unit)

# ----------------------------------------------------------------------------
# View for editing config parameters (e.g., thresholds)

class ConfigView(View):
  def __init__(self, display, border, header, unit):
    """Create a config view with header + editable value"""
    super().__init__(display, border)
    self._unit = unit

    if self._display:
      self._header = self.add(header, 'NW', View.FONT_S)
      self._value = self.add(' ', 'SE', View.FONT_L)

  def set_value(self, value):
    """Set config value"""
    if self._display:
      self._value.text = "{0:s}{1:s}".format(value, self._unit)

  def set_unit(self, unit):
    """Set config unit"""
    if self._display:
      self._unit = unit

# ----------------------------------------------------------------------------
# View for plotting live sparkline data (e.g., current trend) //if want to use then do self._view = PlotView(self._display, 1, self._units) instead of self._view = ValuesView(self._display, 1, self._units) in active state


class PlotView(View):
  def __init__(self, display, border, units):
    """Create a simple plot view with sparklines"""
    super().__init__(display, border)
    self._units = units
    self._sparklines = []
    self._values = []
    pos = ['NW', 'NE']

    for i in range(min(len(units), 2)):
      sparkline = Sparkline(
        width=self._display.width - 2 * self._offset,
        height=self._display.height - 2 * self._offset,
        max_items=64,
        dyn_xpitch=False,
        x=0, y=0
      )
      self._sparklines.append(sparkline)
      self._values.append(self.add('0.00', pos[i], View.FONT_T))
      self._group.append(sparkline)

  def reset(self):
    """Clear the plotted data"""
    if self._display:
      for sparkline in self._sparklines:
        sparkline.clear_values()

  def set_values(self, values):
    """Add new values to the sparkline and update display"""
    if self._display:
      for i in range(len(self._sparklines)):
        self._sparklines[i].add_value(values[i], update=False)
        self._values[i].text = self.format(values[i], self._units[i])

  def show(self):
    """Render the updated plot on the screen"""
    if self._display:
      for sparkline in self._sparklines:
        sparkline.update()
      super().show()
