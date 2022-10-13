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
    name:                       str             = "compare_wasm"

    """The path in which Experiment Runner will create a folder with the name `self.name`, in order to store the
    results from this experiment. (Path does not need to exist - it will be created if necessary.)
    Output path defaults to the config file's path, inside the folder 'experiments'"""
    results_output_path:        Path             = ROOT_DIR / 'experiments'

    """Experiment operation type. Unless you manually want to initiate each run, use `OperationType.AUTO`."""
    operation_type:             OperationType   = OperationType.AUTO

    """The time Experiment Runner will wait after a run completes.
    This can be essential to accommodate for cooldown periods on some systems."""
    time_between_runs_in_ms:    int             = 1000 # TODO: bit much, isn't it?

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

    """
    Idea: we will have all precompiled algorithms in the data folder
    - structure given by filename: ALG_NAME.
    
    We have:
    - runtime
        - wasmer
        - wasmEdge
    
    - four benchmarks
        - fannkuch-redux
        - n-body
        - mandelbrot
        - k-nucleotide
        
    - four languages
        - Rust
        - C
        - JS
        - Go
    """


    def create_run_table_model(self) -> RunTableModel:
        """Create and return the run_table model here. A run_table is a List (rows) of tuples (columns),
        representing each run performed"""
        factor_test = FactorModel("test", ["whatever"])
        factor_runtime = FactorModel("runtime", ["wasmer", "wasmEdge"])
        factor_algorithm = FactorModel("algorithm", ["fannkuch_redux", "n_body", "mandelbrot", "k_nucleotide"])
        factor_language = FactorModel("language", ["c", "rust", "javaScript", "go"])
        self.run_table_model = RunTableModel(
            #factors=[factor_runtime, factor_algorithm, factor_language],
            factors=[factor_test],
            data_columns=['energy_usage', 'execution_time', 'memory_usage', 'cpu_usage', 'storage']
        )
        return self.run_table_model

    def before_experiment(self) -> None:
        """Perform any activity required before starting the experiment here
        Invoked only once during the lifetime of the program."""

    def before_run(self) -> None:
        """Perform any activity required before starting a run.
        No context is available here as the run is not yet active (BEFORE RUN)"""
        pass

    def start_run(self, context: RunnerContext) -> None:
        """Perform any activity required for starting the run here.
        For example, starting the target system to measure.
        Activities after starting the run should also be performed here."""

        # TODO: select right binary and runtime
        file_name = "/tmp/pycharm_project_960/experiments/binaries/nbody.c.wasm"
        runtime = "/home/pi/.wasmer/bin/wasmer"

        # measure size of binary
        file_stats = os.stat(file_name)
        context.run_variation["storage"] = file_stats.st_size

        # TODO: set target to RUNTIME BINARY_ALGORITHM
        # start the target
        time = ["/usr/bin/time", "-f", "%C, %e", "-o", f"{context.run_dir}/runtime.csv"]
        runtime_command = [runtime, file_name, '--', '31211111']

        self.target = subprocess.Popen(runtime_command,  # TODO: set a per-benchmark input
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.ROOT_DIR,
        )

        # Configure the environment based on the current variation
        # does not apply
        

    def start_measurement(self, context: RunnerContext) -> None:
        """Perform any activity required for starting measurements."""
        profilers = []

        # config PS script and powerjoular
        profiler_cmd = f"ps -p {self.target.pid} --noheader -o '%cpu %mem'"
        powerjoular_cmd = f'powerjoular -l -p {self.target.pid} -f {context.run_dir / "powerjoular.csv"}'
        # TODO: name needs to be changed in smart way
        wrapper_script = f'while true; do {profiler_cmd}; sleep 1; done'

        time.sleep(1)  # allow the process to run a little before measuring
        profilers.append(subprocess.Popen(['sh', '-c', wrapper_script], stdout=subprocess.PIPE, stderr=subprocess.PIPE))
        profilers.append(subprocess.Popen(shlex.split(powerjoular_cmd)))

        self.profiler = profilers

    def interact(self, context: RunnerContext) -> None:
        """Perform any interaction with the running target system here, or block here until the target finishes."""

        # TODO: wait until it is finished
        self.target.wait()

    def stop_measurement(self, context: RunnerContext) -> None:
        """Perform any activity here required for stopping measurements."""
        for p in self.profiler:
            os.kill(p.pid, signal.SIGINT)
            p.wait()

    def stop_run(self, context: RunnerContext) -> None:
        """Perform any activity here required for stopping the run.
        Activities after stopping the run should also be performed here."""

        # shutdown runtime (if needed)
        self.target.kill()
        self.target.wait()
    
    def populate_run_data(self, context: RunnerContext) -> Optional[Dict[str, Any]]:
        """Parse and process any measurement data here.
        You can also store the raw measurement data under `context.run_dir`
        Returns a dictionary with keys `self.run_table_model.data_columns` and their values populated"""

        # TODO: parse PowerJoular data
        #with open(f"{context.run_dir}/runtime.csv") as time_file:
        #    reader = csv.reader(time_file, delimiter=',')
        #    exec_time = float(next(reader)[1].strip())

        # TODO: parse PS data

        # powerjoular.csv - Power consumption of the whole system
        # powerjoular.csv-PID.csv - Power consumption of that specific process
        df = pd.read_csv(context.run_dir / f"powerjoular.csv-{self.target.pid}.csv")
        df_ps = pd.DataFrame(columns=['cpu_usage', 'memory_usage'])
        for i, l in enumerate(self.profiler[0].stdout.readlines()):  # TODO: depends on order + is cryptic
            decoded_line = l.decode('ascii').strip()
            decoded_arr = decoded_line.split("  ")
            cpu_usage = float(decoded_arr[0])
            mem_usage = float(decoded_arr[1])
            df_ps.loc[i] = [cpu_usage, mem_usage]

        df.to_csv(context.run_dir / 'raw_data.csv', index=False)
        run_data = {
            'cpu_usage': round(df_ps['cpu_usage'].mean(), 3),
            'memory_usage': round(df_ps['memory_usage'].mean(), 3),  # TODO: still not shown properly
            'energy_usage': round(df['CPU Power'].sum(), 3),
            'execution_time': 'TODO',
        }
        return run_data

    def after_experiment(self) -> None:
        """Perform any activity required after stopping the experiment here
        Invoked only once during the lifetime of the program."""
        pass

    # ================================ DO NOT ALTER BELOW THIS LINE ================================
    experiment_path:            Path             = None
