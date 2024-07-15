
from enum import Enum, auto
from pathlib import Path
from typing import Iterable

import codecarbon
import csv
import re

from ConfigValidator.Config.Models.RunnerContext import RunnerContext
from ConfigValidator.Config.RunnerConfig import RunnerConfig

class DataColumns(Enum):
    """For the description of data columns, see
      1. https://mlco2.github.io/codecarbon/output.html#id2
      2. https://github.com/mlco2/codecarbon/blob/master/codecarbon/output.py#L25
    """
    EMISSIONS         = auto()
    EMISSIONS_RATE    = auto()
    CPU_ENERGY        = auto()
    GPU_ENERGY        = auto()
    RAM_ENERGY        = auto()
    ENERGY_CONSUMED   = auto()

    _PATTERN = re.compile(r'(codecarbon__)(.+)') # group1: prefix, group2: name

    @property
    def name(self) -> str:
        return f'codecarbon__{super().name.lower()}'

def emission_tracker(online=False, *decargs, **deckwargs):
    def emission_tracker_decorator(cls: RunnerConfig.__class__):
        data_columns =  deckwargs.pop('data_columns', [DataColumns.EMISSIONS])

        cls.create_run_table_model  = add_data_columns(data_columns)(cls.create_run_table_model)
        cls.start_measurement       = start_emission_tracker(online=online, *decargs, **deckwargs)(cls.start_measurement)
        cls.stop_measurement        = stop_emission_tracker(cls.stop_measurement)
        cls.populate_run_data       = populate_data_columns(cls.populate_run_data)

        return cls
    return emission_tracker_decorator

def start_emission_tracker(online=False, *decargs, **deckwargs):
    def start_emission_tracker_decorator(func):
        def wrapper(*args, **kwargs):
            self: RunnerConfig = args[0]
            context: RunnerContext = args[1]

            if 'project_name' not in deckwargs:
                deckwargs['project_name'] = self.name
            if 'output_dir' not in deckwargs:
                deckwargs['output_dir'] = str(context.run_dir.resolve())
            codecarbon_cls = codecarbon.EmissionsTracker if online else codecarbon.OfflineEmissionsTracker

            self.__emission_tracker__ = codecarbon_cls(*decargs, **deckwargs)
            self.__emission_tracker__.start()
            return func(*args, **kwargs)
        return wrapper
    return start_emission_tracker_decorator

def stop_emission_tracker(func):
    def wrapper(*args, **kwargs):
        self: RunnerConfig = args[0]

        ret_val = func(*args, **kwargs)
        self.__emission_tracker__.stop()
        return ret_val
    return wrapper

def add_data_columns(data_cols: Iterable[DataColumns]):
    def add_data_columns_decorator(func):
        def wrapper(*args, **kwargs):
            self: RunnerConfig = args[0]

            func(*args, **kwargs)  # will set self.run_table_model
            for dc in data_cols:
                self.run_table_model.get_data_columns().append(dc.name)
            return self.run_table_model
        return wrapper
    return add_data_columns_decorator

def populate_data_columns(func):
    def wrapper(*args, **kwargs):
        self: RunnerConfig = args[0]

        ret_val = func(*args, **kwargs)
        if ret_val is None:
            ret_val = {}
        with open(Path(self.__emission_tracker__._output_dir) / Path(self.__emission_tracker__._output_file)) as csvfile:
            reader = csv.DictReader(csvfile)
            rows = [row for row in reader]
            assert(len(rows) == 1)
            data = rows[0]
            for dc in self.run_table_model.get_data_columns():
                m = DataColumns._PATTERN.value.match(dc)
                if m:
                    ret_val[dc] = float(data[m.group(2)])
        return ret_val
    return wrapper
