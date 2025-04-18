import sys
import csv
import os
import datetime

# Ensure our modules are accessable
sys.path.append("experiment-runner")
sys.path.append("test-standalone")

import TestUtilities
from ConfigValidator.Config.RunnerConfig import RunnerConfig as OriginalRunnerConfig
from Plugins.Profilers.PicoCM3 import PicoCM3

def is_valid_date(date_str):
    try:
        datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except:
        return False

    return True

if __name__ == '__main__':
    TEST_DIR = TestUtilities.get_test_dir(__file__)

    config_file = TestUtilities.load_and_get_config_file_as_module(TEST_DIR)
    RunnerConfig: OriginalRunnerConfig = config_file.RunnerConfig
    
    # Validate the PicoCM3 log
    for entry in os.scandir(RunnerConfig.results_output_path / RunnerConfig.name):
        if entry.is_dir():
            log_data = PicoCM3.parse_log(os.path.join(entry.path, "picocm3.log"))
            
            for t in log_data["timestamp"]:
                assert(is_valid_date(t))

            for v in log_data['channel_1']:
                assert(float(v) > 0)

            for v in log_data['channel_2']:
                assert(float(v) == 0)

            for v in log_data["channel_3"]:
                assert(float(v) == 0)

    # Validate RunTable 
    with open(RunnerConfig.results_output_path / RunnerConfig.name / 'run_table.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            times = row["timestamp"].split(" - ")

            start_time = datetime.datetime.strptime(times[0], "%Y-%m-%d %H:%M:%S")
            end_time = datetime.datetime.strptime(times[1], "%Y-%m-%d %H:%M:%S")
            
            assert(end_time > start_time)
            assert(float(row["channel_1(avg)"]) > 0)
            assert(float(row["channel_2(off)"]) == 0)
            assert(float(row["channel_3(off)"]) == 0)
