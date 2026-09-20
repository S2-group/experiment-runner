from EventManager.Models.RunnerEvents import RunnerEvents
from EventManager.EventSubscriptionController import EventSubscriptionController
from ConfigValidator.Config.Models.RunTableModel import RunTableModel
from ConfigValidator.Config.Models.FactorModel import FactorModel
from ConfigValidator.Config.Models.RunnerContext import RunnerContext
from ConfigValidator.Config.Models.OperationType import OperationType
from ProgressManager.Output.OutputProcedure import OutputProcedure as output
from ProgressManager.Validation.RequirementsValidator import (validate_experiment_requirements)
from Plugins.Profilers.AndroidDebugBridge import AndroidBatteryMonitor

from typing import Dict, List, Any, Optional
from pathlib import Path
from os.path import dirname, realpath
import time

class RunnerConfig:
    ROOT_DIR = Path(dirname(realpath(__file__)))

    # ================================ USER SPECIFIC CONFIG ================================
    """The name of the experiment."""
    name: str = "android_energy_monitoring_experiment"

    """The path in which Experiment Runner will create a folder with the name `self.name`"""
    results_output_path: Path = ROOT_DIR / 'experiments'

    """Experiment operation type"""
    operation_type: OperationType = OperationType.AUTO

    """Time between runs (cooldown period)"""
    time_between_runs_in_ms: int = 3000
    
    """Path to log file for energy validation report. Relative to experiment output directory."""
    energy_validation_log_file: str             = "energy_validation_report.log"
    
    # Dynamic configurations can be one-time satisfied here before the program takes the config as-is
    # e.g. Setting some variable based on some criteria
    def __init__(self):
        """Executes immediately after program start, on config load"""
        self.profiler = None 

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

        output.console_log("Android Energy Monitoring config loaded")

    def create_run_table_model(self) -> RunTableModel:
        """Define the experimental design with factors and data columns.
        """
        # Define experimental factors
        workload_factor = FactorModel("workload", ['light', 'medium', 'heavy'])
        screen_factor = FactorModel("screen_brightness", ['low', 'high'])
        
        self.run_table_model = RunTableModel(
            factors=[workload_factor, screen_factor],
            repetitions=1,
            data_columns=['workload_duration_ms', 'task_completion_status']
        )
        return self.run_table_model

    def validate_experiment(self) -> None:
        """Perform any experiment validation here. If any validation fails, raise an exception with details on the failure."""
        validate_experiment_requirements(Path(__file__))
        output.console_log("Config.validate_experiment() called!")

    def before_experiment(self):
        self.profiler = AndroidBatteryMonitor(
            device_serial=None,
            poll_interval=2
        )
        self.profiler.open_device()
        output.console_log("Android profiler initialized")

    def before_run(self) -> None:
        """Called before each run."""
        output.console_log(f"Preparing device for run...")

    def start_run(self, context):
        if self.profiler is None:
            self.profiler = AndroidBatteryMonitor(
                device_serial=None,
                poll_interval=2
            )
            self.profiler.open_device()

        self.profiler.logfile = (context.run_dir / "android_battery.csv")

    def start_measurement(self, context: RunnerContext) -> None:
        """Start measurement."""
        output.console_log("Energy monitoring started")
        self.profiler.start()

    def interact(self, context: RunnerContext):
        workload = context.execute_run['workload']
        brightness = context.execute_run['screen_brightness']

        duration_ms = {
            'light': 5000,
            'medium': 10000,
            'heavy': 15000
        }[workload]

        output.console_log(
            f"Running {workload} workload "
            f"for {duration_ms}ms "
            f"(brightness: {brightness})"
        )

        time.sleep(duration_ms / 1000)

        output.console_log("Workload completed")

    def stop_measurement(self, context: RunnerContext) -> None:
        """Stop measurement - energy monitoring ends here automatically."""
        output.console_log("Energy monitoring stopped")
        self.profiler.stop()

    def stop_run(self, context: RunnerContext) -> None:
        """Stop the current run."""
        output.console_log(f"Stopped run: {context.execute_run['__run_id']}")

    def populate_run_data(self, context: RunnerContext):
        battery_log = self.profiler.parse_log(self.profiler.logfile)
        workload = context.execute_run['workload']
        duration_ms = {
            'light':5000,
            'medium':10000,
            'heavy':15000
        }[workload]

        return {
            "workload_duration_ms": duration_ms,
            "task_completion_status": "success",
            "android_battery__battery_percentage":
                battery_log.get("android_battery__percentage", 0),
            "android_battery__battery_temperature":
                battery_log.get("android_battery__temperature", 0),
            "android_battery__battery_voltage":
                battery_log.get(
                    "android_battery__voltage",0),
            "android_battery__current_now":
                battery_log.get(
                    "android_battery__current_now",0),
            "android_battery__charge_counter":
                battery_log.get(
                    "android_battery__charge_counter",0),
            "android_battery__power_draw":
                battery_log.get("android_battery__power_draw",0)
        }

    def after_experiment(self) -> None:
        """Called after experiment completes."""
        output.console_log("Android energy monitoring experiment completed!")
        output.console_log(f"Results stored in {self.results_output_path}")

    # ================================ DO NOT ALTER BELOW THIS LINE ================================
    experiment_path: Path = None