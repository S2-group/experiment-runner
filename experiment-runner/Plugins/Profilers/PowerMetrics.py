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
    def __init__(self,                                         sample_frequency: int          = 5000, 
                 out_file: Path             = "pm_out.plist",  samplers: list[PMSampleTypes] = [],
                 additional_args: list[str] = None,            hide_cpu_duty_cycle: bool = True):
        
        self.pm_process = None
        self.logfile = "test"
        
        self.additional_args = additional_args
        # Grab all available power stats by default
        self.default_parameters = {
            "--output-file": self.logfile,
            "--sample-interval": sample_frequency,
            "--format": PMFormatTypes.PM_FMT_PLIST.value,
            "--samplers": [PMSampleTypes.PM_SAMPLE_CPU_POWER.value, 
                           PMSampleTypes.PM_SAMPLE_GPU_POWER.value,
                           PMSampleTypes.PM_SAMPLE_AGPM.value] + samplers,
            "--hide-cpu-duty-cycle": hide_cpu_duty_cycle
        }

    # Ensure that powermetrics is not currently running when we delete this object 
    def __del__(self):
        if self.pm_process:
            self.pm_process.terminate()
    
    # Check that we are running on OSX, and that the powermetrics command exists
    def __validate_platform(self):
        pass

    def __format_cmd(self):
        cmd = ""

        return cmd

    def start_pm(self):
        """
        Starts the powermetrics process, with the parameters in default_parameters + additional_args.
        """
        cmd = self.__format_cmd()

        try:
            self.pm_process = subprocess.Popen(["powermetrics", *shlex.split(cmd)], stdout=subprocess.PIPE)
        except Exception as e:
            print(e)            

    def stop_pm(self):
        """
        Terminates the powermetrics process, as it was running indefinetly. This method collects the stdout and stderr

        Returns:
            stdout, stderr of the powermetrics process.
        """
        if not self.pm_process:
            return

        try:
            self.pm_process.terminate()
            stdout, stderr = self.pm_process.communicate()

            print(stdout)
            return stdout, stderr
        except Exception as e:
            print(e)
    
    # Set the parameters used for power metrics to a new set
    def update_parameters(self, new_params: dict):
        """
        Updates the list of parameters, to be in line with new_params.
        Note that samplers will be set to the new list if present, make sure
        to include the previous set if you still want to use them.

        Parameters:
            new_params (dict): A dictionary containing the new list of parameters. For 
            parameters with no value (like --hide-cpu-duty-cycle) use a boolean to indicate
            if they can be used.

        Returns:
            The new list of parameters, can also be valided with self.default_parameters
        """
        for p, v in new_params.items():
            self.default_parameters[p] = v
    
    @staticmethod
    def get_plist_power(pm_plists: list[dict]):
        """
        Extracts from a list of plists, the relavent power statistics if present. If no 
        power stats are present, this returns an empty list. This is mainly a helper method, 
        to make the plists easier to work with.

        Parameters:
            pm_plists (list[dict]): The list of plists created by parse_pm_plist

        Returns:
            A list of dicts, each containing a subset of the available stats related to power.
        """
        power_plists = []

        for plist in pm_plists:
            stats = {}
            if "GPU" in plist.keys():
                stats["GPU"] = plist["GPU"].copy()
                del stats["GPU"]["misc_counters"]
                del stats["GPU"]["pstates"]

            if "processor" in plist.keys():
                stats["processor"] = plist["processor"]
                del stats["processor"]["packages"]

            if "agpm_stats" in plist.keys():
                stats["agpm_stats"] = plist["agpm_stats"]

            if "timestamp" in plist.keys():
                stats["timestamp"] = plist["timestamp"]

            power_plists.apend(stats)
        
        return power_plists
    
    @staticmethod
    def parse_pm_plist(logfile: Path):
        """
        Parses a provided logfile from powermetrics in plist format. Powermetrics outputs a plist
        for every sample taken, it included a newline after the closing <\plist>, we account for that here
        to make things easier to parse.
        
        Parameters:
            logfile (Path): The path to the plist logfile created by powermetrics

        Returns:
            A list of dicts, each representing the plist for a given sample    
        """
        
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
            
        return plists
