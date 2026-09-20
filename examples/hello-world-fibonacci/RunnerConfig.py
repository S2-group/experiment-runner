from EventManager.Models.RunnerEvents import RunnerEvents
from EventManager.EventSubscriptionController import EventSubscriptionController
from ConfigValidator.Config.Models.RunTableModel import RunTableModel
from ConfigValidator.Config.Models.FactorModel import FactorModel
from ConfigValidator.Config.Models.RunnerContext import RunnerContext
from ConfigValidator.Config.Models.OperationType import OperationType
from ProgressManager.Output.OutputProcedure import OutputProcedure as output
from ProgressManager.Validation.RequirementsValidator import validate_experiment_requirements
import shutil
import sys

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
    default_output = ROOT_DIR / "experiments"
    results_output_path:        Path            = Path(os.getenv("EXPERIMENT_RUNNER_OUTPUT_PATH", str(default_output)))

    """Experiment operation type. Unless you manually want to initiate each run, use `OperationType.AUTO`."""
    operation_type:             OperationType   = OperationType.AUTO

    """The time Experiment Runner will wait after a run completes.
    This can be essential to accommodate for cooldown periods on some systems."""
    time_between_runs_in_ms:    int             = 1000

    """Path to log file for energy validation report. Relative to experiment output directory."""
    energy_validation_log_file: str             = "energy_validation_report.log"
    # Dynamic configurations can be one-time satisfied here before the program takes the config as-is
    # e.g. Setting some variable based on some criteria
    def __init__(self):
        """Executes immediately after program start, on config load"""

        EventSubscriptionController.subscribe_to_multiple_events([
            (RunnerEvents.VALIDATE_EXPERIMENT, self.validate_experiment),
            (RunnerEvents.BEFORE_EXPERIMENT  , self.before_experiment  ),
            (RunnerEvents.BEFORE_RUN         , self.before_run         ),
            (RunnerEvents.START_RUN          , self.start_run          ),
            (RunnerEvents.START_MEASUREMENT  , self.start_measurement  ),
            (RunnerEvents.INTERACT           , self.interact           ),
            (RunnerEvents.STOP_MEASUREMENT   , self.stop_measurement   ),
            (RunnerEvents.STOP_RUN           , self.stop_run           ),
            (RunnerEvents.POPULATE_RUN_DATA  , self.populate_run_data  ),
            (RunnerEvents.AFTER_EXPERIMENT   , self.after_experiment   )
        ])
        self.run_table_model = None  # Initialized later
        output.console_log("Custom config loaded")

    def create_run_table_model(self) -> RunTableModel:
        """Create and return the run_table model here. A run_table is a List (rows) of tuples (columns),
        representing each run performed"""
        factor1 = FactorModel("fib_type", ['iter', 'mem', 'rec'])
        factor2 = FactorModel("problem_size", [10, 35, 40, 5000, 10000])
        self.run_table_model = RunTableModel(
            factors=[factor1, factor2],
            exclude_combinations=[
                {factor2: [10]},   # all runs having treatment "10" will be excluded
                {factor1: ['rec'], factor2: [5000, 10000]},
                {factor1: ['mem', 'iter'], factor2: [35, 40]},  # all runs having the combination ("iter", 30) will be excluded
            ],
            repetitions = 10,
            data_columns=["energy", "runtime", "memory"]
        )
        return self.run_table_model

    def validate_experiment(self) -> None:
        """Validate the experiment setup before starting."""
        validate_experiment_requirements(Path(__file__))

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
        fib_type = context.execute_run["fib_type"]
        problem_size = context.execute_run["problem_size"]

        profiler_cmd = (
            f'energibridge '
            f'--max-execution 20 '
            f'--output {context.run_dir / "energibridge.csv"} '
            f'--summary '
            f'{sys.executable} '  # instead of bare "python"
            f'examples/hello-world-fibonacci/fibonacci_{fib_type}.py '
            f'{problem_size}'
        )

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
        df = pd.read_csv(context.run_dir / "energibridge.csv")
        return {
            "energy":  round(df["CPU_ENERGY (J)"].iloc[-1] - df["CPU_ENERGY (J)"].iloc[0], 3),
            "runtime": round(df["Delta"].sum() / 1000, 3),   # ms -> s
            "memory":  round(df["USED_MEMORY"].iloc[-1] / 1e9, 3),  # bytes -> GB
        }

    def after_experiment(self) -> None:
        """Perform any activity required after stopping the experiment here
        Invoked only once during the lifetime of the program."""
        pass

    # ================================ DO NOT ALTER BELOW THIS LINE ================================
    experiment_path:            Path             = None
