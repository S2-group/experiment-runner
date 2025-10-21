import sys
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

def zero_energy_columns(df):
    # zeroing energy consumption
    columns_to_zero = [col for col in df.columns if "(J)" in col]
    #subtract the first value from the entire column
    for col in columns_to_zero:
        df.loc[:, col] = df[col] - df[col].iloc[0]

class RunnerConfig:
    ROOT_DIR = Path(dirname(realpath(__file__)))

    # ================================ USER SPECIFIC CONFIG ================================
    """The name of the experiment."""
    name:                       str             = "new_runner_experiment"

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
        sampling_factor = FactorModel("sampling", [10, 50, 100, 200, 500, 1000])
        self.run_table_model = RunTableModel(
            factors = [sampling_factor],
            data_columns=['cold_start_energy', 'warm_start_energy']

        )
        return self.run_table_model

    def before_experiment(self) -> None:
        """Perform any activity required before starting the experiment here
        Invoked only once during the lifetime of the program."""
        pass

    def before_run(self) -> None:
        """Perform any activity required before starting a run.
        No context is available here as the run is not yet active (BEFORE RUN)"""
        pass

    def start_run(self, context: RunnerContext) -> None:
        """Perform any activity required for starting the run here.
        For example, starting the target system to measure.
        Activities after starting the run should also be performed here."""
        pass

    def start_measurement(self, context: RunnerContext) -> None:
        """Perform any activity required for starting measurements."""
        sampling_interval = context.execute_run['sampling']

        profiler_cmd = f'sudo energibridge \
                        --interval {sampling_interval} \
                        --max-execution 20 \
                        --output {context.run_dir / "energibridge.csv"} \
                        --summary \
                        -- python3 examples/green-lab-exp/primer.py'

        #time.sleep(1) # allow the process to run a little before measuring
        energibridge_log = open(f'{context.run_dir}/energibridge.log', 'w')
        self.profiler = subprocess.Popen(shlex.split(profiler_cmd), stdout=energibridge_log)

    def interact(self, context: RunnerContext) -> None:
        """Perform any interaction with the running target system here, or block here until the target finishes."""

        # No interaction. We just run it for XX seconds.
        # Another example would be to wait for the target to finish, e.g. via `self.target.wait()`
        output.console_log("Running program for 20 seconds")
        time.sleep(20)

    def stop_measurement(self, context: RunnerContext) -> None:
        """Perform any activity here required for stopping measurements."""
        self.profiler.wait()

    def stop_run(self, context: RunnerContext) -> None:
        """Perform any activity here required for stopping the run.
        Activities after stopping the run should also be performed here."""
        pass
    
    def populate_run_data(self, context: RunnerContext) -> Optional[Dict[str, Any]]:
        """Parse and process any measurement data here.
        You can also store the raw measurement data under `context.run_dir`
        Returns a dictionary with keys `self.run_table_model.data_columns` and their values populated"""

        # energibridge.csv - Power consumption of the whole system
        with open(context.run_dir / "energibridge.log", "r") as f:
            lines = f.readlines()
            timestamp = int(lines[0].strip())


        df = pd.read_csv(context.run_dir / f"energibridge.csv")
        headers = df.columns.tolist()
        core_id = 0 # TODO change me to the core that the benchmark is pinned to

        # assert Time column exists
        if "Time" not in headers:
            raise ValueError("Time (ns) column is missing from the input data.")

        # split into two phases
        phase1 = df[df['Time'] <= timestamp].copy()
        phase2 = df[df['Time'] > timestamp].copy()
        # check if both phases have data
        if phase1.empty:
            raise ValueError(f"No data found for Phase 1 (Time <= {timestamp}).")
        if phase2.empty:
            raise ValueError(f"No data found for Phase 2 (Time > {timestamp}).")
        # zeroing
        zero_energy_columns(phase1)
        zero_energy_columns(phase2)
        cold_start_energy = phase1[f'CORE{core_id}_ENERGY (J)'].iloc[-1]
        warm_start_energy = phase2[f'CORE{core_id}_ENERGY (J)'].iloc[-1]
        print(f"Cold Start Energy (J): {cold_start_energy}")
        print(f"Warm Start Energy (J): {warm_start_energy}")


        run_data = {
            'cold_start_energy': round(cold_start_energy, 3),
            'warm_start_energy': round(warm_start_energy, 3)
        }
        return run_data

    def after_experiment(self) -> None:
        """Perform any activity required after stopping the experiment here
        Invoked only once during the lifetime of the program."""
        pass

    # ================================ DO NOT ALTER BELOW THIS LINE ================================
    experiment_path:            Path             = None
