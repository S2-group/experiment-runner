from __future__ import annotations
import enum
from collections.abc import Callable
from pathlib import Path
import subprocess
import plistlib
import platform
import shutil
import time
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
        ("-o", "o", "--format"): str,
        ("-P"): None,
        ("s"): None,
        ("u"): None,
        ("v"): None,
        ("X"): None,
        ("--context"): None,
        ("--headers"): None,
        ("--no-headers"): None,
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

class Ps(CliSource):
    parameters = ParameterDict(PS_PARAMTERS)
    source_name = "ps"
    supported_platforms = ["Linux"]

    """An integration of the Linux ps utility into experiment-runner as a data source plugin"""
    def __init__(self,
                 sample_frequency:      int                 = 5000,
                 out_file:              Path                = "powerjoular.csv",
                 additional_args:       list[str]           = []):
        
        self.logfile = out_file
        
        # TODO: Convert this into a params dict
        self.args = f'ps -p {self.target.pid} --noheader -o %cpu'

        # man 1 ps
        # %cpu:
        #   cpu utilization of the process in "##.#" format.  Currently, it is the CPU time used
        #   divided by the time the process has been running (cputime/realtime ratio), expressed
        #   as a percentage.  It will not add up to 100% unless you are lucky.  (alias pcpu).
        wrapper_script = f'''
        while true; do {profiler_cmd}; sleep 1; done
        '''

    def parse_log(self, logfile: Path):
        df = pd.DataFrame(columns=['cpu_usage'])
        for i, l in enumerate(self.profiler.stdout.readlines()):
            cpu_usage=float(l.decode('ascii').strip())
            df.loc[i] = [cpu_usage]
        
        df.to_csv(self.run_dir / 'raw_data.csv', index=False)

