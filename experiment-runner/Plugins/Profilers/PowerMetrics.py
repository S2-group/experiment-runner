from __future__ import annotations
import enum
from collections.abc import Callable
from pathlib import Path
import subprocess
import shlex
import plistlib

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
    PM_SAMPLE_THROTTLE  = "io_throttle_ssd" # IO Throttling information

class PowerMetrics(object):
    """An integration of OSX powermetrics into experiment-runner as a data source plugin"""
    def __init__(self,                              sample_frequency: int          = 5000, 
                 out_file: Path             = None,  poweravg: int                 = None,  
                 show_summary: bool         = False, samplers: list[PMSampleTypes] = None,
                 additional_args: list[str] = None):
        
        self.pm_process = None
        self.logfile = "test"
        
        # Grab all available power stats by default
        self.default_parameters = {
            "--output-file": self.logfile,
            "--sample-interval": sample_frequency,
            "--format": PMFormatTypes.PM_FMT_PLIST.value,
            "--samplers": [PMSampleTypes.PM_SAMPLE_CPU_POWER.value, 
                           PMSampleTypes.PM_SAMPLE_GPU_POWER.value,
                           PMSampleTypes.PM_SAMPLE_AGPM.value],
            "--hide-cpu-duty-cycle": ""
        }

    # Ensure that powermetrics is not currently running when we delete this object 
    def __del__(self):
        if self.pm_process:
            self.pm_process.terminate()
    
    # Check that we are running on OSX, and that the powermetrics command exists
    def validate_platform(self):
        pass

    # Set the parameters used for power metrics to a new set
    def update_parameters(self, new_params: dict):
        for p, v in new_params.items():
            self.default_parameters[p] = v
    
    def format_cmd(self):
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
    
    @staticmethod
    def get_stat_types(logfile):
        pass

    @staticmethod
    def get_power(logfile):
        pass

    @staticmethod
    def parse_logs(logfile, stats: list):
        fp = open(logfile, "rb")

        plists = []
        cur_plist = bytearray()
        for l in fp.readlines():
            if l[0] == 0:
                plists.append(plistlib.loads(cur_plist))

                cur_plist = bytearray()
                cur_plist.extend(l[1:])
            else:
                cur_plist.extend(l)
