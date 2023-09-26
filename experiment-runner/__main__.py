import sys
import traceback
import dill as pickle
import hashlib
import ast
from typing import List
from importlib import util
import multiprocessing

from ConfigValidator.Config.Models.Metadata import Metadata
from ConfigValidator.CustomErrors.BaseError import BaseError
from ConfigValidator.CLIRegister.CLIRegister import CLIRegister
from ConfigValidator.Config.Validation.ConfigValidator import ConfigValidator
from ConfigValidator.CustomErrors.ConfigErrors import ConfigInvalidClassNameError
from ExperimentOrchestrator.Experiment.ExperimentController import ExperimentController

def is_no_argument_given(args: List[str]): return (len(args) == 1)
def is_config_file_given(args: List[str]): return (args[1][-3:] == '.py')
def load_and_get_config_file_as_module(args: List[str]):
    module_name = args[1].split('/')[-1].replace('.py', '')
    spec = util.spec_from_file_location(module_name, args[1]) 
    config_file = util.module_from_spec(spec)
    sys.modules[module_name] = config_file
    spec.loader.exec_module(config_file)
    return config_file

def calc_ast_md5sum(src, name):
    tree = compile(src, name, 'exec', flags=ast.PyCF_ONLY_AST, optimize=0)

    for node in ast.walk(tree):
        # Ignores empty lines and comment only lines
        if hasattr(node, 'lineno'):
            setattr(node, 'lineno', 0)
        if hasattr(node, 'col_offset'):
            setattr(node, 'col_offset', 0)
        if hasattr(node, 'end_lineno'):
            setattr(node, 'end_lineno', 0)
        if hasattr(node, 'end_col_offset'):
            setattr(node, 'end_col_offset', 0)

        # Ignore docstring
        if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef, ast.ClassDef, ast.Module)) and ast.get_docstring(node) is not None:
            docstring_node = node.body[0].value
            if isinstance(docstring_node, ast.Str):
                docstring_node.s = ''
            elif isinstance(docstring_node, ast.Constant) and isinstance(docstring_node.value, str):
                docstring_node.value = ''

    return hashlib.md5(pickle.dumps(tree)).digest()


if __name__ == "__main__":
    try: 
        if is_no_argument_given(sys.argv):
            sys.argv.append('help')
            CLIRegister.parse_command(sys.argv)
        elif is_config_file_given(sys.argv):                                # If the first argument ends with .py -> a config file is entered
            multiprocessing.set_start_method('fork')                        # Set "fork" as the default method for spawning new processes 
                                                                            # (in this way the new processes will have a shared context when running)                   
            config_file = load_and_get_config_file_as_module(sys.argv)

            if hasattr(config_file, 'RunnerConfig'):
                config = config_file.RunnerConfig()                         # Instantiate config from injected file
                metadata = Metadata(
                    calc_ast_md5sum(pickle.source.getsource(config_file), sys.argv[1])  # hash of the whole file, not just RunnerConfig
                )

                ConfigValidator.validate_config(config)                     # Validate config as a valid RunnerConfig
                ExperimentController(config, metadata).do_experiment()      # Instantiate controller with config and start experiment
            else:
                raise ConfigInvalidClassNameError
        else:                                                               # Else, a utility command is entered
            CLIRegister.parse_command(sys.argv)
    except BaseError as e:                                                  # All custom errors are displayed in custom format
        print(f"\n{e}")
        sys.exit(1)
    except:                                                                 # All non-covered errors are displayed normally
        traceback.print_exc()
        sys.exit(1)