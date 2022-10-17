import logging
from subprocess import Popen, PIPE
from typing import List, Any
from signal import Signals, SIGTERM
from os import kill


class ProcessManager:

    def __init__(self, process: Popen = None) -> None:
        self.process: Popen = process

    @property
    def has_process(self) -> bool:
        return self.process is not None

    @property
    def is_running(self) -> bool:
        return self.has_process and self.process.poll() is not None

    @property
    def stdin(self) -> Any:
        return self.process.stdin

    @property
    def stdout(self) -> Any:
        return self.process.stdout

    @property
    def stderr(self) -> Any:
        return self.process.stderr

    def execute(self, command: List[str]) -> None:
        self.reset()
        self.process = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE)

    def shell_execute(self, command: str) -> None:
        self.reset()
        self.process = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)

    def wait(self) -> None:
        if self.has_process:
            self.process.wait()

    def send_signal(self, signal: Signals) -> None:
        if self.has_process:
            try:
                kill(self.process.pid, signal)
            except ProcessLookupError as e:
                logging.warning(f"Could not kill process {self.process.pid}: {e}")

    def kill(self, signal: Signals) -> None:
        self.send_signal(signal)
        self.wait()

    def stop(self) -> None:
        self.kill(SIGTERM)

    def reset(self) -> None:
        self.kill(SIGTERM)
        self.process = None
