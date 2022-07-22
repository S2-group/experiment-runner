
import csv

from ConfigValidator.Config.RunnerConfig import RunnerConfig as OriginalRunnerConfig
from ProgressManager.Output.CSVOutputManager import CSVOutputManager
from ProgressManager.RunTable.Models.RunProgress import RunProgress

import TestUtilities

if __name__ == 'main':
    TEST_DIR = TestUtilities.get_test_dir(__file__)

    config_file = TestUtilities.load_and_get_config_file_as_module(TEST_DIR)
    RunnerConfig: OriginalRunnerConfig = config_file.RunnerConfig

    with open(RunnerConfig.results_output_path / RunnerConfig.name / 'run_table.old.csv') as f:
        old = f.read() # this is before the crash.
    with open(RunnerConfig.results_output_path / RunnerConfig.name / 'run_table.csv') as f:
        new = f.read()
    assert(old == new)

    csv_data_manager = CSVOutputManager(RunnerConfig.results_output_path / RunnerConfig.name)
    run_table = csv_data_manager.read_run_table()
    for row in run_table:
        assert(row['__done']) == RunProgress.DONE.name
        assert(int(row['avg_cpu'])) == 13
