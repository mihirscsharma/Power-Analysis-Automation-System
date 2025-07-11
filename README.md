# Power-Analysis-Automation-System

An advanced, real-time power profiling and logging platform built on the Raspberry Pi Pico W and ESP32-S2, engineered to measure and visualize voltage, current, and power using an INA260 sensor

---

## Features

- **Live Power Monitoring**: Real-time display of voltage (V), current (mA), and power (mW) using CircuitPython + OLED display.
- **Wi-Fi Data Logging**: Wirelessly stream measurements to a remote server over UDP using onboard ESP32 Wi-Fi (no SD card required).
- **Interactive Touchpad UI**: Navigate between modes (Config, Run, View) via capacitive touchpad.
- **Modular Codebase**: Object-oriented state machine separates concerns (Ready, Active, Config states).
- **Custom PCB**: 2-layer PCB designed in KiCad to neatly interface INA260, touchpad, OLED, ESP32, and Pico W.
- **Fully Git-controlled**: Tracked firmware + schematic/hardware evolution with branches for board targets and logging options.

---

## Project Architecture

```
📁 circuitpython-vameter
├── main.py                 # Entry point, handles init and state machine
├── def_config.py           # Default runtime settings
├── user_config.py          # Custom runtime overrides (overrides defaults)
│
├── 📁 lib/                 # CircuitPython dependencies (e.g., adafruit_ina260)
├── 📁 fonts/               # Fonts used for OLED display rendering
│
├── 📁 adafruit_qtpy_esp32s2/
│   └── board_config.py     # Pin map for ESP32-S2 board variant
├── 📁 raspberry_pi_pico/
│   └── board_config.py     # Pin map for Pico W variant
│
├── 📁 tools/
│   └── cp-datalogger.py    # UDP listener to log incoming ESP32 messages
│
├── 📁 pcb/
│   ├── cp-vameter.kicad_pcb
│   ├── cp-vameter.kicad_sch
│   ├── ...
│
├── ActiveState.py          # Handles live readings, plotting, logging
├── ConfigState.py          # Touchpad-based runtime config interface
├── ReadyState.py           # Idle/start screen state
├── Data.py                 # Data aggregation, filtering
├── Scales.py               # Time/scale unit helpers
│
├── INA260DataProvider.py   # Reads sensor values over I2C
├── FakeDataProvider.py     # Simulates readings for headless testing
│
├── ESP32Logger.py          # Logs to remote server via UDP (Wi-Fi)
├── SerialLogger.py         # Alternate logging over USB serial
├── LogWriter.py            # Logger base class (handles formatting)
│
├── Touchpad.py             # KeyEventProvider abstraction for capacitive input
├── View.py                 # OLED and plot rendering views
└── secrets.py              # Wi-Fi credentials and logger target config
```

---

## ⚙Hardware Stack

- **Microcontroller**: Raspberry Pi Pico W (or Qt Py ESP32-S2)
  **Sensor**: Adafruit INA260 (voltage/current monitor over I2C)
- **Display**: 128x64 OLED via I2C
- **Touchpad**: Capacitive 3/4-key interface
- **Logger**: ESP32 onboard or ESP-01 over UART, logs via UDP
- **PCB**: Designed in KiCad 7 with headers for all peripherals

---

## Wi-Fi Logging via UDP

All logs are sent as CSV-like messages (e.g., `time_ms, V, mA,mW`) to a server IP and port defined in `secrets.py`.

Sample `secrets.py`:
```python
secrets = {
    "ssid": "YourWiFiName",
    "password": "YourPassword",
    "remote_ip": "192.168.0.42",
    "remote_port": 6500,
    "transport": "UDP",
    "retry": 3
}
```

On your PC, run:
```bash
python tools/cp-datalogger.py -p 6500 -o output.csv
```

---

## Getting Started

### Setup

1. Clone the repo  
   ```bash
   git clone https://github.com/yourname/circuitpython-vameter.git
   ```

2. Install CircuitPython libs under `/lib`
3. Edit `secrets.py` with your Wi-Fi and target IP
4. Flash `main.py` + config files to your board
5. Launch a listener on your PC with `cp-datalogger.py`

---

## Modes of Operation

- **ConfigState**: Set interval, oversampling, duration, etc. via touchpad
- **ReadyState**: Preview screen before recording
- **ActiveState**: Live measurement + plotting + UDP logging

---

## License

GPLv3 — Open-source and open-hardware.  

---

## Acknowledgements

Forked from [bablokb/circuitpython-vameter](https://github.com/bablokb/circuitpython-vameter)  
Extended for Wi-Fi UDP logging, Pico W compatibility, and full hardware integration.
