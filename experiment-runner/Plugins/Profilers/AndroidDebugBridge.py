from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum, auto
import re
import subprocess
import csv
from datetime import datetime
import pandas as pd
import time
import threading

from Plugins.Profilers.DataSource import DeviceSource
from ConfigValidator.Config.Models.RunnerContext import RunnerContext


class DataColumns(Enum):
    BATTERY_PERCENTAGE  = auto()
    BATTERY_TEMPERATURE = auto()
    BATTERY_VOLTAGE     = auto()
    CURRENT_NOW         = auto()
    CHARGE_COUNTER      = auto()
    BATTERY_HEALTH      = auto()
    CHARGING_STATUS     = auto()
    POWER_DRAW          = auto()

    _PATTERN = re.compile(r'(android_battery__)(.+)')

    @property
    def column_name(self) -> str:
        return f'android_battery__{self.name.lower()}'


class AndroidBatteryMonitor(DeviceSource):
    source_name = "adb"
    supported_platforms = ["Linux", "Darwin"]

    def __init__(self, device_serial=None, poll_interval=2, out_file=Path("android_battery.csv")):
        super().__init__()

        self.device_serial = device_serial
        self.poll_interval = poll_interval
        self.logfile = Path(out_file)

        self._validate_adb_available()

        self._thread = None
        self._stop_event = threading.Event()

    def _validate_adb_available(self):
        result = subprocess.run(['adb', 'version'], capture_output=True, timeout=5)
        if result.returncode != 0:
            raise RuntimeError("ADB version check failed.")

    def open_device(self):
        if self.device_serial:
            return

        result = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=5)
        devices = [
            line.split()[0]
            for line in result.stdout.splitlines()
            if "\tdevice" in line
        ]
        if not devices:
            raise RuntimeError("No devices found")

        self.device_serial = devices[0]

    def close_device(self):
        self.device_serial = None
    
    def list_devices(self):
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=5)
        return [
            line.split()[0]
            for line in result.stdout.splitlines()
            if "\tdevice" in line
        ]

    def set_mode(self, settings=None):
        return

    def read_sample(self):
        result = subprocess.run(["adb", "-s", self.device_serial, "shell", "dumpsys battery"], capture_output=True, text=True, timeout=10)
        return self._parse(result.stdout)

    def _parse(self, text):
        patterns = {
            "percentage": r"^\s*level:\s*(\d+)",
            "temperature": r"^\s*temperature:\s*(\d+)",
            "voltage": r"^\s*voltage:\s*(\d+)",
            "current_now": r"^\s*current now:\s*(-?\d+)",
            "charge_counter": r"^\s*charge counter:\s*(\d+)",
        }
        data = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                data[key] = match.group(1)

        voltage_raw = data.get("voltage")
        if voltage_raw is None:
            fallback = re.search(r"voltage:\s*(\d+)", text)
            voltage_raw = fallback.group(1) if fallback else None
        try:
            voltage_v = (float(voltage_raw) / 1000.0) if voltage_raw else None
        except ValueError:
            voltage_v = None

        try:
            current_raw = float(data.get("current_now", 0))
            current_ma = abs(current_raw) / 1000.0
        except ValueError:
            current_ma = 0.0
        if voltage_v is not None:
            data["voltage"] = float(voltage_raw)
            data["power_draw"] = voltage_v * current_ma
        else:
            data["voltage"] = 0.0
            data["power_draw"] = 0.0

        return data

    def _run(self):
        self.open_device()
        with open(self.logfile, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "timestamp",
                    "percentage",
                    "temperature",
                    "voltage",
                    "current_now",
                    "charge_counter",
                    "power_draw"
                ]
            )
            writer.writeheader()

            while not self._stop_event.is_set():
                data = self.read_sample()
                data["timestamp"] = datetime.now().isoformat()
                writer.writerow(data)
                f.flush()
                time.sleep(self.poll_interval)
        self.close_device()

    def log(self):
        self._run()
        return 0

    def start(self):
        if self._thread and self._thread.is_alive():
            raise RuntimeError("Battery monitor already running")
        self._stop_event.clear()
        self._thread = threading.Thread(target=self.log, name="DeviceWorker", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()

        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None

    @staticmethod
    def parse_log(logfile):
        df = pd.read_csv(logfile)
        if df.empty:
            return {}

        result = {}
        for col in df.columns:
            if col == "timestamp":
                continue
            values = pd.to_numeric(df[col], errors="coerce").dropna()

            if len(values):
                result[f"android_battery__{col}"] = float(values.mean())

        return result