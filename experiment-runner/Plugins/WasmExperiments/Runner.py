from typing import List
from os import stat, kill, waitpid
from signal import SIGINT, SIGTERM, Signals
from os.path import join
from time import sleep

from Plugins.WasmExperiments.ProcessManager import ProcessManager
from ConfigValidator.Config.Models.FactorModel import FactorModel
from ConfigValidator.Config.Models.RunnerContext import RunnerContext


class Runner(ProcessManager):

    class RunnerConfig:
        pass

    @property
    def factors(self) -> List[FactorModel]:
        raise LookupError("\"factors\" is not implementented by this object!")

    def start(self, context: RunnerContext) -> None:
        self.reset()

    def interact(self, context: RunnerContext) -> None:
        raise LookupError("\"interact\" is not implementented by this object!")


RunnerConfig = Runner.RunnerConfig


class TimedRunner(Runner):

    class TimedRunnerConfig(RunnerConfig):
        pass

    def __init__(self) -> None:
        super(TimedRunner, self).__init__()
        
        self.subprocess_id = None
        self.time_output = None

    def create_timed_process(self, command: str, output_path: str = None) -> None:

        if output_path is not None:
            time_script = f"/usr/bin/time -f 'User: %U, System: %S' -o {output_path} {command} & echo $(pgrep -P $(echo $!))"
        else:
            time_script = f"/usr/bin/time -f 'User: %U, System: %S'  {command} & echo $(pgrep -P $(echo $!))"

        self.create_shell_process(time_script)
        _ = self.stdout.readline() # skip default message of time binary

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
        def parameters(self, algorithm: str, language: str) -> str:
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
        
        # Not beautiful, but gets the job done...
        # There is no obvious way for this object to know that it is supposed to set the file size.
        # But as it is the only object ever touching the actual binary, this is the easiest thing to do
        if not WasmRunnerCofig.DEBUG:
            executable_size = stat(executable).st_size
            context.run_variation["storage"] = executable_size

        # DEBUG COMMAND
        if WasmRunnerCofig.DEBUG:
            print(f"Command: {command}")
            command = "stress --cpu 1"

        self.create_timed_process(command, output_path)

        # DEBUG COMMAND
        if WasmRunnerCofig.DEBUG:
            # because stress creates another subprocess, which *MOSTLY* has pid + 1
            self.subprocess_id += 1
            print(self.subprocess_id)

        return self.process, self.subprocess_id

    def interact(self, context: RunnerContext) -> None:
        # DEBUG INTERACTION
        if WasmRunnerCofig.DEBUG:
            sleep(3)
            return

        self.wait_for_subprocess()
        self.wait_for_process()

    def report_time(self) -> int:

        with open(self.time_output, "r") as file:
            line = file.readlines()[1].split()

        # calculate execution time in milliseconds
        user_time = int(float(line[1].strip(",")) * 1000)
        system_time = int(float(line[3].strip(",")) * 1000)
        execution_time = user_time + system_time

        return execution_time
    

WasmRunnerCofig = WasmRunner.WasmRunnerCofig