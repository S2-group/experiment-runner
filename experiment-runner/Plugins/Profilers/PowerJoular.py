from __future__ import annotations
from pathlib import Path
import pandas as pd
from Plugins.Profilers.DataSource import CLISource, ParameterDict, ValueRef

# Supported Paramters for the PowerJoular metrics plugin
POWERJOULAR_PARAMETERS = {
    ("-p",): int,
    ("-a",): str,
    ("-f",): ValueRef,
    ("-o",): Path,
    ("-t",): None,
    ("-l",): None,
    ("-m",): str,
    ("-s",): str
}

class PowerJoular(CLISource):
    parameters = ParameterDict(POWERJOULAR_PARAMETERS)
    source_name = "powerjoular"
    supported_platforms = ["Linux"]

    """An integration of PowerJoular into experiment-runner as a data source plugin"""
    def __init__(self,
                 sample_frequency:      int                 = 5000,
                 out_file:              Path                = "powerjoular.csv",
                 additional_args:       dict                = {},
                 target_pid:            int                 = None):
        
        super().__init__()
        self.logfile = out_file
        self.args = {
            "-l": None,
            "-f": self._logfile,
        }

        if target_pid:
            self.update_parameters(add={"-p": target_pid})

        self.update_parameters(add=additional_args)
    
    @property
    def target_logfile(self):
        if "-p" in self.args.keys():
            return f"{self.logfile}-{self.args["-p"]}.csv"

        return None

    @staticmethod
    def parse_log(logfile: Path):
        # Things are already in csv format here, no checks needed
        return pd.read_csv(logfile).to_dict()
