from typing import Dict

from ProgressManager.Output.CSVOutputManager import CSVOutputManager
from pathlib import Path
from abc import ABC, abstractmethod
from multiprocessing import Event

from ConfigValidator.Config.RunnerConfig import RunnerConfig
from ConfigValidator.Config.Models.RunnerContext import RunnerContext

class IRunController(ABC):
    run_dir: Path = None
    current_run: int = None
    variation: Dict = None
    config: RunnerConfig = None
    run_context: RunnerContext = None
    data_manager: CSVOutputManager = None

    def __init__(self, variation: Dict, config: RunnerConfig, current_run: int, total_runs: int):
        self.run_dir = config.experiment_path / variation['__run_id']
        self.run_dir.mkdir(parents=True, exist_ok=True)

        self.variation = variation
        self.config = config
        self.current_run = current_run
        self.run_context = RunnerContext(self.variation, self.current_run, self.run_dir)
        self.data_manager = CSVOutputManager(self.config.experiment_path)

        self.run_completed_event = Event()

        print(f"\n-----------------NEW RUN [{current_run} / {total_runs}]-----------------\n")

    @abstractmethod
    def do_run(self):
        pass
