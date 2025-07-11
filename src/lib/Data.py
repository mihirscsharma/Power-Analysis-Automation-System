# ----------------------------------------------------------------------------
# Data.py: Helper classes for data-collection and aggregation.
# ----------------------------------------------------------------------------

#DataAggregator	Min, mean, max	Summary stats after measurement
#DataTable	Rolling buffer	Sparkline plot display during measurement

# ----------------------------------------------------------------------------
# --- DataAggregator: for calculating min/mean/max of measured values --------
class DataAggregator:
    """Calculates min, mean, and max for each dimension (e.g., voltage, current)"""

    def __init__(self, dim):
        """Initialize aggregator with number of data streams (dimensions)."""
        self._dim = dim
        self.reset()

    def reset(self):
        """Reset internal counters and aggregates."""
        self._n = 0  # Number of samples added
        # Initialize each stream with [min=large, sum=0, max=0]
        self._data = [[1e6, -1, 0] for i in range(self._dim)]

    def add(self, values):
        """Add a new data sample to the aggregator."""
        self._n += 1
        for index, value in enumerate(values):
            if index == self._dim:
                break  # ignore extra values
            self._data[index][1] += value                    # add to sum
            if value < self._data[index][0]:                 # update min
                self._data[index][0] = value
            if value > self._data[index][2]:                 # update max
                self._data[index][2] = value

    def get(self, index=None):
        """
        Return [min, mean, max] for each dimension.
        If index is given, return only that dimension.
        """
        if index is None:
            return [[data[0], data[1]/self._n, data[2]] for data in self._data]
        else:
            return [
                self._data[index][0],
                self._data[index][1]/self._n,
                self._data[index][2]
            ]

    def get_mean(self):
        """Return only the mean value for each stream."""
        return [data[1]/self._n for data in self._data]

# ----------------------------------------------------------------------------
# --- DataTable: ring buffer for live plots (sparklines) ---------------------
class DataTable:
    """Saves a fixed number of recent data points (per stream) for plotting."""

    def __init__(self, dim, size):
        """Initialize with number of dimensions and buffer size."""
        self._dim = dim
        self._size = size
        self.reset()

    def reset(self):
        """Clear all stored data."""
        self._n = 0
        # Create a list of lists: one per dimension (e.g., [[], [], []] for 3 streams)
        self._data = [[] for i in range(self._dim)]

    def add(self, values):
        """Add a new set of values to the data table (1 per dimension)."""
        # If buffer is full, remove oldest value (FIFO behavior)
        if len(self._data[0]) == self._size:
            for i in range(self._dim):
                self._data[i] = self._data[i][1:]

        # Append each value to its respective stream
        for i in range(self._dim):
            self._data[i].append(values[i])

    def get(self, index=None):
        """
        Get all recorded values.
        If index is given, return only the specified dimension.
        """
        if index is None:
            return self._data
        else:
            return self._data[index]
