import plistlib
from pathlib import Path
from Plugins.Profilers.DataSource import CLISource, ParameterDict

POWERLETRICS_PARAMETERS = {
    ("-h", "--help"): None,             # Dont support this
    ("-i", "--sample-rate"): int,
    ("-n", "--sample-count"): int,
    ("-o", "--output-file"): str,
    ("-r", "--order"): str,
    ("-A", "--show-all"): None,
    ("--show-process-io"): None,
    ("--show-process-netstats"): None,
    ("--show-command-line"): None,
    ("--short"): None,
    ("--format"): None,                 # Keep this fixed
    ("--proc-memory"): None,
    (-"f", "--flush"): None,
    (-"c", "--clear"): None,
    (-"s", "--server"): None,
    ("--port"): int,
    ("--host"): str,
    ("--rapl"): None,
    ("--psys"): None,
    ("--rapl-sample-rate"): int,
    ("--overhead"): None,
    ("--thread"): None,
}

class PowerLetrics(CLISource):
    parameters = POWERLETRICS_PARAMETERS
    source_name = "powerletrics"
    supported_platforms = ["Linux"]
    
    def __init__(self,
                 sample_frequency:      int                 = 5000,
                 out_file:              Path                = "pm_out.plist",
                 additional_args:       dict                = {}):

        super().__init__()
        self.logfile = out_file

        self.args = {}

        self.update_parameters(add=additional_args)

    @staticmethod
    def parse_log(logfile: Path):
        plists = []
        cur_plist = bytearray()
        with open(logfile, "rb") as fp:
            for l in fp.readlines():
                # Powermetrics outputs plists with null bytes inbetween. We account for this
                if l[0] == 0:
                    cur_plist.extend(l[1:])
                else:
                    cur_plist.extend(l)

                if b"</plist>\n" in l:
                    plists.append(plistlib.loads(cur_plist))
                    cur_plist = bytearray()

        return plists
