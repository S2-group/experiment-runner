import os
import ctypes
from picosdk.plcm3 import plcm3
from platform import uname


class PicoCM3(object):
    """An integration of PicoTech CM3 current data logger (https://www.picotech.com/download/manuals/PicoLogCM3CurrentDataLoggerUsersGuide.pdf)"""
    SAMPLE_FREQUENCY = 1000 # in ms
    CHANNEL_SETTINGS = {

    }
    
    def __init__(self):
        # Check if a CM3 is present
        pass

    def mode(self, runmode):
        pass

    def log(self,timeout, logfile = None):
        pass

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
