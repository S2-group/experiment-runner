from __future__ import annotations
import enum
from collections.abc import Callable
from pathlib import Path
import subprocess
import plistlib
import platform
from shutil import shlex
import time
import signal
import os
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
                 additional_args:       list[str]           = []):

        self.logfile = outfile
        # TODO: Convert to appropriate dict
        self.args = f'powerjoular -l -p {self.target.pid} -f {self.run_dir / "powerjoular.csv"}'
            
    @staticmethod
    def parse_log(logfile: Path):
        # powerjoular.csv - Power consumption of the whole system
        # powerjoular.csv-PID.csv - Power consumption of that specific process
        df = pd.read_csv(context.run_dir / f"powerjoular.csv-{self.target.pid}.csv")
