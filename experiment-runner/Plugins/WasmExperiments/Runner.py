import logging
import stat as lib_stat
from subprocess import Popen
from typing import List, Type, Tuple
from os import stat, kill, getcwd, chmod, remove
from signal import Signals
from os.path import join
from psutil import Process

from Plugins.WasmExperiments.ProcessManager import ProcessManager
from ConfigValidator.Config.Models.FactorModel import FactorModel
from ConfigValidator.Config.Models.RunnerContext import RunnerContext


class Runner(ProcessManager):
    class RunnerConfig:
        pass

    def __init__(self, config: Type[RunnerConfig] = RunnerConfig):
        self.config: Type[RunnerConfig] = config
        super(Runner, self).__init__()

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
        SCRIPT_PATH = join(getcwd(), "experiments/binaries/script.sh")

    def __init__(self, config: Type[TimedRunnerConfig] = TimedRunnerConfig) -> None:
        super(TimedRunner, self).__init__()
        self.config: Type[TimedRunnerConfig] = config
        self.subprocess_id: int = None
        self.time_output: str = None

    @property
    def has_subprocess(self) -> bool:
        return self.subprocess_id is not None

    def create_timed_process(self, command: str, output_path: str = None) -> None:

        script_path = self.config.SCRIPT_PATH
        with open(script_path, "w") as file:
            file.write(command)
        chmod(script_path, lib_stat.S_IRWXU | lib_stat.S_IRWXG | lib_stat.S_IRWXO)

        if output_path is not None:
            time_script = f"/usr/bin/time -f 'User: %U, System: %S' -o {output_path} {script_path}"
        else:
            time_script = f"/usr/bin/time -f 'User: %U, System: %S' {script_path}"

        self.shell_execute(time_script)

        shell_process = Process(self.process.pid)
        script_process = shell_process.children(recursive=True)[1]
        command_process = script_process.children(recursive=True)[0]

        self.subprocess_id = command_process.pid  # TODO: Figure our how to deal with multi-process environments
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
        WASM_TIME = "/home/pi/.wasmtime/bin/wasmtime"

        # Obligatory
        PROBLEM_DIR = join(getcwd(), "experiments/binaries")
        ALGORITHMS = ["binarytrees", "spectral-norm", "nbody"]
        LANGUAGES = ["rust", "javascript", "go", "c"]

        RUNTIME_PATHS = {"wasmer": WASMER_PATH, "wasmtime": WASM_TIME}
        RUNTIMES = list(RUNTIME_PATHS.keys())

        PARAMETERS = {"binarytrees": 18, "spectral-norm": 1900, "nbody": 5000000}

        @classmethod
        def pipe_command(cls, algorithm: str, language: str) -> str:
            value = str(cls.PARAMETERS[algorithm])

            if language == "javascript":
                return "echo '{\"n\": %s}' |" % value

            return ""

        @classmethod
        def arguments(cls, algorithm: str, language: str) -> str:
            if language == "javascript":
                return ""

            return str(cls.PARAMETERS[algorithm])

    def __init__(self) -> None:
        super(WasmRunner, self).__init__()
        self.config: Type[WasmRunnerConfig] = WasmRunnerConfig
        self.algorithms = FactorModel("algorithm", self.config.ALGORITHMS)
        self.languages = FactorModel("language", self.config.LANGUAGES)
        self.runtimes = FactorModel("runtime", self.config.RUNTIMES)

    @property
    def factors(self) -> List[FactorModel]:
        return [self.algorithms, self.languages, self.runtimes]

    def start(self, context: RunnerContext) -> Tuple[Popen, int]:
        super(WasmRunner, self).start(context)

        output_time_path = join(context.run_dir, "runtime.csv")
        run_variation = context.run_variation

        algorithm = run_variation[self.algorithms.factor_name]
        language = run_variation[self.languages.factor_name]
        runtime = self.config.RUNTIME_PATHS[run_variation[self.runtimes.factor_name]]

        executable = join(self.config.PROBLEM_DIR, f"{algorithm}.{language}.wasm")
        pipe_command = self.config.pipe_command(algorithm, language)
        arguments = self.config.arguments(algorithm, language)
        command = f"{pipe_command} {runtime} {executable} {arguments}".strip()

        print(f"\nAlgorithm: {algorithm}\nLanguage: {language}\nRuntime: {runtime}")
        print(f"Command: {command}\n")

        # Not beautiful, but gets the job done...
        # There is no obvious way for this object to know that it is supposed to set the file size.
        # But as it is the only object ever touching the actual binary, this is the easiest thing to do
        executable_size = stat(executable).st_size
        context.run_variation["storage"] = executable_size

        self.create_timed_process(command, output_time_path)

        return self.process, self.subprocess_id

    def interact(self, context: RunnerContext) -> None:
        self.wait()

    def stop(self) -> None:
        super(WasmRunner, self).stop()
        remove(self.config.SCRIPT_PATH)

    def report_time(self) -> int:

        with open(self.time_output, "r") as file:
            line = file.readlines()[0].split()

        # calculate execution time in milliseconds
        user_time = int(float(line[1].strip(",")) * 1000)
        system_time = int(float(line[3].strip(",")) * 1000)
        execution_time = user_time + system_time

        return execution_time


WasmRunnerConfig = WasmRunner.WasmRunnerConfig
