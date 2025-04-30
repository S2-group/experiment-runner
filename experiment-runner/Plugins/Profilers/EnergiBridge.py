from pathlib import Path
import pandas as pd
from Plugins.Profilers.DataSource import CLISource, ParameterDict

# Supported Paramters for the PowerJoular metrics plugin
ENERGIBRIDGE_PARAMETERS = {
    ("-o","--output"): Path,
    ("-s","--separator"): str,
    ("-c","--output-command"): str,
    ("-i","--interval"): int,
    ("-m","--max-execution"): int,
    ("-g","--gpu"): None,
    ("--summary",): None
}

class EnergiBridge(CLISource):
    parameters = ParameterDict(ENERGIBRIDGE_PARAMETERS)
    source_name = "energibridge"
    supported_platforms = ["Linux"]

    """An integration of PowerJoular into experiment-runner as a data source plugin"""
    def __init__(self,
                 sample_frequency:      int                 = 5000,
                 out_file:              Path                = "energibridge.csv",
                 summary:               bool                = True,
                 target_program:        str                 = "sleep 1000000",
                 additional_args:       dict                = {}):
        
        super().__init__()

        self.target_program = target_program
        self.logfile = out_file
        self.args = {
            "-o": Path(self.logfile),
            "-i": sample_frequency,
        }

        if summary:
            self.update_parameters(add={"--summary": None})

        self.update_parameters(add=additional_args)

    def _format_cmd(self):
        cmd = super()._format_cmd()

        return cmd + f" -- {self.target_program}"

    @staticmethod
    def parse_log(logfile: Path):
        # Things are already in csv format here, no checks needed
        return pd.read_csv(logfile).to_dict()
