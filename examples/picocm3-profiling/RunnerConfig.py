from EventManager.Models.RunnerEvents import RunnerEvents
from EventManager.EventSubscriptionController import EventSubscriptionController
from ConfigValidator.Config.Models.RunTableModel import RunTableModel
from ConfigValidator.Config.Models.FactorModel import FactorModel
from ConfigValidator.Config.Models.RunnerContext import RunnerContext
from ConfigValidator.Config.Models.OperationType import OperationType
from ProgressManager.Output.OutputProcedure import OutputProcedure as output

from typing import Dict, Any, Optional
from pathlib import Path
from os.path import dirname, realpath

import subprocess
import shlex
from statistics import mean

from Plugins.Profilers.PicoCM3 import PicoCM3, CM3DataTypes, CM3Channels

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
        
        self.latest_log = None
        self.run_table_model = None  # Initialized later
        output.console_log("Custom config loaded")

    def create_run_table_model(self) -> RunTableModel:
        """Create and return the run_table model here. A run_table is a List (rows) of tuples (columns),
        representing each run performed"""
        workers_factor = FactorModel("num_workers", [2, 4])
        write_factor = FactorModel("write_size", [1024, 4096])

        self.run_table_model = RunTableModel(
            factors = [workers_factor, write_factor],
            data_columns=['timestamp', 'channel_1(avg)', 'channel_2(off)', 'channel_3(off)']) # Channel 1 is in Amps

        return self.run_table_model

    def before_experiment(self) -> None:
        """Perform any activity required before starting the experiment here
        Invoked only once during the lifetime of the program."""

        # Setup the picolog cm3 here (the parameters passed are also the default)
        self.meter = PicoCM3(sample_frequency   = 1000, # Sample the CM3 every second
                             mains_setting      = 0,    # Account for 50hz mains frequency
                             channel_settings   = {     # Which channels are enabled in what mode
                                CM3Channels.PLCM3_CHANNEL_1.value: CM3DataTypes.PLCM3_1_MILLIVOLT.value,
                                CM3Channels.PLCM3_CHANNEL_2.value: CM3DataTypes.PLCM3_OFF.value,
                                CM3Channels.PLCM3_CHANNEL_3.value: CM3DataTypes.PLCM3_OFF.value})
        # Open the device
        self.meter.open_device()
        
    def before_run(self) -> None:
        """Perform any activity required before starting a run.
        No context is available here as the run is not yet active (BEFORE RUN)"""
        pass

    def start_run(self, context: RunnerContext) -> None:
        """Perform any activity required for starting the run here.
        For example, starting the target system to measure.
        Activities after starting the run should also be performed here."""
        
        num_workers = context.execute_run['num_workers']
        write_size = context.execute_run['write_size']

        # Start stress-ng
        stress_cmd = f"sudo stress-ng \
                    --hdd {num_workers} \
                    --hdd-write-size {write_size} \
                    --hdd-ops 1000000 \
                    --hdd-dev /dev/sda1 \
                    --timeout 60s \
                    --metrics-brief"

        stress_log = open(f'{context.run_dir}/stress-ng.log', 'w')
        self.stress_ng = subprocess.Popen(shlex.split(stress_cmd), stdout=stress_log)

    def start_measurement(self, context: RunnerContext) -> None:
        """Perform any activity required for starting measurements."""
        
        # Start the picologs measurements here, create a unique log file for each (or pass the values through a variable)
        self.latest_log = str(context.run_dir.resolve() / 'picocm3.log')
        self.meter.log(finished_fn=lambda: self.stress_ng.poll() == None, logfile=self.latest_log)
    
    def interact(self, context: RunnerContext) -> None:
        """Perform any interaction with the running target system here, or block here until the target finishes."""

        # Wait for stress-ng to finish or time.sleep(60)
        self.stress_ng.wait() 

    def stop_measurement(self, context: RunnerContext) -> None:
        """Perform any activity here required for stopping measurements."""
        
        # Wait for stress-ng to finish
        self.stress_ng.wait()

    def stop_run(self, context: RunnerContext) -> None:
        """Perform any activity here required for stopping the run.
        Activities after stopping the run should also be performed here."""
        pass
    
    def populate_run_data(self, context: RunnerContext) -> Optional[Dict[str, Any]]:
        """Parse and process any measurement data here.
        You can also store the raw measurement data under `context.run_dir`
        Returns a dictionary with keys `self.run_table_model.data_columns` and their values populated"""

        if self.latest_log == None:
            return {}
        
        # Read data from the relavent CM3 log
        log_data = self.meter.parse_log(self.latest_log)

        return {'timestamp': log_data['timestamp'][0] + " - " + log_data['timestamp'][-1],
                'channel_1(avg)': mean(log_data['channel_1']),
                'channel_2(off)': mean(log_data['channel_2']),
                'channel_3(off)': mean(log_data['channel_3'])}

    def after_experiment(self) -> None:
        """Perform any activity required after stopping the experiment here
        Invoked only once during the lifetime of the program."""
        
        # This must always be run
        self.meter.close_device()

    # ================================ DO NOT ALTER BELOW THIS LINE ================================
    experiment_path:            Path             = None
