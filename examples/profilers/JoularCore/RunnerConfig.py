from EventManager.Models.RunnerEvents import RunnerEvents
from EventManager.EventSubscriptionController import EventSubscriptionController
from ConfigValidator.Config.Models.RunTableModel import RunTableModel
from ConfigValidator.Config.Models.FactorModel import FactorModel
from ConfigValidator.Config.Models.RunnerContext import RunnerContext
from ConfigValidator.Config.Models.OperationType import OperationType
from ProgressManager.Output.OutputProcedure import OutputProcedure as output
from ProgressManager.Validation.RequirementsValidator import (validate_experiment_requirements)

import shlex
from typing import Dict, Any, Optional
from pathlib import Path
from os.path import dirname, realpath
import subprocess
import os
import signal
import time
from Plugins.Profilers.JoularCore import JoularCore

mean = lambda lst: sum(lst) / len(lst) if lst else 0

class RunnerConfig:
    ROOT_DIR = Path(dirname(realpath(__file__)))

    name: str = "joularcore_example"
    default_output = ROOT_DIR / "experiments"
    results_output_path: Path = Path(os.getenv("EXPERIMENT_RUNNER_OUTPUT_PATH", str(default_output)))
    operation_type: OperationType = OperationType.AUTO
    time_between_runs_in_ms: int = 1000
    
    """Path to log file for energy validation report. Relative to experiment output directory."""
    energy_validation_log_file: str             = "energy_validation_report.log"

    # Dynamic configurations can be one-time satisfied here before the program takes the config as-is
    # e.g. Setting some variable based on some criteria
    def __init__(self):
        """Executes immediately after program start, on config load"""

        EventSubscriptionController.subscribe_to_multiple_events([
            (RunnerEvents.VALIDATE_EXPERIMENT, self.validate_experiment),
            (RunnerEvents.BEFORE_EXPERIMENT  , self.before_experiment),
            (RunnerEvents.BEFORE_RUN         , self.before_run       ),
            (RunnerEvents.START_RUN          , self.start_run        ),
            (RunnerEvents.START_MEASUREMENT  , self.start_measurement),
            (RunnerEvents.INTERACT           , self.interact         ),
            (RunnerEvents.STOP_MEASUREMENT   , self.stop_measurement ),
            (RunnerEvents.STOP_RUN           , self.stop_run         ),
            (RunnerEvents.POPULATE_RUN_DATA  , self.populate_run_data),
            (RunnerEvents.AFTER_EXPERIMENT   , self.after_experiment )
        ])
        self.run_table_model = None

        # Local run state
        self._target_proc: subprocess.Popen | None = None
        self._joular: JoularCore | None = None

        output.console_log("Custom config (attach PID) loaded")

    def create_run_table_model(self) -> RunTableModel:
        factor1 = FactorModel("example_factor1", ["t1", "t2"])
        factor2 = FactorModel("example_factor2", [True, False])
        self.run_table_model = RunTableModel(
            factors=[factor1, factor2],
            exclude_combinations=[],
            repetitions=1,
            data_columns=["avg_process_power", "avg_cpu_usage", "avg_cpu_power"]
        )
        return self.run_table_model
    def validate_experiment(self) -> None:
        output.console_log("Config.validate_experiment() called!")

    def before_experiment(self) -> None:
        output.console_log("Config.before_experiment() called!")

    def before_run(self) -> None:
        output.console_log("Config.before_run() called!")

    def start_run(self, context: RunnerContext) -> None:
        """
        Spawn the target here and store the PID in context so JoularCore can attach.
        """
        output.console_log("Config.start_run() called! Spawning target process...")

        # Example target: platform independent single-core utilization process
        cmd = "sleep 30"

        # Use a process group on POSIX so stop_run can clean up whole tree if needed
        self.target_process = subprocess.Popen(
            shlex.split(cmd),
            shell=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        output.console_log(f"Spawned target PID: {self.target_process.pid}")

        # Create JoularCore in "pid-only" mode (no target_program)
        joular_csv = Path(context.run_dir) / "joularcore.csv"
        self.profiler = JoularCore(
            out_file=joular_csv,
            pid=int(self.target_process.pid),
        )

    def start_measurement(self, context: RunnerContext) -> None:
        output.console_log("Config.start_measurement() called! Starting JoularCore...")
        # Start the JoularCore measurement
        self.profiler.start()

    def interact(self, context: RunnerContext) -> None:
        """
        Block until completion or a fixed time.
        """
        output.console_log("Config.interact() called! Letting target run for 5 seconds...")
        time.sleep(5)

    def stop_measurement(self, context: RunnerContext) -> None:
        output.console_log("Config.stop_measurement() called! Stopping JoularCore...")
        self.profiler.stop()

    def stop_run(self, context: RunnerContext) -> None:
        """
        Terminate the target process we spawned in start_run().
        """
        output.console_log("Config.stop_run() called! Terminating target process...")

        # Terminate the target process (through process group on POSIX)
        self.target_process.kill()

        self.target_process = None
    def populate_run_data(self, context: RunnerContext) -> Optional[Dict[str, Any]]:
        output.console_log("Config.populate_run_data() called!")
        jc_data = self.profiler.parse_log(self.profiler.logfile)

        return {"avg_process_power": mean(jc_data["Process Power (W)"].values()),
                "avg_cpu_usage": mean(jc_data["CPU Usage (%)"].values()),
                "avg_cpu_power": mean(jc_data["CPU Power (W)"].values())}

    def after_experiment(self) -> None:
        output.console_log("Config.after_experiment() called!")

    experiment_path: Path = None
