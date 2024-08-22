import ctypes
import datetime
import time
import enum
from collections.abc import Callable

from picosdk.plcm3 import plcm3
from picosdk.functions import assert_pico_ok
from picosdk.constants import PICO_STATUS

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
    """An integration of PicoTech CM3 current data logger (https://www.picotech.com/download/manuals/PicoLogCM3CurrentDataLoggerUsersGuide.pdf)"""
    def __init__(self, sample_frequency: int = None, mains_setting: int = None, channel_settings: dict[int, int] = None):
        # Check that the picolog driver is accessible
        if ctypes.util.find_library("plcm3") is None:
            print("No valid PicoLog CM3 driver could be found, please check LD_LIBRARY_PATH is set properly")
            raise RuntimeError("Driver not available")

        # Check if a CM3 device is present
        if self.list_devices() == "":
            print("No valid PicoLog CM3 device could be found, please ensure the device is connected")
            raise RuntimeError("Device not available")

        # Some default settings
        self.sample_frequency    = sample_frequency if sample_frequency != None else 1000   # In ms
        self.mains_setting       = mains_setting if mains_setting != None else 0            # 50 Hz
        self.channel_settings    = channel_settings if channel_settings != None else {      # Which channels are enabled in what mode
            CM3Channels.PLCM3_CHANNEL_1: CM3DataTypes.PLCM3_1_MILLIVOLT,
            CM3Channels.PLCM3_CHANNEL_2: CM3DataTypes.PLCM3_OFF,
            CM3Channels.PLCM3_CHANNEL_3: CM3DataTypes.PLCM3_OFF}
    
    # Apply channel and mains settings to the picolog
    def mode(self, handle):
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
            status = plcm3.PLCM3SetChannel(handle, ch+1, self.channel_settings[ch+1])
            assert_pico_ok(status)
        
        # Apply mains setting
        status = plcm3.PLCM3SetMains(handle, ctypes.c_uint16(self.mains_setting))
        assert_pico_ok(status)

    def log(self, logfile = None, dev = None, timeout: int = 60, finished_fn: Callable[[], bool] = None):
        log_data = {}
        if logfile:
            self.logfile = logfile
        
        # Open the device
        handle = self.open_device()

        # Apply channel and mains settings 
        self.mode(handle)

        print('Logging started successfully...')
        timeout_start = time.time()       
        finished_checker = finished_fn if finished_fn != None else lambda: time.time() < timeout_start + timeout
        
        # Ensure the PicoLog always gets closed
        try:
            while finished_checker():
                channel_data = {}
                # Poll every channel for data
                for ch in range(plcm3.PLCM3Channels["PLCM3_MAX_CHANNELS"]):  
                    ch_handle = ctypes.c_uint32(ch+1)
                    data_handle = ctypes.c_uint32()
                    status = plcm3.PLCM3GetValue(handle, ch_handle, ctypes.byref(data_handle))
                    
                    if status == PICO_STATUS["PICO_NO_SAMPLES_AVAILABLE"]:
                        channel_data[ch+1] = (0, "")
                    else:
                        assert_pico_ok(status)
                        channel_data[ch+1] = self.apply_scaling(data_handle.value, self.channel_settings[ch+1])
                   
                log_data[datetime.datetime.now()] = [channel_data[1], channel_data[2], channel_data[3]]

                # Ensure measurement frequency
                time.sleep(self.sample_frequency/1000)
        except:
            print("Error durring PicoLog CM3 data collection")
        finally:
            # Close the connection to the unit
            self.close_device(handle)

            # Write all of the data to a log file (if requested)
            if self.logfile:
                with open(self.logfile,'w') as f:
                    for t_stamp, data in log_data.items():
                        f.write('%s, %.2f %s, %.2f %s, %.2f %s\n' % 
                                (t_stamp, data[0][0], data[0][1], data[1][0], data[1][1], data[2][0], data[2][1]))
        return log_data
    
    def close_device(self, handle):
        status = plcm3.PLCM3CloseUnit(handle)
        assert_pico_ok(status)

    def open_device(self, dev=None, verbose=True):
        if dev is not None:
            dev = ctypes.create_string_buffer(dev.encode("utf-8"))

        # Open the device
        handle = ctypes.c_int16()
        status = plcm3.PLCM3OpenUnit(ctypes.byref(self.handle), dev) 
        assert_pico_ok(status)
        
        if verbose:
            print("Device opened: ")
            self.print_info(handle)

        return handle

    def enumerate_devices(self):
        details = ctypes.create_string_buffer(255)
        length = ctypes.c_uint32(255)
        com_type = ctypes.c_uint32(plcm3.PLCM3CommunicationType["PLCM3_CT_USB"])

        status = plcm3.PLCM3Enumerate(details, ctypes.byref(length), com_type)
        assert_pico_ok(status)

        return details.value.decode("utf-8")

    def print_info(self):
        info_strings = ["Driver Version    :", 
                        "USB Version       :", 
                        "Hardware Version  :", 
                        "Variant Info      :", 
                        "Batch and Serial  :", 
                        "Calibration Date  :", 
                        "Kernel Driver Ver.:",
                        "Mac Address       :"]

        for i, s in enumerate(info_strings):
            res_buf = ctypes.create_string_buffer(255)
            required_size = ctypes.c_int16()

            status = plcm3.PLCM3GetUnitInfo(self.handle, res_buf, ctypes.c_int16(255), ctypes.byref(required_size), ctypes.c_uint32(i))
            assert_pico_ok(status)
            print(f" {s}{repr(res_buf.value).decode("utf-8")}")

    # Returns a tuple (scaled_value, unit_string)
    def apply_scaling(value, channel_mode):
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
