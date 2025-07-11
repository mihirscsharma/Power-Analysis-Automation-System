# ----------------------------------------------------------------------------
# ESP32Logger.py: log values using built-in Wi-Fi (ESP32-S2 or Pico W)
# ----------------------------------------------------------------------------

import socketpool         # CircuitPython module for network socket management
import wifi               # CircuitPython Wi-Fi interface
from LogWriter import LogWriter  # Base class for all loggers (handles formatting, etc.)

# Try importing Wi-Fi credentials from secrets.py
try:
    from secrets import secrets
except ImportError:
    print("WiFi settings need the file secrets.py, see documentation")
    raise  # Stops execution if no secrets.py exists

# Main class to log data via Wi-Fi
class DataLogger(LogWriter):
    """ Logs sensor data using Wi-Fi-capable board (ESP32 or Pico W) """

    def __init__(self, app):
        """ Initialize logger and connect to Wi-Fi """
        super(DataLogger, self).__init__(app)  # Call base class constructor
        self._init_esp32()                     # Setup Wi-Fi and socket

    def _init_esp32(self):
        """ Connect to Wi-Fi and prepare a UDP (or TCP) socket """

        retry = secrets["retry"]  # Number of times to retry Wi-Fi connection

        # Retry loop for connecting to access point
        while True:
            if retry == 0:
                raise RuntimeError("failed to connect to %s" % secrets["ssid"])
            try:
                wifi.radio.connect(secrets["ssid"], secrets["password"])  # connect!
                break  # success
            except Exception as e:
                retry -= 1  # try again

        # Setup network socket
        pool = socketpool.SocketPool(wifi.radio)  # use the connected Wi-Fi radio
        self._transport = secrets["transport"]    # either 'UDP' or 'TCP'

        # Configure UDP socket (default)
        if self._transport == 'UDP':
            self._socket = pool.socket(
                family=socketpool.SocketPool.AF_INET,
                type=socketpool.SocketPool.SOCK_DGRAM
            )
            # Destination IP and port from secrets.py
            self._dest = (secrets["remote_ip"], secrets["remote_port"])
        else:
            # TCP is not implemented in this version (stub only)
            self._socket = pool.socket(
                family=socketpool.SocketPool.AF_INET,
                type=socketpool.SocketPool.SOCK_STREAM
            )

    def log(self, msg):
        """ Sends one message string over the network using the selected protocol """
        try:
            if self._transport == 'UDP':
                # Send UTF-8 encoded message to the remote server
                self._socket.sendto(msg.encode('utf-8'), self._dest)
            else:
                # TCP not implemented here
                pass
        except:
            # If send fails, do nothing — keep measurement running
            pass
