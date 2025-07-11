
import collections  # To maintain the order of time units for display and logic

# ----------------------------------------------------------------------------
# This module defines time scaling utilities for converting between time units
# and for determining appropriate display/plot labels for durations.
#
# - INT_SCALES maps interval scale units to a tuple:
#     (conversion factor to seconds, next larger duration label)
#   Example: 'm' → (60.0, 'h')  means 1 minute = 60 seconds, display in hours
#
# - int_fac(scale):      Returns how many seconds are in one unit of 'scale'
# - dur_scale(scale):    Returns the next larger unit label for a given scale
# - dur_fac(scale):      Returns how many seconds are in one unit of the *duration*
#                        corresponding to the input interval scale
#   Example: dur_fac('s') → 60.0 (since durations are shown in 'm' for 's')
# ----------------------------------------------------------------------------

# map interval scale to (conversion factor to seconds, display label for duration)
INT_SCALES = collections.OrderedDict([
    ('ms', (0.001, 's')),     # milliseconds → seconds
    ('s',  (1.0,   'm')),     # seconds → minutes
    ('m',  (60.0,  'h')),     # minutes → hours
    ('h',  (3600.0,'d')),     # hours → days
    ('d',  (86400.0,'d'))     # days → days (label doesn't change)
])

def int_fac(scale):
    """Return the time conversion factor for a given interval scale (e.g., 'm' → 60.0)"""
    return INT_SCALES[scale][0]

def dur_scale(scale):
    """Return the label of the larger time unit used for duration display (e.g., 'm' → 'h')"""
    return INT_SCALES[scale][1]

def dur_fac(scale):
    """
    Return the duration conversion factor for the next larger time unit.
    For example, if scale is 's', duration is displayed in 'm', so return 60.0
    """
    return INT_SCALES[dur_scale(scale)][0]
