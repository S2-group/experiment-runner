from __future__ import annotations
import enum
from collections.abc import Callable
from pathlib import Path
import subprocess
import shlex

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

# Which sources to sample from
class PMSampleTypes(enum.Enum):
    PM_SAMPLE_TASKS     = "tasks"           # per task cpu usage and wakeup stats
    PM_SAMPLE_BAT       = "battery"         # battery and backlight info
    PM_SAMPLE_NET       = "network"         # network usage info
    PM_SAMPLE_DISK      = "disk"            # disk usage info
    PM_SAMPLE_INT       = "interrupts"      # interrupt distribution
    PM_SAMPLE_CPU_POWER = "cpu_power"       # c-state residency, power and frequency info
    PM_SAMPLE_TEMP      = "thermal"         # thermal pressure notifications
    PM_SAMPLE_SFI       = "sfi"             # selective forced idle information
    PM_SAMPLE_GPU_POWER = "gpu_power"       # gpu c-state residency, p-state residency and frequency info
    PM_SAMPLE_AGPM      = "gpu_agpm_stats"  # Statistics reported by AGPM
    PM_SAMPLE_SMC       = "smc"             # SMC sensors
    PM_SAMPLE_DCC       = "gpu_dcc_stats"   # gpu duty cycle info
    PM_SAMPLE_NVME      = "nvme_ssd"        # NVMe power state information
    LM_SAMPLE_THROTTLE  = "io_throttle_ssd" # IO Throttling information

# Different categories of stats available
class PMStatTypes(enum.Enum):
    PM_STAT_BATTERY     = 0 # Battery statistics
    PM_STAT_INTERRUPT   = 1 # Interrupt distribution
    PM_STAT_POWER       = 2 # CPU energy usage
    PM_STAT_IO          = 3 # Disc / Network
    PM_STAT_BACKLIGHT   = 4 # Backlight usage (not portable)

class PowerMetrics(object):
    """An integration of OSX powermetrics into experiment-runner as a data source plugin"""
    def __init__(self,                          sample_frequency: int  = 5000, 
                 out_file: Path         = None, sample_count: int      = None,
                 order: PMOrderTypes    = None, poweravg: int          = None, wakeup_cost: int       = None,
                 show_initial: bool     = False, show_summary: bool     = False):
        
        self.pm_process = None
        self.logfile = "test"

        # All paramters we can pass to powermetrics
        self.parameters = {
            "--output-file": self.logfile,
            "--sample-interval": sample_frequency,  # default
            "--sample-count": 0,                    # 0 for inifinite
            "--order": PMOrderTypes.PM_ORDER_CPU.value,
            "--format": PMFormatTypes.PM_FMT_PLIST.value,
            "--poweravg": 10,                       # default
            #"--wakeup-cost": 10,
            #"--buffer-size": 0,
            "--hide-platform-power": "",
            "--hide-cpu-duty-cycle": "",
            "--hide-gpu-duty-cycle": "",
            "--show-initial-usage": "",
            "--show-usage-summary": ""
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

    def start_pm(self):
        cmd = " ".join([f"{key} {value}" for key, value in self.parameters.items()])

        try:
            self.pm_process = subprocess.Popen(["powermetrics", *shlex.split(cmd)], stdout=subprocess.PIPE)
        except Exception as e:
            print(e)

    def stop_pm(self):
        if not self.pm_process:
            return

        try:
            self.pm_process.terminate()
            stdout, stderr = self.pm_process.communicate()

            print(stdout)
        except Exception as e:
            print(e)

    def print_config(self, handle):
        pass

    @staticmethod
    def parse_logs(logfile, stats: list):
        pass
