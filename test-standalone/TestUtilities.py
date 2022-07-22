import importlib.util
import sys
from os.path import dirname, realpath
from pathlib import Path
from types import ModuleType
from typing import AnyStr


def get_test_dir(file: AnyStr) -> Path:
    return Path(dirname(realpath(file)))


def load_and_get_config_file_as_module(test_dir: Path) -> ModuleType:
    module_name = 'RunnerConfig'

    spec = importlib.util.spec_from_file_location(module_name, test_dir / f'{module_name}.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    return module
