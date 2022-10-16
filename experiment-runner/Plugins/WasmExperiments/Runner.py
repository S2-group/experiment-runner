import string
from typing import Any, List
from subprocess import Popen, PIPE
from os import stat, kill, waitpid
from signal import SIGINT, SIGTERM, Signals
from os.path import join
from shlex import split
from time import sleep

from ConfigValidator.Config.Models.FactorModel import FactorModel
from ConfigValidator.Config.Models.RunnerContext import RunnerContext


class Runner:

    class RunnerConfig:
        pass

    def __init__(self) -> None:
        self.process = None

    @property
    def stdin(self) -> Any:
        return self.process.stdin

    @property
    def stdout(self) -> Any:
        return self.process.stdout

    @property
    def stderr(self) -> Any:
        return self.process.stderr

    @property
    def factors(self) -> List[FactorModel]:
        raise LookupError("\"factors\" is not implementented by this object!")

    def create_process(self, command: List[str]) -> None:
        self.reset()
        self.process = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE)

    def create_shell_process(self, command: string) -> None:
        self.reset()
        self.process = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)

    def wait_for_process(self):
        if self.process is not None:
            self.process.wait()

    def kill_process(self, signal: Signals):
        if self.process is not None:
            kill(self.process.pid, signal)
            self.wait_for_process()

    def reset(self) -> None:
        self.kill_process(SIGTERM)
        self.process = None

    def start(self, context: RunnerContext) -> None:
        self.reset()

    def interact(self, context: RunnerContext) -> None:
        raise LookupError("\"interact\" is not implementented by this object!")

    def stop(self) -> None:
        self.kill_process(SIGTERM)


RunnerConfig = Runner.RunnerConfig


class TimedRunner(Runner):

    class TimedRunnerConfig(RunnerConfig):
        pass

    def __init__(self) -> None:
        super(TimedRunner, self).__init__()
        
        self.subprocess_id = None
        self.time_output = None

    def create_timed_process(self, command: string, output_path: string = None) -> None:

        if output_path is not None:
            time_script = f"/usr/bin/time -o {output_path} {command} & echo $(pgrep -P $(echo $!))"
        else:
            time_script = f"/usr/bin/time {command} & echo $(pgrep -P $(echo $!))"

        self.create_shell_process(time_script)
        sleep(1) # TODO: Figure our good timing to avoid premature reading
        _ = self.stdout.readline() # skip default message by time

        self.subprocess_id = int(self.stdout.readline().strip())
        self.time_output = output_path

    def wait_for_subprocess(self):
        if self.subprocess_id is not None:
            try:
                waitpid(self.subprocess_id, 0)
            except:
                return

    def kill_subprocess(self, signal: Signals):
        if self.subprocess_id is not None:
            kill(self.subprocess_id, signal)
            self.wait_for_subprocess()

    def reset(self) -> None:
        self.kill_subprocess(SIGTERM)
        super(TimedRunner, self).reset()

        self.subprocess_id = None
        self.time_output = None

    def stop(self) -> None:
        self.kill_subprocess(SIGTERM)
        super(TimedRunner, self).stop()

    def report_time(self) -> float:
        raise LookupError("\"report\" is not implementented by this object!")


TimedRunnerConfig = TimedRunner.TimedRunnerConfig


class WasmRunner(TimedRunner):

    class WasmRunnerCofig(TimedRunnerConfig):
        # Optional
        DEBUG = True
        WASMER_PATH = "/path/to/wasmer"
        WASM_EDGE_PATH = "/path/to/wasm_edge"

        # Obligatory
        PROBLEM_DIR = "/path/to/problems/"
        ALGORITHMS = ["fannkuch_redux", "n_body", "mandelbrot", "k_nucleotide"]
        LANGUAGES = ["c", "rust", "javaScript", "go"]

        RUNTIME_PATHS = { "wasmer": WASMER_PATH, "wasmEdge": WASM_EDGE_PATH }
        RUNTIMES = RUNTIME_PATHS.keys()

        @classmethod
        def parameters(self, algorithm: string, language: string) -> string:
            # TODO: Implementation of executable-specific parameters
            return ""

    
    def __init__(self) -> None:
        super(WasmRunner, self).__init__()

        self.algorithms = FactorModel("algorithm", WasmRunnerCofig.ALGORITHMS)
        self.languages = FactorModel("language", WasmRunnerCofig.LANGUAGES)
        self.runtimes = FactorModel("runtime", WasmRunnerCofig.RUNTIMES)

    @property
    def factors(self) -> List[FactorModel]:
        return [self.algorithms, self.languages, self.runtimes]

    def start(self, context: RunnerContext) -> None:
        super(WasmRunner, self).start(context)

        output_path = join(context.run_dir, "runtime.csv")
        run_variation = context.run_variation

        algorithm = run_variation[self.algorithms.factor_name]
        language  = run_variation[self.languages.factor_name]
        runtime   = WasmRunnerCofig.RUNTIME_PATHS[run_variation[self.runtimes.factor_name]]

        executable = join(WasmRunnerCofig.PROBLEM_DIR, f"{algorithm}.{language}.wasm")
        parameters = WasmRunnerCofig.parameters(algorithm, language)
        command = f"{runtime} {executable} {parameters}"
        
        # CURRENTLY DISABLED AS I DON'T HAVE ALL EXECUTABLES YET
        # Not beautiful, but gets the job done...
        # There is no obvious way for this object to know that it is supposed to set the file size.
        # But as it is the only object ever touching the actual binary, this is the easiest thing to do
        #
        # executable_size = stat(executable).st_size
        # context.run_variation["storage"] = executable_size

        if WasmRunnerCofig.DEBUG:
            # DEBUG COMMAND
            print(f"Command: {command}")
            command = "stress --cpu 1"

        self.create_timed_process(command, output_path)

        if WasmRunnerCofig.DEBUG:
            # DEBUG COMMAND
            self.subprocess_id += 1 # because stress is annoying
            print(self.subprocess_id)

        return self.process, self.subprocess_id

    def interact(self, context: RunnerContext) -> None:
        # DEBUG INTERACTION
        if WasmRunnerCofig.DEBUG:
            sleep(3)
            return

        self.wait_for_subprocess()
        self.wait_for_process()

    def report_time(self) -> float:
        # TODO: Implementation parsing from self.time_output
        return 0.0
    

WasmRunnerCofig = WasmRunner.WasmRunnerCofig