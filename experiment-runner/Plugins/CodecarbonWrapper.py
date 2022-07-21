############################################### codecarbon plugin ###############################################
#
# pip install codecarbon
# Relevant issues:
#  * "AttributeError: Jumbotron was deprecated in dash-bootstrap-components version 1.0.0." - https://github.com/mlco2/codecarbon/issues/319
#  * "Unable to read Intel RAPL files for CPU power : Permission denied" https://github.com/mlco2/codecarbon/issues/244
# To find country codes, use the ISO 3166-1 Alpha-3 code from https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes
#
#################################################################################################################

import codecarbon

from ConfigValidator.Config.Models.RunnerContext import RunnerContext
from ConfigValidator.Config.RunnerConfig import RunnerConfig

def emission_tracker(online=False, *decargs, **deckwargs):
    def emission_tracker_decorator(cls):
        cls.create_run_table  = add_co2_data_column(cls.create_run_table)
        cls.start_measurement = start_emission_tracker(online=online, *decargs, **deckwargs)(cls.start_measurement)
        cls.stop_measurement  = stop_emission_tracker(cls.stop_measurement)
        cls.populate_run_data = populate_co2_data(cls.populate_run_data)

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
        self.__emissions__ = self.__emission_tracker__.stop()  # store it for usage later
        return ret_val
    return wrapper

def add_co2_data_column(func):
    def wrapper(*args, **kwargs):
        self: RunnerConfig = args[0]

        func(*args, **kwargs)  # will set self.run_table_model. Discard result
        self.run_table_model.get_data_columns().insert(2, '__co2_emissions')
        return self.run_table_model.generate_experiment_run_table()  # FIXME: this is bad
    return wrapper

def populate_co2_data(func):
    def wrapper(*args, **kwargs):
        self: RunnerConfig = args[0]

        ret_val = func(*args, **kwargs)
        ret_val['__co2_emissions'] = self.__emissions__

        return ret_val
    return wrapper
