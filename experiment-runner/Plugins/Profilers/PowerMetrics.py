from __future__ import annotations
import enum
from pathlib import Path
import plistlib

from Plugins.Profilers.DataSource import ParameterDict, CLISource

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

# Supported Paramters for the power metrics plugin
POWERMETRICS_PARAMETERS = {
    ("--poweravg",      "-a"): int,
    ("--buffer-size",   "-b"): int,
    ("--format",        "-f"): PMFormatTypes,
    ("--sample-rate",   "-i"): int,
    ("--sample-count",  "-n"): int,
    ("--output-file",   "-o"): Path,
    ("--order",         "-r"): PMOrderTypes,
    ("--samplers",      "-s"): list[PMSampleTypes],
    ("--wakeup-cost",   "-t"): int,
    ("--unhide-info",):        list[PMSampleTypes],
    ("--show-all",      "-A"): None,
    ("--show-initial-usage",): None,
    ("--show-usage-summary",): None,
    ("--show-extra-power-info",): None,
    ("--show-pstates",): None,
    ("--show-plimits",): None,
    ("--show-cpu-qos",): None,
    ("--show-cpu-scalability",): None,
    ("--show-hwp-capability",): None,
    ("--show-process-coalition",): None,
    ("--show-responsible-pid",): None,
    ("--show-process-wait-times",): None,
    ("--show-process-qos-tiers",): None,
    ("--show-process-io",): None,
    ("--show-process-gpu",): None,
    ("--show-process-netstats",): None,
    ("--show-process-qos"): None,
    ("--show-process-energy",): None,
    ("--show-process-samp-norm",): None,
    ("--handle-invalid-values",): None,
    ("--hide-cpu-duty-cycle",): None,
}

class PowerMetrics(CLISource):
    parameters = ParameterDict(POWERMETRICS_PARAMETERS)
    source_name = "powermetrics"
    supported_platforms = ["OS X"]

    """An integration of OSX powermetrics into experiment-runner as a data source plugin"""
    def __init__(self,
                 sample_frequency:      int                 = 5000,
                 out_file:              Path                = "pm_out.plist",
                 additional_args:       dict                = {},    
                 additional_samplers:   list[PMSampleTypes] = [],
                 hide_cpu_duty_cycle:   bool                = True,
                 order:                 PMOrderTypes        = PMOrderTypes.PM_ORDER_CPU):

        self.logfile = out_file
        # Grab all available power stats by default
        self.args = {
            "--output-file": self.logfile,
            "--sample-interval": sample_frequency,
            "--format": PMFormatTypes.PM_FMT_PLIST.value,
            "--samplers": [PMSampleTypes.PM_SAMPLE_CPU_POWER,
                           PMSampleTypes.PM_SAMPLE_GPU_POWER,
                           PMSampleTypes.PM_SAMPLE_AGPM] + additional_samplers,
            "--hide-cpu-duty-cycle": hide_cpu_duty_cycle,
            "--order": order.value
        }

        self.update_parameters(add=additional_args)
    
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
    def parse_log(logfile: Path):
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
            # Powermetrics outputs plists with null bytes inbetween. We account for this
            if l[0] == 0:
                plists.append(plistlib.loads(cur_plist))

                cur_plist = bytearray()
                cur_plist.extend(l[1:])
            else:
                cur_plist.extend(l)
            
        return plists
