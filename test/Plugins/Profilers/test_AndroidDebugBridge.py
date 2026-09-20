import unittest
import tempfile
import shutil
import sys
import time
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.append("experiment-runner")

from Plugins.Profilers.AndroidDebugBridge import AndroidBatteryMonitor

class TestADBMonitorLoop(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
    def tearDown(self):
        shutil.rmtree(self.tmpdir)
    def fake_subprocess(self, *args, **kwargs):
        cmd = args[0]
        mock = MagicMock()
        mock.returncode = 0
        # CASE 1: adb devices
        if "devices" in cmd:
            mock.stdout = "emulator-5554\tdevice\n"
            return mock
        # CASE 2: dumpsys battery
        mock.stdout = """
        level: 75
        temperature: 315
        voltage: 4100
        current now: -900000
        charge counter: 3810000
        """
        return mock

    def test_start_stop_monitor(self):
        with patch("subprocess.run", side_effect=self.fake_subprocess):
            monitor = AndroidBatteryMonitor(
                out_file=Path(self.tmpdir) / "android_battery.csv",
                poll_interval=1
            )

            monitor.start()
            time.sleep(3)
            monitor.stop()

        csv_path = Path(self.tmpdir) / "android_battery.csv"
        self.assertTrue(csv_path.exists())

        df = pd.read_csv(csv_path)

        self.assertFalse(df.empty)
        self.assertIn("voltage", df.columns)
        self.assertIn("power_draw", df.columns)
        print(df.head())

class FakeBatteryDevice:
    """
    Deterministic battery simulator.
    Mimics Android dumpsys battery output.
    """
    def __init__(self):
        self.level = 80
        self.voltage = 4200
        self.temperature = 310
        self.current_now = -900000  # µA
        self.charge_counter = 3810000
        self.tick = 0

    def step(self):
        """
        Simulate time passing.
        """
        self.tick += 1

        # battery slowly drains
        if self.tick % 2 == 0:
            self.level = max(0, self.level - 1)
        # voltage drops slightly with battery level
        self.voltage = 4200 - (80 - self.level) * 2
        # current fluctuates slightly
        self.current_now = -900000 - (self.tick * 1000)

    def dumpsys(self):
        self.step()
        return f"""
        level: {self.level}
        temperature: {self.temperature}
        voltage: {self.voltage}
        current now: {self.current_now}
        charge counter: {self.charge_counter}
        """

class FakeADB:
    def __init__(self, device: FakeBatteryDevice):
        self.device = device

    def run(self, cmd, *args, **kwargs):
        mock = MagicMock()
        mock.returncode = 0
        cmd_str = " ".join(cmd)
        # adb devices
        if "devices" in cmd_str:
            mock.stdout = "emulator-5554\tdevice\n"
            return mock

        # dumpsys battery
        if "dumpsys battery" in cmd_str:
            mock.stdout = self.device.dumpsys()
            return mock

        mock.stdout = ""
        return mock

class TestDeterministicBattery(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_monitor(self):
        device = FakeBatteryDevice()
        fake_adb = FakeADB(device)

        def patched_run(cmd, *args, **kwargs):
            return fake_adb.run(cmd, *args, **kwargs)

        with patch("subprocess.run", side_effect=patched_run):
            monitor = AndroidBatteryMonitor(
                out_file=Path(self.tmpdir) / "battery.csv",
                poll_interval=1
            )
            monitor.start()

            time.sleep(4)
            monitor.stop()

        df = pd.read_csv(Path(self.tmpdir) / "battery.csv")

        # deterministic checks
        self.assertGreater(len(df), 2)
        self.assertIn("voltage", df.columns)
        self.assertIn("power_draw", df.columns)
        self.assertTrue(df["voltage"].iloc[-1] <= df["voltage"].iloc[0])
        print(df)