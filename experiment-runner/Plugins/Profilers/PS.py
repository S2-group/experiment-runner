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

class PowerJoular(object):
    """An integration of OSX powermetrics into experiment-runner as a data source plugin"""
    def __init__(self):
        self.ps_process = None
        self.additional_args = None
        pass

    # Ensure that powermetrics is not currently running when we delete this object 
    def __del__(self):
        if self.pj_process:
            self.pj_process.terminate()
    
    # Check that we are running on OSX, and that the powermetrics command exists
    def __validate_platform(self):
        pass

    def __format_cmd(self):
        cmd = []
        return cmd + self.additional_args

    def start_ps(self):
        """
        Starts the powermetrics process, with the parameters in default_parameters + additional_args.
        """
                # man 1 ps
        # %cpu:
        #   cpu utilization of the process in "##.#" format.  Currently, it is the CPU time used
        #   divided by the time the process has been running (cputime/realtime ratio), expressed
        #   as a percentage.  It will not add up to 100% unless you are lucky.  (alias pcpu).
        profiler_cmd = f'ps -p {self.target.pid} --noheader -o %cpu'
        wrapper_script = f'''
        while true; do {profiler_cmd}; sleep 1; done
        '''

        time.sleep(1) # allow the process to run a little before measuring
        self.profiler = subprocess.Popen(['sh', '-c', wrapper_script],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

    def stop_pm(self):
        """
        Terminates the powermetrics process, as it was running indefinetly. This method collects the stdout and stderr

        Returns:
            stdout, stderr of the powermetrics process.
        """
        self.ps_profiler.kill()
        self.ps_profiler.wait()

    # Set the parameters used for power metrics to a new set
    def update_parameters(self, new_params: dict):
        """
        Updates the list of parameters, to be in line with new_params.
        Note that samplers will be set to the new list if present, make sure
        to include the previous set if you still want to use them.

        Parameters:
            new_params (dict): A dictionary containing the new list of parameters. For 
            parameters with no value (like --hide-cpu-duty-cycle) use a boolean to indicate
            if they can be used.

        Returns:
            The new list of parameters, can also be valided with self.default_parameters
        """
        pass
    
    def parse_pj_logs(self, logfile: Path):
        """
        Parses a provided logfile from powermetrics in plist format. Powermetrics outputs a plist
        for every sample taken, it included a newline after the closing <\plist>, we account for that here
        to make things easier to parse.
        
        Parameters:
            logfile (Path): The path to the plist logfile created by powermetrics

        Returns:
            A list of dicts, each representing the plist for a given sample    
        """
        df = pd.DataFrame(columns=['cpu_usage'])
        for i, l in enumerate(self.profiler.stdout.readlines()):
            cpu_usage=float(l.decode('ascii').strip())
            df.loc[i] = [cpu_usage]
        
        df.to_csv(self.run_dir / 'raw_data.csv', index=False)

