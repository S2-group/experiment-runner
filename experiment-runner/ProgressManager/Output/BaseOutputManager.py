from pathlib import Path


class BaseOutputManager:

    def __init__(self, experiment_path: Path):
        self._experiment_path = experiment_path
