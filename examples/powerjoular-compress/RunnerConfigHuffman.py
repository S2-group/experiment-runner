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
from datetime import datetime
import itertools

class RunnerConfig:
    ROOT_DIR = Path(dirname(realpath(__file__)))

    # ================================ USER SPECIFIC CONFIG ================================
    """The name of the experiment."""
    name:                       str             = "huffman_formal"
    # check the if the output path exists, if exists, add timestamp to the name
    if os.path.exists(ROOT_DIR / 'experiments' / name):
        # convert time to date and time
        name = name + "_" + time.strftime("%Y%m%d-%H%M%S")

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
        file_format_list = ['txt', 'pdf', 'jpg', 'png', 'mp4', 'flv']
        # file_format_list = ['mp4']
        file_size_list = ['small', 'large']
        # file_size_list = ['small']
        file_repetition_list = ['low', 'high']
        # file_repetition_list = ['high']
        num_list = [i for i in range(1, 51)]
        # num_list = [8]

        # make a permutation of all the factors
        data_type_factors = []
        for format in file_format_list:
            for size in file_size_list:
                for repetition in file_repetition_list:
                    for num in num_list:
                        factor = format + '-' + size + '-' + repetition + '-' + str(num)
                        data_type_factors.append(factor)
        print(data_type_factors)
        data_type_factor = FactorModel("data_type", data_type_factors)
        self.run_table_model = RunTableModel(
            factors = [data_type_factor],
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
        # remove compressed files from previous run, which is *.huffman
        # data_type = context.run_variation['data_type']
        # path_tmp = data_type.split('-')
        # file_path = path_tmp[0] + '/' + path_tmp[1] + '-' + path_tmp[2] + '/' + path_tmp[3]
        # subprocess.check_call(shlex.split(f'rm -rf {self.ROOT_DIR / "data2" / file_path / "*.huffman"}'))
        pass

    def start_run(self, context: RunnerContext) -> None:
        """Perform any activity required for starting the run here.
        For example, starting the target system to measure.
        Activities after starting the run should also be performed here."""
        
        # cpu_limit = context.run_variation['cpu_limit']
        data_type = context.run_variation['data_type']

        # start the target python
        # self.target = subprocess.Popen(['python', './compress_huffman.py', data_type],
        #     stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.ROOT_DIR,
        # )

        # C++ version
        # path_tmp = data_type.split('-')
        # file_path = path_tmp[0] + '/' + path_tmp[1] + '-' + path_tmp[2] + '/' + path_tmp[3]
        # data_path = "/home/roy/green-lab/experiment-runner/examples/powerjoular-compress/data2/" + file_path
        # sum_size = 0
        # files_str = ""
        # for file in os.listdir(data_path):
        #     if file.endswith(".huffman") or file.endswith(".lzw"):
        #         continue
        #     else:
        #         files_str += "./data2/" + file_path + "/" + file + " "
        # print(files_str)
        # self.target = subprocess.Popen("/home/roy/green-lab/Huffman-Coding/archive "+ files_str,
        #     stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.ROOT_DIR,
        # )

        # compress_cmd = "/home/roy/green-lab/Huffman-Coding/archive " + \
        #                "/home/roy/green-lab/experiment-runner/examples/powerjoular-compress/data2/mp4/large-high/10/6bgLZnwL0VQ.mp4 "
        data_path = "/home/roy/green-lab/experiment-runner/examples/powerjoular-compress/data/"
        path_tmp = data_type.split('-')
        file_path = path_tmp[0] + '/' + path_tmp[1] + '-' + path_tmp[2] + '/' + path_tmp[3]
        path = data_path + file_path
        cd_cmd = "cd " + path + "; "
        rm_cmd = "rm -rf *.huffman *.lzw .huffman .lzw; "
        final_cmd = cd_cmd + rm_cmd
        subprocess.Popen(final_cmd,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        # get all the files in the directory path
        files = os.listdir(path)
        files_cmd = ""
        for file in files:
            if file.endswith(".huffman") or file.endswith(".lzw"):
                continue
            else:
                files_cmd += file + " "
        compress_cmd = cd_cmd + "/home/roy/green-lab/Huffman-Coding/archive " + files_cmd
        print(compress_cmd)
        self.target = subprocess.Popen(compress_cmd,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)


        # self.target = subprocess.Popen(["/home/roy/green-lab/Huffman-Coding/archive",
        #                                 "~/green-lab/experiment-runner/examples/powerjoular-compress/data2/txt/small-low/3/8734.txt "],
        #                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.ROOT_DIR, shell=True)


        # Configure the environment based on the current variation
        # subprocess.check_call(shlex.split(f'cpulimit -b -p {self.target.pid} --limit {cpu_limit}'))
        

    def start_measurement(self, context: RunnerContext) -> None:
        """Perform any activity required for starting measurements."""
        # data_file_name = "powerjoular" + "-" + context.run_variation['data_type'] + ".csv"
        # # profiler_cmd = f'powerjoular -l -p {self.target.pid} -f {context.run_dir / data_file_name}'
        # profiler_cmd = f'powerjoular -l -f {context.run_dir / data_file_name}'
        # print(profiler_cmd)
        # time.sleep(1) # allow the process to run a little before measuring
        # self.profiler = subprocess.Popen(shlex.split(profiler_cmd))
        output_path = context.run_variation['data_type'] + ".csv"
        profiler_cmd = f'powerjoular -l -f {context.run_dir / output_path}'
        print(profiler_cmd)
        self.profiler = subprocess.Popen(shlex.split(profiler_cmd))

    def interact(self, context: RunnerContext) -> None:
        """Perform any interaction with the running target system here, or block here until the target finishes."""

        # No interaction. We just run it for XX seconds.
        # Another example would be to wait for the target to finish, e.g. via `self.target.wait()`
        # output.console_log("Running program for 20 seconds")
        # time.sleep(20)
        output.console_log("Waiting for program to finish")
        # while self.target.returncode != 0:
        #     time.sleep(1)
        # print("Program finished successfully")

        self.target.wait()
        # time.sleep(10)

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
        """Parse and process any measurement data2 here.
        You can also store the raw measurement data2 under `context.run_dir`
        Returns a dictionary with keys `self.run_table_model.data_columns` and their values populated"""

        # powerjoular.csv - Power consumption of the whole system
        # powerjoular.csv-PID.csv - Power consumption of that specific process
        data_type = context.run_variation['data_type']
        # rename the powerjoular.csv to powerjoular.csv-{data_type}.csv
        # os.rename(context.run_dir / "powerjoular.csv", context.run_dir / f"powerjoular-{data_type}.csv")
        # import pdb; pdb.set_trace()
        output_path = context.run_variation['data_type'] + ".csv"
        df = pd.read_csv(context.run_dir / output_path, sep=',', header=0)
        # create new columns for df: compression_ratio, compression_time, energy_efficiency
        # replace the '-' in data_type with '/' except for the last second one
        path_tmp = data_type.split('-')
        file_path = path_tmp[0] + '/' + path_tmp[1] + '-' + path_tmp[2] + '/' + path_tmp[3]
        # print("file_path: ", file_path)
        data_path = "/home/roy/green-lab/experiment-runner/examples/powerjoular-compress/data/" + file_path
        # print("data_path: ", data_path)
        # compute the sum size of files without extension huffman nor lzw
        sum_size = 0
        sum_size_huffman = 0
        for file in os.listdir(data_path):
            if file.endswith(".huffman"):
                sum_size_huffman += os.path.getsize(os.path.join(data_path, file))
            elif file.endswith(".lzw"):
                continue
            else:
                sum_size += os.path.getsize(os.path.join(data_path, file)) # unit Byte
        print("sum_size: ", sum_size, " sum_size_huffman: ", sum_size_huffman)
        # compute the compression ratio
        compression_ratio = sum_size / sum_size_huffman
        # compute the compression time
        start_time_str = df['Date'].iloc[0]
        end_time_str = df['Date'].iloc[-1]
        start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
        end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')
        compression_time = (end_time - start_time).total_seconds()
        # compute the saving size
        saving_size = (sum_size - sum_size_huffman) / 1024 # unit KB
        # sum the power in column 'Total Power'
        total_power = df['Total Power'].sum()
        # compute the cpu utilization average in column 'CPU Utilization'
        cpu_utilization = df['CPU Utilization'].mean()
        # compute the energy efficiency
        energy_efficiency = saving_size / (total_power*cpu_utilization)
        # append new columns compression_ratio, compression_time, energy_efficiency into df
        df['compression_ratio'] = compression_ratio
        df['compression_time'] = compression_time
        df['saving_size'] = saving_size
        df['total_power'] = total_power
        df['cpu_utilization'] = cpu_utilization
        df['energy_efficiency'] = energy_efficiency
        # save the df into csv file
        print(df)
        # save the df into original file
        df.to_csv(context.run_dir / output_path, index=False)
        print("finished: ", context.run_dir / output_path)

        data_path = "/home/roy/green-lab/experiment-runner/examples/powerjoular-compress/data/"
        path_tmp = data_type.split('-')
        file_path = path_tmp[0] + '/' + path_tmp[1] + '-' + path_tmp[2] + '/' + path_tmp[3]
        path = data_path + file_path
        cd_cmd = "cd " + path + "; "
        rm_cmd = "rm -rf *.huffman *.lzw .huffman .lzw"
        final_cmd = cd_cmd + rm_cmd
        subprocess.Popen(final_cmd,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        return df.to_dict()

    def after_experiment(self) -> None:
        """Perform any activity required after stopping the experiment here
        Invoked only once during the lifetime of the program."""
        pass

    # ================================ DO NOT ALTER BELOW THIS LINE ================================
    experiment_path:            Path             = None
