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
from statistics import mean

from Plugins.Profilers.PicoCM3 import PicoCM3, CM3DataTypes, CM3Channels

class RunnerConfig:
    ROOT_DIR = Path(dirname(realpath(__file__)))

    # ================================ USER SPECIFIC CONFIG ================================
    name:                       str             = "new_runner_experiment"
    results_output_path:        Path             = ROOT_DIR / 'experiments'
    operation_type:             OperationType   = OperationType.AUTO
    time_between_runs_in_ms:    int             = 1000

    def __init__(self):
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
        factor1 = FactorModel("example_factor1", ['example_treatment1', 'example_treatment2'])
        self.run_table_model = RunTableModel(
            factors = [factor1],
            data_columns=['timestamp', 'channel_1(avg)', 'channel_2(off)', 'channel_3(off)']) # Channel 1 is in Amps

        return self.run_table_model

    def before_experiment(self) -> None:
        # Setup the picolog cm3 here (the parameters passed are also the default)
        self.meter = PicoCM3(sample_frequency   = 1000, # Sample the CM3 every second
                             mains_setting      = 0,    # Account for 50hz mains frequency
                             channel_settings   = {     # Which channels are enabled in what mode
                                CM3Channels.PLCM3_CHANNEL_1.value: CM3DataTypes.PLCM3_1_MILLIVOLT.value,
                                CM3Channels.PLCM3_CHANNEL_2.value: CM3DataTypes.PLCM3_OFF.value,
                                CM3Channels.PLCM3_CHANNEL_3.value: CM3DataTypes.PLCM3_OFF.value})

        self.meter.open_device()

    def before_run(self) -> None:
        pass

    def start_run(self, context: RunnerContext) -> None:
        self.sleep = subprocess.Popen(["sleep", "10"])

    def start_measurement(self, context: RunnerContext) -> None:
        self.latest_log = str(context.run_dir.resolve() / 'picocm3.log')
        self.meter.log(finished_fn=lambda: self.sleep.poll() == None, logfile=self.latest_log)
    
    def interact(self, context: RunnerContext) -> None:
        # Wait the maximum timeout for stress-ng to finish or time.sleep(60)
        self.sleep.wait() 

    def stop_measurement(self, context: RunnerContext) -> None:
        # Wait for stress-ng to finish
        self.sleep.wait()

    def stop_run(self, context: RunnerContext) -> None:
        pass
    
    def populate_run_data(self, context: RunnerContext) -> Optional[Dict[str, Any]]:
        if self.latest_log == None:
            return {}

        log_data = self.meter.parse_log(self.latest_log)

        return {'timestamp': log_data['timestamp'][0] + " - " + log_data['timestamp'][-1],
                'channel_1(avg)': mean(log_data['channel_1']),
                'channel_2(off)': mean(log_data['channel_2']),
                'channel_3(off)': mean(log_data['channel_3'])}

    def after_experiment(self) -> None:
        # Close the connection to the unit
        self.meter.close_device()

    # ================================ DO NOT ALTER BELOW THIS LINE ================================
    experiment_path:            Path             = None
