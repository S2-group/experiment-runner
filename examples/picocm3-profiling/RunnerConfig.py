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

import time
import subprocess
import shlex

from Plugins.Profilers.PicoCM3 import PicoCM3, CM3DataTypes, CM3Channels

# TODO
# Finish parsing / averaging the values to place in the results table
# Finish the documentation in 2 places
# Test the implementation
# Write actual test code to test the implementaiton

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
        
        self.latest_measurement = None
        self.run_table_model = None  # Initialized later
        output.console_log("Custom config loaded")

    def create_run_table_model(self) -> RunTableModel:
        """Create and return the run_table model here. A run_table is a List (rows) of tuples (columns),
        representing each run performed"""
        workers_factor = FactorModel("num_workers", [1, 2, 3, 4])
        write_factor = FactorModel("write_size", [256, 1024, 2048, 4096])

        self.run_table_model = RunTableModel(
            factors = [workers_factor, write_factor],
            data_columns=['timestamp', 'channel_1(A)', 'channel_2(off)', 'channel_3(off)']) # Channel 1 is in Amps

        return self.run_table_model

    def before_experiment(self) -> None:
        """Perform any activity required before starting the experiment here
        Invoked only once during the lifetime of the program."""

        # Setup the picolog cm3 here (the parameters passed are also the default)
        self.meter = PicoCM3(sample_frequency   = 1000, # Sample the CM3 every second
                             mains_setting      = 0,    # Account for 50hz mains frequency
                             # Which channels are enabled in what mode
                             channel_settings   = { CM3Channels.PLCM3_CHANNEL_1: CM3DataTypes.PLCM3_1_MILLIVOLT,
                                                    CM3Channels.PLCM3_CHANNEL_2: CM3DataTypes.PLCM3_OFF,
                                                    CM3Channels.PLCM3_CHANNEL_3: CM3DataTypes.PLCM3_OFF})

    def before_run(self) -> None:
        """Perform any activity required before starting a run.
        No context is available here as the run is not yet active (BEFORE RUN)"""
        pass

    def start_run(self, context: RunnerContext) -> None:
        """Perform any activity required for starting the run here.
        For example, starting the target system to measure.
        Activities after starting the run should also be performed here."""
        
        num_workers = context.run_variation['num_workers']
        write_size = context.run_variation['write_size']

        # Start stress-ng
        stress_cmd = f"sudo stress-ng \
                    --hdd {num_workers} \
                    --hdd-write-size {write_size} \
                    --hdd-ops 1000000 \
                    --hdd-dev /dev/sda1 \
                    --timeout 60s \
                    --metrics-brief"

        stress_log = open(f'{context.run_dir}/stress-ng-log.log', 'w')
        self.stress_ng = subprocess.Popen(shlex.split(stress_cmd), stdout=stress_log)

    def start_measurement(self, context: RunnerContext) -> None:
        """Perform any activity required for starting measurements."""
        
        num_workers = context.run_variation['num_workers']
        write_size = context.run_variation['write_size']
        
        # Start the picologs measurements here, create a unique log file for each
        self.latest_log = str(context.run_dir.resolve() / f'pico_run_{num_workers}_{write_size}.log')
        self.latest_measurement = self.meter.log(lambda: self.stress_ng.poll() != None, self.latest_log)
    
    def interact(self, context: RunnerContext) -> None:
        """Perform any interaction with the running target system here, or block here until the target finishes."""

        # Wait the maximum timeout for stress-ng to finish or time.sleep(60)
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

        run_data = {k: [] for k in self.run_table_model.data_columns}

        # Pass data through variables
        if self.latest_measurement != {}:
            for k, v in self.latest_measurement.items():
                    run_data['timestamp'].append(k)
                    run_data['channel_1(A)'].append(v[0][0])
                    run_data['channel_2(off)'].append(v[1][0])
                    run_data['channel_3(off)'].append(v[2][0])

        # Or through a log file
        else:
            with open(self.latest_log) as f:
                lines = f.readlines()

                for line in lines:
                    channel_vals = line.split(",")
                    
                    run_data['timestamp'].append(channel_vals[0])
                    run_data['channel_1(A)'].append(channel_vals[1].split(" ")[0])
                    run_data['channel_2(off)'].append(channel_vals[2].split(" ")[0])
                    run_data['channel_3(off)'].append(channel_vals[3].split(" ")[0])

        return run_data

    def after_experiment(self) -> None:
        """Perform any activity required after stopping the experiment here
        Invoked only once during the lifetime of the program."""
        pass

    # ================================ DO NOT ALTER BELOW THIS LINE ================================
    experiment_path:            Path             = None
