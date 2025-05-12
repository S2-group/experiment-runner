from EventManager.Models.RunnerEvents import RunnerEvents
from EventManager.EventSubscriptionController import EventSubscriptionController
from ConfigValidator.Config.Models.RunTableModel import RunTableModel
from ConfigValidator.Config.Models.FactorModel import FactorModel
from ConfigValidator.Config.Models.RunnerContext import RunnerContext
from ConfigValidator.Config.Models.OperationType import OperationType
from ProgressManager.Output.OutputProcedure import OutputProcedure as output
from Plugins.Profilers.NvidiaML import NvidiaML, NVML_Sample, NVML_Field, NVML_GPU_Operation_Mode, NVML_IDs, NVML_Dynamic_Query

from typing import Dict, List, Any, Optional
from pathlib import Path
import numpy as np
import time
from os.path import dirname, realpath


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
        # Create the experiment run table with factors, and desired data columns
        factor1 = FactorModel("test_factor", [1, 2])
        self.run_table_model = RunTableModel(
            factors = [factor1],
            data_columns=["avg_enc", "avg_dec", "avg_pstate"])
        
        return self.run_table_model

    def before_experiment(self) -> None:
        """Perform any activity required before starting the experiment here
        Invoked only once during the lifetime of the program."""

        self.profiler = NvidiaML(queries=[NVML_Dynamic_Query.NVML_PERFORMANCE_STATE],
                                 fields=[NVML_Field.NVML_FI_DEV_POWER_INSTANT,
                                         NVML_Field.NVML_FI_DEV_TOTAL_ENERGY_CONSUMPTION],
                                 samples=[NVML_Sample.NVML_ENC_UTILIZATION_SAMPLES,
                                          NVML_Sample.NVML_DEC_UTILIZATION_SAMPLES],
                                 settings={"GpuOperationMode": (NVML_GPU_Operation_Mode.NVML_GOM_ALL_ON,)})

        # Show stats about available GPUs
        devices = self.profiler.list_devices(print_dev=True)

        # Open the driver for the device we want to use
        self.profiler.open_device(0, NVML_IDs.NVML_ID_INDEX)

    def before_run(self) -> None:
        """Perform any activity required before starting a run.
        No context is available here as the run is not yet active (BEFORE RUN)"""
        pass

    def start_run(self, context: RunnerContext) -> None:
        """Perform any activity required for starting the run here.
        For example, starting the target system to measure.
        Activities after starting the run should also be performed here."""

        self.profiler.logfile = context.run_dir / "nvml_log.json"

        # Start your GPU based target program here

    def start_measurement(self, context: RunnerContext) -> None:
        """Perform any activity required for starting measurements."""
        self.profiler.start()

    def interact(self, context: RunnerContext) -> None:
        """Perform any interaction with the running target system here, or block here until the target finishes."""
        time.sleep(5)

    def stop_measurement(self, context: RunnerContext) -> None:
        """Perform any activity here required for stopping measurements."""
        log_data = self.profiler.stop()

    def stop_run(self, context: RunnerContext) -> None:
        """Perform any activity here required for stopping the run.
        Activities after stopping the run should also be performed here."""
        
        # Stop your GPU based target here

    def populate_run_data(self, context: RunnerContext) -> Optional[Dict[str, Any]]:
        """Parse and process any measurement data here.
        You can also store the raw measurement data under `context.run_dir`
        Returns a dictionary with keys `self.run_table_model.data_columns` and their values populated"""
        
        nvml_log = self.profiler.parse_log(self.profiler.logfile, remove_errors=True)

        # Aggregate some data for results
        return {
            "avg_enc": 0 if len(nvml_log["enc_utilization_samples"]) == 0
                       else np.mean(list(map(lambda x: x[1], nvml_log["enc_utilization_samples"]))),
            "avg_dec": 0 if len(nvml_log["dec_utilization_samples"]) == 0
                       else np.mean(list(map(lambda x: x[1], nvml_log["dec_utilization_samples"]))),
            "avg_pstate": 0 if len(nvml_log["NVML_PERFORMANCE_STATE"]) == 0
                       else np.mean(list(map(lambda x: x[1], nvml_log["NVML_PERFORMANCE_STATE"]))),
        }

    def after_experiment(self) -> None:
        """Perform any activity required after stopping the experiment here
        Invoked only once during the lifetime of the program."""

        # This also gets called when the object is garbase collected
        self.profiler.close_device()

    # ================================ DO NOT ALTER BELOW THIS LINE ================================
    experiment_path:            Path             = None
