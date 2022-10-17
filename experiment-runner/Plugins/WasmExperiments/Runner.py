import logging
from subprocess import Popen
from typing import List
from os import stat, kill
from signal import Signals
from os.path import join
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
        self.subprocess_id: int = None
        self.time_output: str = None

    @property
    def has_subprocess(self) -> bool:
        return self.subprocess_id is not None

    def create_timed_process(self, command: str, output_path: str = None) -> None:

        if output_path is not None:
            time_script = f"/usr/bin/time -f 'User: %U, System: %S' -o {output_path} {command}"
        else:
            time_script = f"/usr/bin/time -f 'User: %U, System: %S' {command}"

        self.shell_execute(time_script)
        children = Process(self.process.pid).children(recursive=True)

        self.subprocess_id = children[1].pid  # TODO: Figure our how to deal with multi-process environments
        self.time_output = output_path

    def send_signal(self, signal: Signals) -> None:
        if self.has_subprocess:
            try:
                kill(self.subprocess_id, signal)
            except ProcessLookupError as e:
                logging.warning(f"Could not kill subprocess {self.subprocess_id}: {e}")

        if self.is_running:
            super(TimedRunner, self).send_signal(signal)

    def reset(self) -> None:
        super(TimedRunner, self).reset()
        self.subprocess_id = None
        self.time_output = None

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
        # ALGORITHMS = ["binarytrees", "nbody", "spectral-norm"]
        ALGORITHMS = ["binarytrees"]
        # LANGUAGES = ["c", "rust", "javascript", "go"]
        LANGUAGES = ["rust", "go"]

        # RUNTIME_PATHS = {"wasmer": WASMER_PATH, "wasmEdge": WASM_EDGE_PATH}
        RUNTIME_PATHS = {"wasmer": WASMER_PATH}
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
        executable_size = stat(executable).st_size
        context.run_variation["storage"] = executable_size

        self.create_timed_process(command, output_time_path)

        return self.process, self.subprocess_id

    def interact(self, context: RunnerContext) -> None:
        self.wait()

    def report_time(self) -> int:

        with open(self.time_output, "r") as file:
            line = file.readlines()[0].split()

        # calculate execution time in milliseconds
        user_time = int(float(line[1].strip(",")) * 1000)
        system_time = int(float(line[3].strip(",")) * 1000)
        execution_time = user_time + system_time

        return execution_time
    

WasmRunnerConfig = WasmRunner.WasmRunnerConfig
