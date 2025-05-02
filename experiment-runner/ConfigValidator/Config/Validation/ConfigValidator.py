from pathlib import Path
from tabulate import tabulate
import os
import subprocess
import platform

from ExperimentOrchestrator.Misc.DictConversion import class_to_dict
from ExperimentOrchestrator.Misc.PathValidation import is_path_exists_or_creatable_portable
from ConfigValidator.Config.RunnerConfig import RunnerConfig
from ConfigValidator.Config.Models.OperationType import OperationType
from ConfigValidator.CustomErrors.ConfigErrors import (ConfigInvalidError, ConfigAttributeInvalidError)

class ConfigValidator:
    config_values_or_exception_dict: dict = {}
    error_found:                     bool = False

    @staticmethod
    def __check_expression(name, value, expected, expression):
        if expression(value, expected):
            ConfigValidator \
                .config_values_or_exception_dict[name] = str(ConfigValidator.config_values_or_exception_dict[name]) + \
                                                    f"\n\n{ConfigAttributeInvalidError(name, value, expected)}"
            ConfigValidator.error_found = True
    
 # Verifies that an energybridge executable is present, and can be executed without error
    @staticmethod
    def __validate_energibridge(config):
        # Do nothing if its not enabled
        if not config.self_measure:
            return

        if  not platform.system() == "Linux"    \
            or not os.path.exists(config.self_measure_bin)      \
            or not os.access(config.self_measure_bin, os.X_OK):

            ConfigValidator.error_found = True
            ConfigValidator \
            .config_values_or_exception_dict["EnergiBridge"] = "EnergiBridge executable was not present or valid"
        
        if  config.self_measure_logfile \
            and not is_path_exists_or_creatable_portable(config.self_measure_logfile):
            ConfigValidator.error_found = True
            ConfigValidator \
            .config_values_or_exception_dict["EnergiBridge"] = f"EnergiBridge logfile ({config.self_measure_logfile}) was not a valid path"
        
        # Test run to see if energibridge works
        try:
            eb_args = [config.self_measure_bin, "--summary", "-o", "/dev/null", "--", "sleep", "0.5"]
            p = subprocess.Popen(eb_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            stdout, stderr = p.communicate(timeout=5)

            if stderr or not stdout:
                ConfigValidator.error_found = True
                ConfigValidator \
                        .config_values_or_exception_dict["EnergiBridge"] = f"EnergiBridge error durring test:\n{stderr}"

            
            if "joules" not in stdout:
                ConfigValidator.error_found = True
                ConfigValidator \
                        .config_values_or_exception_dict["EnergiBridge"] = f"Unexpected output durring EnergiBridge test:\n{stdout}"


        except Exception as e:
            ConfigValidator.error_found = True
            ConfigValidator \
                    .config_values_or_exception_dict["EnergiBridge"] = f"Exception durring EnergiBridge test:\n{e}"
        
    @staticmethod
    def validate_config(config: RunnerConfig):

        # Runtime set experiment_path
        config.experiment_path = Path(str(config.results_output_path) + f"/{config.name}")
        if '~' in str(config.experiment_path):
            config.experiment_path = config.experiment_path.expanduser()
        
        # Set defaults to support configs without the self_measure parameter and friends
        if not hasattr(config, "self_measure"):
            config.self_measure = False

        if config.self_measure:
            if not hasattr(config, "self_measure_bin"):
                config.self_measure_bin = "/usr/local/bin/energibridge" # This is spesific to linux, might work for osx as well
            
            if not hasattr(config, "self_measure_logfile"):
                config.self_measure_logfile = None
            
        # Convert class to dictionary with utility method
        ConfigValidator.config_values_or_exception_dict = class_to_dict(config)

        # operation_type
        ConfigValidator.__check_expression('operation_type', config.operation_type, OperationType, 
                                (lambda a, b: not isinstance(type(a), type(b)))
                            )
        # time_between_runs_in_ms
        ConfigValidator.__check_expression('time_between_runs_in_ms', config.time_between_runs_in_ms, int,
                                (lambda a, b: not isinstance(a, b))
                            )

        # Results output path
        ConfigValidator.__check_expression("results_output_path", 
                            config.results_output_path,
                            Path,
                            (lambda a, b: not isinstance(a, b))
                        )

        ConfigValidator.__check_expression("results_output_path",
                            config.experiment_path,
                            "path must be valid and writable",
                            (lambda a, b: is_path_exists_or_creatable_portable(a))
                        )
        
        ConfigValidator.__validate_energibridge(config)

        # Display config in user-friendly manner, including potential errors found
        print(
            tabulate(
                ConfigValidator.config_values_or_exception_dict.items(),
                ['Key', 'Value'],
                tablefmt="rst"
            )
        )

        if ConfigValidator.error_found:
            raise ConfigInvalidError
