import logging
import os
from subprocess import Popen
from typing import List
from os import stat, kill, waitpid
from signal import SIGTERM, Signals
from os.path import join
from time import sleep
from psutil import Process

from Plugins.WasmExperiments.ProcessManager import ProcessManager
from ConfigValidator.Config.Models.FactorModel import FactorModel
from ConfigValidator.Config.Models.RunnerContext import RunnerContext


class Runner(ProcessManager):

    class RunnerConfig:
        pass

    @property
    def factors(self) -> List[FactorModel]:
        raise LookupError("\"factors\" is not implemented by this object!")

    def start(self, context: RunnerContext) -> None:
        self.reset()

    def interact(self, context: RunnerContext) -> None:
        raise LookupError("\"interact\" is not implemented by this object!")


RunnerConfig = Runner.RunnerConfig


class TimedRunner(Runner):

    class TimedRunnerConfig(RunnerConfig):
        pass

    def __init__(self) -> None:
        super(TimedRunner, self).__init__()
        
        self.subprocess: Process = None
        self.time_output: str = None

    def create_timed_process(self, command: str, output_path: str = None) -> None:

        if output_path is not None:
            time_script = f"/usr/bin/time -f 'User: %U, System: %S' -o {output_path} {command}"
        else:
            time_script = f"/usr/bin/time -f 'User: %U, System: %S' {command}"

        self.create_shell_process(time_script)
        children = Process(self.process.pid).children(recursive=False)

        self.subprocess = children[0]
        self.time_output = output_path

    def wait_for_subprocess(self):
        if self.subprocess is not None:
            self.subprocess.wait()

    def kill_subprocess(self, signal: Signals):
        if self.subprocess is not None:
            self.subprocess.send_signal(signal)
            self.wait_for_subprocess()

    def reset(self) -> None:
        self.kill_subprocess(SIGTERM)
        super(TimedRunner, self).reset()

        self.subprocess = None
        self.time_output = None

    def stop(self) -> None:
        self.kill_subprocess(SIGTERM)
        super(TimedRunner, self).stop()

    def report_time(self) -> float:
        raise LookupError("\"report\" is not implemented by this object!")


TimedRunnerConfig = TimedRunner.TimedRunnerConfig


class WasmRunner(TimedRunner):

    class WasmRunnerConfig(TimedRunnerConfig):
        # Optional
        DEBUG = False
        WASMER_PATH = "/home/pi/.wasmer/bin/wasmer"
        WASM_EDGE_PATH = "/usr/local/bin/wasmedge"

        # Obligatory
        PROBLEM_DIR = "/tmp/pycharm_project_960/experiments/binaries"
        #ALGORITHMS = ["binarytrees", "nbody", "spectral-norm"]
        ALGORITHMS = ["binarytrees"]
        #LANGUAGES = ["c", "rust", "javascript", "go"]
        LANGUAGES = ["go"]

        #RUNTIME_PATHS = { "wasmer": WASMER_PATH, "wasmEdge": WASM_EDGE_PATH }
        RUNTIME_PATHS = { "wasmer": WASMER_PATH }
        RUNTIMES = list(RUNTIME_PATHS.keys())

        @classmethod
        def parameters(cls, algorithm: str, language: str) -> str:
            if algorithm == "binarytrees":
                return "18"
            # if language == "javascript":
            #     if algorithm == "nbody":
            #         return '{"n": 1}'
            #     return "{}"
            return ""

    
    def __init__(self) -> None:
        super(WasmRunner, self).__init__()

        self.algorithms = FactorModel("algorithm", WasmRunnerConfig.ALGORITHMS)
        self.languages = FactorModel("language", WasmRunnerConfig.LANGUAGES)
        self.runtimes = FactorModel("runtime", WasmRunnerConfig.RUNTIMES)

    @property
    def factors(self) -> List[FactorModel]:
        return [self.algorithms, self.languages, self.runtimes]

    def start(self, context: RunnerContext) -> tuple[Popen, int]:
        super(WasmRunner, self).start(context)

        output_time_path = join(context.run_dir, "runtime.csv")
        run_variation = context.run_variation

        algorithm = run_variation[self.algorithms.factor_name]
        language  = run_variation[self.languages.factor_name]
        runtime   = WasmRunnerConfig.RUNTIME_PATHS[run_variation[self.runtimes.factor_name]]

        executable = join(WasmRunnerConfig.PROBLEM_DIR, f"{algorithm}.{language}.wasm")
        parameters = WasmRunnerConfig.parameters(algorithm, language)
        command = f"{runtime} {executable} {parameters}"
        
        # Not beautiful, but gets the job done...
        # There is no obvious way for this object to know that it is supposed to set the file size.
        # But as it is the only object ever touching the actual binary, this is the easiest thing to do
        if not WasmRunnerConfig.DEBUG:
            executable_size = stat(executable).st_size
            context.run_variation["storage"] = executable_size

        self.create_timed_process(command, output_time_path)

        self.subprocess.cpu_times()
        os.times()

        return self.process, self.subprocess

    def interact(self, context: RunnerContext) -> None:
        # DEBUG INTERACTION
        if WasmRunnerConfig.DEBUG:
            logging.warning("Debug sleep 3 seconds interact")
            sleep(3)
            return

        self.wait_for_subprocess()
        self.wait_for_process()

    def report_time(self) -> int:

        with open(self.time_output, "r") as file:
            line = file.readlines()[0].split()

        # calculate execution time in milliseconds
        user_time = int(float(line[1].strip(",")) * 1000)
        system_time = int(float(line[3].strip(",")) * 1000)
        execution_time = user_time + system_time

        return execution_time
    

WasmRunnerConfig = WasmRunner.WasmRunnerConfig