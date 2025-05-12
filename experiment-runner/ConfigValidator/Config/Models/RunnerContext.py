from pathlib import Path


class RunnerContext:

    def __init__(self, execute_run: dict, run_nr: int, run_dir: Path):
        self.execute_run = execute_run
        self.run_nr = run_nr
        self.run_dir = run_dir
