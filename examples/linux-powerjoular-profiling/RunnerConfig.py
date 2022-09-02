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
        cpu_limit_factor = FactorModel("cpu_limit", [25, 50, 100])
        self.run_table_model = RunTableModel(
            factors = [cpu_limit_factor],
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
        pass

    def start_run(self, context: RunnerContext) -> None:
        """Perform any activity required for starting the run here.
        For example, starting the target system to measure.
        Activities after starting the run should also be performed here."""
        
        cpu_limit = context.run_variation['cpu_limit']

        # start the target
        self.target = subprocess.Popen(['python', './primer.py'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.ROOT_DIR,
        )

        # Configure the environment based on the current variation
        subprocess.check_call(shlex.split(f'cpulimit -b -p {self.target.pid} --limit {cpu_limit}'))
        

    def start_measurement(self, context: RunnerContext) -> None:
        """Perform any activity required for starting measurements."""

        profiler_cmd = f'powerjoular -l -p {self.target.pid} -f {context.run_dir / "powerjoular.csv"}'

        time.sleep(1) # allow the process to run a little before measuring
        self.profiler = subprocess.Popen(shlex.split(profiler_cmd))

    def interact(self, context: RunnerContext) -> None:
        """Perform any interaction with the running target system here, or block here until the target finishes."""

        # No interaction. We just run it for XX seconds.
        # Another example would be to wait for the target to finish, e.g. via `self.target.wait()`
        output.console_log("Running program for 20 seconds")
        time.sleep(20)

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
        df = pd.read_csv(context.run_dir / f"powerjoular.csv-{self.target.pid}.csv")
        run_data = {
            'avg_cpu': round(df['CPU Utilization'].sum(), 3),
            'total_energy': round(df['CPU Power'].sum(), 3),
        }
        return run_data

    def after_experiment(self) -> None:
        """Perform any activity required after stopping the experiment here
        Invoked only once during the lifetime of the program."""
        pass

    # ================================ DO NOT ALTER BELOW THIS LINE ================================
    experiment_path:            Path             = None
