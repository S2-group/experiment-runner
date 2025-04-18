from __future__ import annotations
from pathlib import Path
import pandas as pd
from Plugins.Profilers.DataSource import CLISource, ParameterDict

PS_PARAMTERS = {
        ("-A", "-e"): None,
        ("-a"): None,
        ("a"): None,
        ("-d"): None,
        ("-N", "--deselect"): None,
        ("r"): None,
        ("T"): None,
        ("x"): None,

        ("-C"): list[str],
        ("-G", "--Group"): list[int],
        ("-g", "--group"): list[str],
        ("-p", "p", "--pid"): list[int],
        ("--ppid"): list[int],
        ("-q", "q", "--quick-pid"): list[int],
        ("-s","--sid"): list[int],
        ("-t", "t", "--tty"): list[int],
        ("-u", "U", "--user"): list[int],
        ("-U", "--User"): list[int],

        ("-D"): str,
        ("-F"): None,
        ("-f"): None,
        ("f", "--forest"): None,
        ("-H"): None,
        ("-j"): None,
        ("j"): None,
        ("-l"): None,
        ("l"): None,
        ("-M", "Z"): None,
        ("-O"): str,
        ("O"): str,
        ("-o", "o", "--format"): list[str],
        ("-P"): None,
        ("s"): None,
        ("u"): None,
        ("v"): None,
        ("X"): None,
        ("--context"): None,
        ("--headers"): None,
        ("--no-headers", "--noheader"): None,
        ("--cols", "--columns", "--width"): int,
        ("--rows", "--lines"): int,
        ("--signames"): None,
        
        ("H"): None,
        ("-L"): None,
        ("-m", "m"): None,
        ("-T"): None,

        ("-c"): None,
        ("c"): None,
        ("e"): None,
        ("k", "--sort"): str, # There is a format type here, maybe regex this eventually
        ("L"): None,
        ("n"): None,
        ("S", "--cumulative"): None,
        ("-y"): None,
        ("-w", "w"): None,
}

class Ps(CLISource):
    parameters = ParameterDict(PS_PARAMTERS)
    source_name = "ps"
    supported_platforms = ["Linux"]

    """An integration of the Linux ps utility into experiment-runner as a data source plugin"""
    def __init__(self,
                 sleep_interval:        int                 = 1,
                 out_file:              Path                = "ps.csv",
                 additional_args:       dict                = {},
                 target_pid:            list[int]           = None,
                 out_format:            list[str]           = ["%cpu", "%mem"]):
        
        super().__init__()
        # man 1 ps
        # %cpu:
        #   cpu utilization of the process in "##.#" format.  Currently, it is the CPU time used
        #   divided by the time the process has been running (cputime/realtime ratio), expressed
        #   as a percentage.  It will not add up to 100% unless you are lucky.  (alias pcpu).
        # %mem:
        #   How much memory the process is currently using
        self.logfile = out_file
        self.sleep_interval = sleep_interval
        self.args = {
            "--noheader": None,
            "-o": out_format
        }

        if target_pid:
            self.update_parameters(add={"-p": target_pid})

        self.update_parameters(add=additional_args)

    def _format_cmd(self):
        cmd = super()._format_cmd()
        
        output_cmd = ""
        if self.logfile is not None:
            output_cmd = f" >> {self.logfile}"

        # This wraps the ps utility so that it runs continously and also outputs into a csv like format
        return f'''sh -c "while true; do {cmd} | awk '{{$1=$1}};1' | tr ' ' ','{output_cmd}; sleep {self.sleep_interval}; done"'''

    # The csv saved by default has no header, this must be provided by the user
    @staticmethod
    def parse_log(logfile: Path, column_names: list[str]):
        # Ps has many options, we dont check them all. converting to csv might fail in some cases
        try:
            df = pd.read_csv(logfile, names=column_names)
        except Exception as e:
            print(f"Could not parse ps ouput csv: {e}")

        return df.to_dict()

