from subprocess import Popen, PIPE
from typing import List, Any
from signal import Signals, SIGTERM
from os import kill

class ProcessManager:

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

    def create_process(self, command: List[str]) -> None:
        self.reset()
        self.process = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE)

    def create_shell_process(self, command: str) -> None:
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

    def stop(self) -> None:
        self.kill_process(SIGTERM)