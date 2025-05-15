from pathlib import Path
import pandas as pd
import re
from Plugins.Profilers.DataSource import CLISource, ParameterDict, ValueRef

# Supported Paramters for the PowerJoular metrics plugin
ENERGIBRIDGE_PARAMETERS = {
    ("-o","--output"): ValueRef,
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
    supported_platforms = ["Linux", "Darwin", "Windows"]

    """An integration of PowerJoular into experiment-runner as a data source plugin"""
    def __init__(self,
                 sample_frequency:      int                 = 200,
                 out_file:              Path                = "energibridge.csv",
                 summary:               bool                = True,
                 target_program:        str                 = "sleep 1000000",
                 additional_args:       dict                = {}):
        
        super().__init__()
        
        self.requires_admin = True
        self.target_program = target_program
        self.logfile = out_file
        self.args = {
            "-o": self._logfile,
            "-i": sample_frequency,
        }

        if summary:
            self.update_parameters(add={"--summary": None})

        self.update_parameters(add=additional_args)
    
    @property
    def summary(self):
        return "--summary" in self.args.keys()
                    
    @property
    def summary_logfile(self):
        if  not self.logfile \
            or not any(map(lambda x: x in self.args.keys(), ["-o", "--output"])):
            
            return None

        return Path(self.logfile).parent / Path(self.logfile.name.split(".")[0] + "-summary.txt")
    
    def _stat_delta(self, data, stat):
        return list(data[stat].values())[-1] - list(data[stat].values())[0]

    # Less accurate than the summary from EB, but better than nothing
    # TODO: EnergiBridge calculates this differently in a system dependent way,
    #       this approximates using available data
    def generate_summary(self):
        log_data = self.parse_log(self.logfile)
        
        elapsed_time = self._stat_delta(log_data, "Time") / 1000
        total_joules = self._stat_delta(log_data, "PACKAGE_ENERGY (J)")

        return f"Energy consumption in joules: {total_joules} for {elapsed_time} sec of execution"

    # We also want to save the summary of EnergiBridge if present
    def stop(self, wait=False):

        stdout = super().stop(wait)

        if self.summary and self.summary_logfile:
            with open(self.summary_logfile, "w") as f:
                # The last line is the summary, if present
                last_line = stdout.splitlines()[-1]
                
                # If runtime was too short, energibridge doesnt provide a summary
                # Approximate this instead
                if not last_line.startswith("Energy consumption"):
                    print("[WARNING] EnergiBridge summary approximated, runtime too short")
                    last_line = self.generate_summary()

                f.write(last_line)

        return stdout

    def _format_cmd(self):
        cmd = super()._format_cmd()

        return cmd + f" -- {self.target_program}"

    @staticmethod
    def parse_log(logfile: Path, summary_logfile: Path|None=None):
        # Things are already in csv format here, no checks needed
        log_data = pd.read_csv(logfile).to_dict()

        if not summary_logfile:
            return log_data

        with open(summary_logfile, "r") as f:
            summary_data = f.read()
            
            # Extract the floats from the string, we expect always positive X.X
            values = re.findall("[0-9]+[.]?[0-9]*", summary_data)

            if len(values) == 2:
                summary_data = {
                    "total_joules": float(values[0]), 
                    "runtime_seconds": float(values[1])
                }

        return (log_data, summary_data)

