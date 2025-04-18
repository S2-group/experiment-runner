from __future__ import annotations
import ctypes
import datetime
import time
import enum
from collections.abc import Callable

from Plugins.Profilers.picosdk.plcm3 import plcm3
from Plugins.Profilers.picosdk.functions import assert_pico_ok
from Plugins.Profilers.picosdk.constants import PICO_STATUS

# Mapping of the PicoLog CM3 enums for convenience
class CM3DataTypes(enum.Enum):
    PLCM3_OFF               = 0
    PLCM3_1_MILLIVOLT       = 1
    PLCM3_10_MILLIVOLTS     = 2
    PLCM3_100_MILLIVOLTS    = 3
    PLCM3_VOLTAGE           = 4

class CM3Channels(enum.Enum):
    PLCM3_CHANNEL_1 = 1
    PLCM3_CHANNEL_2 = 2
    PLCM3_CHANNEL_3 = 3

class CM3MainsTypes(enum.Enum):
    PLCM3_MAINS_50HZ    = 0
    PLCM3_MAINS_60HZ    = 1

class PicoCM3(object):
    """An integration of PicoTech CM3 current data logger (https://www.picotech.com/download/manuals/picolog-cm3-data-logger-programmers-guide.pdf)"""
    def __init__(self, sample_frequency: int = None, mains_setting: int = None, channel_settings: dict[int, int] = None):
        # Some default settings
        self.handle = None
        self.sample_frequency    = sample_frequency if sample_frequency != None else 1000   # In ms
        self.mains_setting       = mains_setting if mains_setting != None else 0            # 50 Hz
        self.channel_settings    = channel_settings if channel_settings != None else {      # Which channels are enabled in what mode
            CM3Channels.PLCM3_CHANNEL_1.value: CM3DataTypes.PLCM3_1_MILLIVOLT.value,
            CM3Channels.PLCM3_CHANNEL_2.value: CM3DataTypes.PLCM3_OFF.value,
            CM3Channels.PLCM3_CHANNEL_3.value: CM3DataTypes.PLCM3_OFF.value}

        # Check that the picolog driver is accessible
        if ctypes.util.find_library("plcm3") is None:
            print("No valid PicoLog CM3 driver could be found, please check LD_LIBRARY_PATH is set properly")
            raise RuntimeError("Driver not available")

        # Check if a CM3 device is present
        if self.enumerate_devices() == "":
            print("No valid PicoLog CM3 device could be found, please ensure the device is connected")
            raise RuntimeError("Device not available")

    # Ensure that 
    def __del__(self):
        if self.handle:
            self.close_device()

    # Apply channel and mains settings to the picolog
    def mode(self):
        # Validate the channel settings
        if len(self.channel_settings.values()) < 3:
            print("All channels should have a setting")
            raise RuntimeError("Invalid PicoLog CM3 settings")
        
        for ch, setting in self.channel_settings.items():
            if  ch not in plcm3.PLCM3Channels.values() or \
                setting not in plcm3.PLCM3DataTypes.values():

                print(f"Channel {ch} has invalid setting: {setting}")
                raise RuntimeError("Invalid PicoLog CM3 settings")
        
        if self.mains_setting > 1 or self.mains_setting < 0:
            print(f"Channel {ch} has invalid setting {setting}")
            raise RuntimeError("Invalid PicoLog CM3 settings")

        # Apply settings to channels
        for ch in range(plcm3.PLCM3Channels["PLCM3_MAX_CHANNELS"]): 
            status = plcm3.PLCM3SetChannel(self.handle, ch+1, self.channel_settings[ch+1])
            assert_pico_ok(status)
        
        # Apply mains setting
        status = plcm3.PLCM3SetMains(self.handle, ctypes.c_uint16(self.mains_setting))
        assert_pico_ok(status)

    def log(self, logfile = None, dev = None, timeout: int = 60, finished_fn: Callable[[], bool] = None):
        log_data = {}
        if logfile:
            self.logfile = logfile

        print('Logging...')
        timeout_start = time.time()       
        finished_checker = finished_fn if finished_fn != None else lambda: time.time() < timeout_start + timeout
        
        # Ensure the PicoLog always gets closed
        while finished_checker():
            channel_data = {}
            # Poll every channel for data
            for ch in range(plcm3.PLCM3Channels["PLCM3_MAX_CHANNELS"]):  
                ch_handle = ctypes.c_uint32(ch+1)
                data_handle = ctypes.c_uint32()
                status = plcm3.PLCM3GetValue(self.handle, ch_handle, ctypes.byref(data_handle))
                
                if status == PICO_STATUS["PICO_NO_SAMPLES_AVAILABLE"]:
                    channel_data[ch+1] = (0, "")
                else:
                    assert_pico_ok(status)
                    channel_data[ch+1] = self.apply_scaling(data_handle.value, self.channel_settings[ch+1])
            log_data[datetime.datetime.now().isoformat(" ", "seconds")] = [channel_data[1], channel_data[2], channel_data[3]]

            # Ensure measurement frequency
            time.sleep(self.sample_frequency/1000)

        # Write all of the data to a log file (if requested)
        if self.logfile:
            with open(self.logfile,'w') as f:
                for t_stamp, data in log_data.items():
                    f.write('%s,%.2f %s,%.2f %s,%.2f %s\n' % \
                            (t_stamp, data[0][0], data[0][1], data[1][0], data[1][1], data[2][0], data[2][1]))
        return log_data
    
    def close_device(self):
        if self.handle:
            status = plcm3.PLCM3CloseUnit(self.handle)
            assert_pico_ok(status)
            self.handle = None
            print("PicoLog CM3 successfully closed...")

    def open_device(self, dev=None, verbose=True):
        if dev is not None:
            dev = ctypes.create_string_buffer(dev.encode("utf-8"))

        # Open the device
        self.handle = ctypes.c_int16()
        status = plcm3.PLCM3OpenUnit(ctypes.byref(self.handle), dev) 
        assert_pico_ok(status)
        
        if verbose:
            print("Device opened: ")
            self.print_info(self.handle)

        # Apply channel and mains settings 
        self.mode()
        
        # The PicoLog CM3 takes some time to warm up before it will return results
        time.sleep(5)
        print("PicoLog CM3 successfully opened...")
        return self.handle

    def enumerate_devices(self):
        details = ctypes.create_string_buffer(255)
        length = ctypes.c_uint32(255)
        com_type = ctypes.c_uint32(plcm3.PLCM3CommunicationType["PLCM3_CT_USB"])

        status = plcm3.PLCM3Enumerate(details, ctypes.byref(length), com_type)
        assert_pico_ok(status)

        return details.value.decode("utf-8")

    def print_info(self, handle):
        info_strings = {"Driver Version    : ": plcm3.PICO_INFO['PICO_DRIVER_VERSION'], 
                        "USB Version       : ": plcm3.PICO_INFO['PICO_USB_VERSION'], 
                        "Hardware Version  : ": plcm3.PICO_INFO['PICO_HARDWARE_VERSION'], 
                        "Variant Info      : ": plcm3.PICO_INFO['PICO_VARIANT_INFO'], 
                        "Batch and Serial  : ": plcm3.PICO_INFO['PICO_BATCH_AND_SERIAL'], 
                        "Calibration Date  : ": plcm3.PICO_INFO['PICO_CAL_DATE'], 
                        "Kernel Driver Ver.: ": plcm3.PICO_INFO['PICO_KERNEL_VERSION'],
                        "Mac Addres        : ": plcm3.PICO_INFO['PICO_MAC_ADDRESS']}

        for s, id in info_strings.items():
            res_buf = ctypes.create_string_buffer(255)
            required_size = ctypes.c_int16()

            status = plcm3.PLCM3GetUnitInfo(handle, res_buf, ctypes.c_int16(255), ctypes.byref(required_size), ctypes.c_uint32(id))
            assert_pico_ok(status)
            info_str = res_buf.value.decode("utf-8")
            print(f" {s}{info_str}")
    
    @staticmethod
    def parse_log(logfile):
        log_data = {k: [] for k in ['timestamp', 'channel_1', 'channel_2', 'channel_3']}

        with open(logfile) as f:
            lines = f.readlines()
            for line in lines:
                channel_vals = line.split(",")
                log_data['timestamp'].append(channel_vals[0])
                log_data['channel_1'].append(float(channel_vals[1].split(" ")[0]))
                log_data['channel_2'].append(float(channel_vals[2].split(" ")[0]))
                log_data['channel_3'].append(float(channel_vals[3].split(" ")[0]))

        return log_data


    # Returns a tuple (scaled_value, unit_string)
    def apply_scaling(self, value, channel_mode):
        if channel_mode == plcm3.PLCM3DataTypes["PLCM3_OFF"]:
            return (0, "")
        elif channel_mode == plcm3.PLCM3DataTypes["PLCM3_1_MILLIVOLT"]:
            return (value / 1000, "A")
        elif channel_mode == plcm3.PLCM3DataTypes["PLCM3_10_MILLIVOLTS"]:
            return (value / 1000.0, "A")
        elif channel_mode == plcm3.PLCM3DataTypes["PLCM3_100_MILLIVOLTS"]:
            return (value, "mA")
        elif channel_mode == plcm3.PLCM3DataTypes["PLCM3_VOLTAGE"]:
            return (value / 1000.0, "mV")
        else:
            return (-1, "invalid mode")
