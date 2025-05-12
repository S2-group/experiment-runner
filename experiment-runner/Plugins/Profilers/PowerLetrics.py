import plistlib
from pathlib import Path
from enum import StrEnum
import weakref
from Plugins.Profilers.DataSource import CLISource, ParameterDict, ValueRef

# How to format the output
class PLFormatTypes(StrEnum):
    PL_FMT_TEXT     = "text"
    PL_FMT_PLIST    = "plist"

# How to order results
class PLOrderTypes(StrEnum):
    PL_ORDER_PID    = "pid"
    PL_ORDER_WAKEUP = "wakeups"
    PL_ORDER_CPU    = "cputime"
    PL_ORDER_HYBRID = "composite"

POWERLETRICS_PARAMETERS = {
#    ("-h", "--help"): None,             # Dont support this
    ("-i", "--sample-rate"): int,
    ("-n", "--sample-count"): int,
    ("-o", "--output-file"): ValueRef,
    ("-r", "--order"): PLOrderTypes,
    ("-A", "--show-all"): None,
    ("--show-process-io"): None,
    ("--show-process-netstats"): None,
    ("--show-command-line"): None,
    ("--short"): None,
    ("--format"): PLFormatTypes,                 # Keep this fixed
    ("--proc-memory"): None,
    ("-f", "--flush"): None,
    ("-c", "--clear"): None,
    ("-s", "--server"): None,
    ("--port"): int,
    ("--host"): str,
    ("--rapl"): None,
    ("--psys"): None,
    ("--rapl-sample-rate"): int,
    ("--overhead"): None,
    ("--thread"): None,
}

class PowerLetrics(CLISource):
    parameters = ParameterDict(POWERLETRICS_PARAMETERS)
    source_name = "powerletrics"
    supported_platforms = ["Linux"]
    
    def __init__(self,
                 sample_frequency:      int                 = 1000,
                 out_file:              Path                = "pl_out.plist",
                 additional_args:       dict                = {},
                 order:                 PLOrderTypes        = PLOrderTypes.PL_ORDER_CPU):

        super().__init__()
        
        self.requires_admin = True
        self.logfile = out_file

        self.args = {
            "--output-file": self._logfile,
            "--format": PLFormatTypes.PL_FMT_PLIST,
            "--order": order,
            "--sample-rate": sample_frequency,
            "--short": None,
            "--overhead": None,
        }

        self.update_parameters(add=additional_args)

    @staticmethod
    def parse_log(logfile: Path):
        plists = []
        cur_plist = bytearray()
        with open(logfile, "rb") as fp:
            # Skip the first lines, they dont contain plist output
            for l in fp.readlines()[2:]:
                # Powermetrics outputs plists with null bytes inbetween. We account for this
                if l[0] == 0:
                    cur_plist.extend(l[1:])
                else:
                    cur_plist.extend(l)

                if b"</plist>\n" in l:
                    plists.append(plistlib.loads(cur_plist))
                    cur_plist = bytearray()

        return plists
