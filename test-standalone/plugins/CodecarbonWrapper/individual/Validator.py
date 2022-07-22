
import csv

from ConfigValidator.Config.RunnerConfig import RunnerConfig as OriginalRunnerConfig
from Plugins import CodecarbonWrapper
from Plugins.CodecarbonWrapper import DataColumns as CCDataCols

import TestUtilities

if __name__ == 'main':
    TEST_DIR = TestUtilities.get_test_dir(__file__)

    config_file = TestUtilities.load_and_get_config_file_as_module(TEST_DIR)
    RunnerConfig: OriginalRunnerConfig = config_file.RunnerConfig

    with open(RunnerConfig.results_output_path / RunnerConfig.name / 'run_table.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            assert (float(row[CCDataCols.EMISSIONS]) > 0)
            assert (float(row[CCDataCols.ENERGY_CONSUMED]) > 0)
