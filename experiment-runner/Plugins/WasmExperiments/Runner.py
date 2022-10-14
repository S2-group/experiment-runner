import string
from typing import Any, List
from subprocess import Popen, PIPE
from os import kill
from signal import SIGINT
from os import stat
from os.path import join
from time import sleep

from ConfigValidator.Config.Models.FactorModel import FactorModel
from ConfigValidator.Config.Models.RunnerContext import RunnerContext


class Runner:

    class RunnerConfig:
        pass

    def __init__(self) -> None:
        self.process = None
        self.time_output = None

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
        self.process = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE)

    def create_timed_process(self, command: string, output_path: string = None) -> int:

        self.time_output = output_path

        if self.time_output is not None:
            time_script = f"/usr/bin/time -f %C -o {self.time_output} '{command}' & time_pid=$!; echo $(pgrep -P $timepid)"
        else:
            time_script = f"/usr/bin/time -f %C '{command}' & time_pid=$!; echo $(pgrep -P $timepid)"

        #/usr/bin/time -f %C 'stess --cpu 1' & time_pid=$!; echo $(pgrep -P $timepid)

        self.create_process(["sh", "-c", time_script])
        sleep(2)

        self.stdout.flush()
        subprocess_id = self.stdout.readlines()
        print(subprocess_id)

        return int(subprocess_id)

    def reset(self) -> None:
        if self.process is not None:
            self.process.kill()
            self.process.wait()

        self.process = None
        self.time_output = None

    def start(self, context: RunnerContext) -> None:
        self.reset()

    def interact(self, context: RunnerContext) -> None:
        raise LookupError("\"interact\" is not implementented by this object!")

    def stop(self) -> None:
        kill(self.process.pid, SIGINT)
        self.process.wait()

    def report_time(self) -> float:
        raise LookupError("\"report\" is not implementented by this object!")


RunnerConfig = Runner.RunnerConfig


class WasmRunner(Runner):

    class WasmRunnerCofig(RunnerConfig):
        # Optional
        WASMER = "/path/to/wasmer"
        WASM_EDGE = "/path/to/wasm_edge"

        # Obligatory
        PROBLEM_DIR = "/path/to/problems/"
        ALGORITHMS = ["fannkuch_redux", "n_body", "mandelbrot", "k_nucleotide"]
        LANGUAGES = ["c", "rust", "javaScript", "go"]
        RUNTIMES = [WASMER, WASM_EDGE]

        @classmethod
        def parameters(self, algorithm: string, language: string) -> string:
            # TODO: Implementation
            return ""

    
    def __init__(self) -> None:
        super(WasmRunner, self).__init__()

        self.algorithms = FactorModel("algorithm", WasmRunnerCofig.ALGORITHMS)
        self.languages = FactorModel("language", WasmRunnerCofig.LANGUAGES)
        self.runtimes = FactorModel("runtime", WasmRunnerCofig.RUNTIMES)

        self.subprocess_pid: int = None

    @property
    def factors(self) -> List[FactorModel]:
        return [self.algorithms, self.languages, self.runtimes]

    def reset(self) -> None:
        super(WasmRunner, self).reset()
        self.subprocess_id = None

    def start(self, context: RunnerContext) -> None:
        super(WasmRunner, self).start(context)

        output_path = join(context.run_dir, "runtime.csv")
        run_variation = context.run_variation

        algorithm = run_variation[self.algorithms.factor_name]
        language  = run_variation[self.languages.factor_name]
        runtime   = run_variation[self.runtimes.factor_name]

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

        # DEBUG COMMAND
        print(f"Command: {command}")
        command = "stress --cpu 1"

        self.subprocess_id = self.create_timed_process(command, output_path)
        return self.process, self.subprocess_pid

    def interact(self, context: RunnerContext) -> None:
        # DEBUG INTERACTION
        sleep(10)
        return

        self.process.wait()

    def report_time(self) -> float:
        # TODO: Implementation
        return 0.0
    

WasmRunnerCofig = WasmRunner.WasmRunnerCofig