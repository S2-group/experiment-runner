from __future__ import annotations
import enum
from collections.abc import Callable
from pathlib import Path

# How to format the output
class PMFormatTypes(enum.Enum):
    PM_FMT_TEXT     = "text"
    PM_FMT_PLIST    = "plist"

# How to order results
class PMOrderTypes(enum.Enum):
    PM_ORDER_PID    = "pid"
    PM_ORDER_WAKEUP = "wakeups"
    PM_ORDER_CPU    = "cputime"
    PM_ORDER_HYBRID = "composite"

# Different categories of stats available
class PMStatTypes(enum.Enum):
    PM_STAT_BATTERY     = 0 # Battery statistics
    PM_STAT_INTERRUPT   = 1 # Interrupt distribution
    PM_STAT_POWER       = 2 # CPU energy usage
    PM_STAT_IO          = 3 # Disc / Network
    PM_STAT_BACKLIGHT   = 4 # Backlight usage (not portable)

class PowerMetrics(object):
    """An integration of OSX powermetrics into experiment-runner as a data source plugin"""
    def __init__(self, sample_frequency: int  = 5000, 
                 out_file: Path         = None, sample_count: int      = None,
                 order: PMOrderTypes    = None, format: PMFormatTypes  = None,
                 poweravg: int          = None, wakeup_cost: int       = None,
                 buffer_size: int       = None, hide_power: bool       = False,
                 hide_cpu: bool         = False, hide_gpu: bool         = False,
                 show_initial: bool     = False, show_summary: bool     = False):
        
        self.pm_process = None
        self.logfile = "test"

        # All paramters we can pass to powermetrics
        self.parameters = {
            "--output-file": self.logfile,
            "--sample-interval": sample_frequency,  # default
            "--sample-count": 0,                    # 0 for inifinite
            "--order": PMOrderTypes.PM_ORDER_CPU,
            "--format": PMFormatTypes.PM_FMT_PLIST,
            "--poweravg": 10,                       # default
            #"--wakeup-cost": 10,
            #"--buffer-size": 0,
            "--hide-platform-power": None,
            "--hide-cpu-duty-cycle": None,
            "--hide-gpu-duty-cycle": None,
            "--show-initial-usage": None,
            "--show-usage-summary": None
        }

    # Ensure that powermetrics is not currently running when we delete this object 
    def __del__(self):
        if self.pm_process:
            pass
    
    # Check that we are running on OSX, and that the powermetrics command exists
    def validate_platform(self):
        pass

    # Apply channel and mains settings to the picolog
    def update_parameters(self, **paramters):
        pass

    # Log data from powermetrics to a logfile
    def log(self, logfile = None, dev = None, timeout: int = 60, finished_fn: Callable[[], bool] = None):
        log_data = {}
        if logfile:
            self.logfile = logfile

        print('Logging...')
        
        # Write all of the data to a log file (if requested)
        if self.logfile:
            with open(self.logfile,'w') as f:
                pass

        return log_data
    
    def print_config(self, handle):
        pass

    @staticmethod
    def parse_log(logfile):
        pass
