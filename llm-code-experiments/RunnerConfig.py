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
import config

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
        problem_factor = FactorModel("problem", ["problem1", "problem2", "problem3"])
        solution_factor = FactorModel("solution", ["human", "basic", "efficient"])
        self.run_table_model = RunTableModel(
            factors = [problem_factor, solution_factor],
            data_columns=['Time', 'PACKAGE_ENERGY', 'CPU_USAGE_0', 'CPU_USAGE_1', 'CPU_USAGE_2', 'CPU_USAGE_3',
                          'CPU_USAGE_4', 'CPU_USAGE_5', 'CPU_USAGE_6', 'CPU_USAGE_7', 'TOTAL_MEMORY', 'USED_MEMORY'],
            repetitions=25,
            shuffle=True
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
        solution = context.run_variation['solution']
        problem = context.run_variation['problem']

        profiler_cmd = f'ssh {config.USERNAME}@{config.IP} "sudo -s energibridge \
                        --interval 200 \
                        --max-execution 0 \
                        --output {config.REMOTE_DIR}/llm-code-experiments/energibridge.csv \
                        python3 {config.REMOTE_DIR}/problems/{problem}/{solution}.py"'

        #time.sleep(1) # allow the process to run a little before measuring
        energibridge_log = open(f'{context.run_dir}/energibridge.log', 'w')
        self.profiler = subprocess.Popen(shlex.split(profiler_cmd), stdout=energibridge_log)

    def interact(self, context: RunnerContext) -> None:
        """Perform any interaction with the running target system here, or block here until the target finishes."""

        # No interaction. We just run it for XX seconds.
        # Another example would be to wait for the target to finish, e.g. via `self.target.wait()`
        output.console_log("Waiting for program to finish")
        self.profiler.wait()
        # time.sleep(20)

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
        scp_command = f"scp -r {config.USERNAME}@{config.IP}:{config.REMOTE_CSV_PATH} {context.run_dir}"

        try:
            # Run the scp command
            subprocess.run(scp_command, shell=True, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            print(f"An error occurred during file transfer: {e}")
            print(f"Error output: {e.stderr}")

        # energibridge.csv - Power consumption of the whole system
        df = pd.read_csv(context.run_dir / f"energibridge.csv")

        run_data = {
            'Time': df['Time'].iloc[-1] - df['Time'].iloc[0],
            'PACKAGE_ENERGY': df['PACKAGE_ENERGY (J)'].iloc[-1] - df['PACKAGE_ENERGY (J)'].iloc[0],
            'CPU_USAGE_0': df['CPU_USAGE_0'].mean(),
            'CPU_USAGE_1': df['CPU_USAGE_1'].mean(),
            'CPU_USAGE_2': df['CPU_USAGE_2'].mean(),
            'CPU_USAGE_3': df['CPU_USAGE_3'].mean(),
            'CPU_USAGE_4': df['CPU_USAGE_4'].mean(),
            'CPU_USAGE_5': df['CPU_USAGE_5'].mean(),
            'CPU_USAGE_6': df['CPU_USAGE_6'].mean(),
            'CPU_USAGE_7': df['CPU_USAGE_7'].mean(),
            'TOTAL_MEMORY': df['TOTAL_MEMORY'].mean(),
            'USED_MEMORY': df['USED_MEMORY'].mean()
        }
        return run_data

    def after_experiment(self) -> None:
        """Perform any activity required after stopping the experiment here
        Invoked only once during the lifetime of the program."""
        pass

    # ================================ DO NOT ALTER BELOW THIS LINE ================================
    experiment_path:            Path             = None
