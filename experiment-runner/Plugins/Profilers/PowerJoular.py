from __future__ import annotations
from pathlib import Path
import pandas as pd
from Plugins.Profilers.DataSource import CLISource, ParameterDict

# Supported Paramters for the PowerJoular metrics plugin
POWERJOULAR_PARAMETERS = {
    ("-p",): int,
    ("-a",): str,
    ("-f",): Path,
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

        self.logfile = out_file
        self.args = {
            "-l": None,
            "-f": self.logfile,
        }

        if target_pid:
            self.update_parameters(add={"-p": target_pid})

        self.update_parameters(add=additional_args)

    @staticmethod
    def parse_log(logfile: Path):
        # Things are already in csv format here, no checks needed
        return pd.read_csv(logfile).to_dict()
