from EventManager.Models.RunnerEvents import RunnerEvents
from EventManager.EventSubscriptionController import EventSubscriptionController
from ConfigValidator.Config.Models.RunTableModel import RunTableModel
from ConfigValidator.Config.Models.FactorModel import FactorModel
from ConfigValidator.Config.Models.RunnerContext import RunnerContext
from ConfigValidator.Config.Models.OperationType import OperationType
from ProgressManager.Output.OutputProcedure import OutputProcedure as output

from typing import Dict, List, Any, Optional
from pathlib import Path
from os.path import dirname, realpath

import os
import signal
import pandas as pd
import time
import subprocess
import shlex
import itertools

class RunnerConfig:
    ROOT_DIR = Path(dirname(realpath(__file__)))

    # ================================ USER SPECIFIC CONFIG ================================
    """The name of the experiment."""
    name:                       str             = "lzw"
    # check the if the output path exists, if exists, add timestamp to the name
    if os.path.exists(ROOT_DIR / 'experiments' / name):
        # convert time to date and time
        name = name + "_" + time.strftime("%Y%m%d-%H%M%S")

    """The path in which Experiment Runner will create a folder with the name `self.name`, in order to store the
    results from this experiment. (Path does not need to exist - it will be created if necessary.)
    Output path defaults to the config file's path, inside the folder 'experiments'"""
    results_output_path:        Path             = ROOT_DIR / 'experiments'

    """Experiment operation type. Unless you manually want to initiate each run, use `OperationType.AUTO`."""
    operation_type:             OperationType   = OperationType.AUTO

    """The time Experiment Runner will wait after a run completes.
    This can be essential to accommodate for cooldown periods on some systems."""
    time_between_runs_in_ms:    int             = 1000

    # Dynamic configurations can be one-time satisfied here before the program takes the config as-is
    # e.g. Setting some variable based on some criteria
    def __init__(self):
        """Executes immediately after program start, on config load"""

        EventSubscriptionController.subscribe_to_multiple_events([
            (RunnerEvents.BEFORE_EXPERIMENT, self.before_experiment),
            (RunnerEvents.BEFORE_RUN       , self.before_run       ),
            (RunnerEvents.START_RUN        , self.start_run        ),
            (RunnerEvents.START_MEASUREMENT, self.start_measurement),
            (RunnerEvents.INTERACT         , self.interact         ),
            (RunnerEvents.STOP_MEASUREMENT , self.stop_measurement ),
            (RunnerEvents.STOP_RUN         , self.stop_run         ),
            (RunnerEvents.POPULATE_RUN_DATA, self.populate_run_data),
            (RunnerEvents.AFTER_EXPERIMENT , self.after_experiment )
        ])
        self.run_table_model = None  # Initialized later
        output.console_log("Custom config loaded")

    def create_run_table_model(self) -> RunTableModel:
        """Create and return the run_table model here. A run_table is a List (rows) of tuples (columns),
        representing each run performed"""
        file_format_list = ['txt', 'pdf', 'jpg', 'png', 'mp4', 'mkv']
        file_size_list = ['small', 'large']
        file_repetition_list = ['low', 'high']

        # make a permutation of all the factors
        data_type_factors = []
        for format in file_format_list:
            for size in file_size_list:
                for repetition in file_repetition_list:
                    for num in range(1,11):
                        factor = format + '-' + size + '-' + repetition + '-' + str(num)
                        data_type_factors.append(factor)

        data_type_factor = FactorModel("data_type", data_type_factors)
        self.run_table_model = RunTableModel(
            factors = [data_type_factor],
            data_columns=['avg_cpu', 'total_energy']
        )
        return self.run_table_model

    def before_experiment(self) -> None:
        """Perform any activity required before starting the experiment here
        Invoked only once during the lifetime of the program."""
        pass

    def before_run(self) -> None:
        """Perform any activity required before starting a run.
        No context is available here as the run is not yet active (BEFORE RUN)"""
        # remove compressed files from previous run, which is *.huffman
        subprocess.check_call(shlex.split(f'rm -rf {self.ROOT_DIR / "data" / "*.lzw"}'))

    def start_run(self, context: RunnerContext) -> None:
        """Perform any activity required for starting the run here.
        For example, starting the target system to measure.
        Activities after starting the run should also be performed here."""
        
        # cpu_limit = context.run_variation['cpu_limit']
        data_type = context.run_variation['data_type']

        # start the target
        self.target = subprocess.Popen(['python', './compress_lzw.py', data_type],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.ROOT_DIR,
        )

        # Configure the environment based on the current variation
        # subprocess.check_call(shlex.split(f'cpulimit -b -p {self.target.pid} --limit {cpu_limit}'))
        

    def start_measurement(self, context: RunnerContext) -> None:
        """Perform any activity required for starting measurements."""

        profiler_cmd = f'powerjoular -l -p {self.target.pid} -f {context.run_dir / "powerjoular.csv"}'

        time.sleep(1) # allow the process to run a little before measuring
        self.profiler = subprocess.Popen(shlex.split(profiler_cmd))

    def interact(self, context: RunnerContext) -> None:
        """Perform any interaction with the running target system here, or block here until the target finishes."""

        # No interaction. We just run it for XX seconds.
        # Another example would be to wait for the target to finish, e.g. via `self.target.wait()`
        # output.console_log("Running program for 20 seconds")
        # time.sleep(20)
        output.console_log("Waiting for program to finish")
        self.target.wait()

    def stop_measurement(self, context: RunnerContext) -> None:
        """Perform any activity here required for stopping measurements."""

        os.kill(self.profiler.pid, signal.SIGINT) # graceful shutdown of powerjoular
        self.profiler.wait()

    def stop_run(self, context: RunnerContext) -> None:
        """Perform any activity here required for stopping the run.
        Activities after stopping the run should also be performed here."""
        
        self.target.kill()
        self.target.wait()
    
    def populate_run_data(self, context: RunnerContext) -> Optional[Dict[str, Any]]:
        """Parse and process any measurement data here.
        You can also store the raw measurement data under `context.run_dir`
        Returns a dictionary with keys `self.run_table_model.data_columns` and their values populated"""

        # powerjoular.csv - Power consumption of the whole system
        # powerjoular.csv-PID.csv - Power consumption of that specific process
        data_type = context.run_variation['data_type']
        # rename the powerjoular.csv to powerjoular.csv-{data_type}.csv
        os.rename(context.run_dir / "powerjoular.csv", context.run_dir / f"powerjoular-{data_type}.csv")
        df = pd.read_csv(context.run_dir / f"powerjoular-{data_type}.csv")
        # create new columns for df: compression_ratio, compression_time, energy_efficiency
        data_path = "/home/roy/green-lab/experiment-runner/examples/powerjoular-compress/data/" + data_type.replace('-', '/')
        # compute the sum size of files without extension huffman nor lzw
        sum_size = 0
        for file in os.listdir(data_path):
            if file.endswith(".huffman") or file.endswith(".lzw"):
                continue
            else:
                sum_size += os.path.getsize(os.path.join(data_path, file)) # unit Byte
        # compute the sum size of files with extension huffman
        sum_size_lzw = 0
        for file in os.listdir(data_path):
            if file.endswith(".lzw"):
                sum_size_lzw += os.path.getsize(os.path.join(data_path, file))
        # compute the compression ratio
        compression_ratio = sum_size / sum_size_lzw
        # compute the compression time
        compression_time = df['timestamp'].iloc[-1] - df['timestamp'].iloc[0]
        # compute the saving size
        saving_size = sum_size - sum_size_lzw
        # sum the power in column 'Total Power'
        total_power = df['Total Power'].sum()
        # compute the cpu utilization average in column 'CPU Utilization'
        cpu_utilization = df['CPU Utilization'].mean()
        # compute the energy efficiency
        energy_efficiency = saving_size / (total_power*cpu_utilization)
        # append new columns compression_ratio, compression_time, energy_efficiency into df
        df['compression_ratio'] = compression_ratio
        df['compression_time'] = compression_time
        df['saving_size'] = saving_size
        df['total_power'] = total_power
        df['cpu_utilization'] = cpu_utilization
        df['energy_efficiency'] = energy_efficiency
        # save the df into csv file
        df.to_csv(context.run_dir / f"lzw-{data_type}.csv", index=False)
        return None

    def after_experiment(self) -> None:
        """Perform any activity required after stopping the experiment here
        Invoked only once during the lifetime of the program."""
        pass

    # ================================ DO NOT ALTER BELOW THIS LINE ================================
    experiment_path:            Path             = None
