import unittest

import shutil
import tempfile
import re
from pathlib import Path
from typing import AnyStr

from ConfigValidator.Config.Models.RunnerContext import RunnerContext
from ConfigValidator.Config.RunnerConfig import RunnerConfig
from ProgressManager.Output.OutputProcedure import OutputProcedure as output

from Plugins.Profilers import CodecarbonWrapper
from Plugins.Profilers.CodecarbonWrapper import DataColumns as CCDataCols


class TestEmissionTrackerIndividual(unittest.TestCase):

    class EmissionTrackerConfig(RunnerConfig):
        # setUpClass and tearDownClass appear broken *sigh*. Use this wrapper instead. We have a singleton anyway.
        tmpdir: AnyStr = tempfile.mkdtemp()
        def clear(self):
            print(f'Clearing tmpdir {self.__class__.tmpdir}')
            shutil.rmtree(self.__class__.tmpdir)

        @CodecarbonWrapper.add_data_columns([CCDataCols.EMISSIONS, CCDataCols.ENERGY_CONSUMED])
        def create_run_table_model(self):
            return super().create_run_table_model()

        @CodecarbonWrapper.start_emission_tracker(
            country_iso_code="NLD",
            output_dir=tmpdir
        )
        def start_measurement(self, context: RunnerContext):
            super().start_measurement(context)

        def interact(self, context: RunnerContext):
            output.console_log("Config.interact() called!")
            re.search(r'^(a|a?)+b$', "a" * 20)  # ReDoS to consume some cpu

        @CodecarbonWrapper.stop_emission_tracker
        def stop_measurement(self, context: RunnerContext):
            super().stop_measurement(context)

        @CodecarbonWrapper.populate_data_columns
        def populate_run_data(self, context: RunnerContext):
            output.console_log("Config.populate_run_data() called!")
            return {
                'avg_cpu': 52.3,
                'avg_mem': 18.1
            }

    def setUp(self) -> None:
        self.runner_config = self.__class__.EmissionTrackerConfig()
        self.run_table = self.runner_config.create_run_table_model().generate_experiment_run_table()

    def tearDown(self) -> None:
        self.runner_config.clear()

    def test_config(self):
        self.runner_config.start_measurement(None)
        self.runner_config.interact(None)
        self.runner_config.stop_measurement(None)
        run_data = self.runner_config.populate_run_data(None)
        self.assertTrue(run_data[CCDataCols.EMISSIONS.name] > 0)
        self.assertTrue(run_data[CCDataCols.ENERGY_CONSUMED.name] > 0)
        self.assertTrue(run_data['avg_cpu'] == 52.3)
        self.assertTrue(run_data['avg_mem'] == 18.1)
        self.assertTrue( (Path(self.runner_config.tmpdir) / 'emissions.csv').is_file() )
        print(run_data)


class TestEmissionTrackerCombined(unittest.TestCase):
    # setUpClass and tearDownClass appear broken *sigh*. Use this wrapper instead. We have a singleton anyway.
    tmpdir: AnyStr = tempfile.mkdtemp()

    @CodecarbonWrapper.emission_tracker(
        data_columns=[CCDataCols.EMISSIONS, CCDataCols.ENERGY_CONSUMED],
        country_iso_code="NLD",
        output_dir=tmpdir
    )
    class EmissionTrackerConfig(RunnerConfig):
        def clear(self):
            print(f'Clearing tmpdir {TestEmissionTrackerCombined.tmpdir}')
            shutil.rmtree(TestEmissionTrackerCombined.tmpdir)

        def interact(self, context: RunnerContext):
            output.console_log("Config.interact() called!")
            re.search(r'^(a|a?)+b$', "a" * 20)  # ReDoS to consume some cpu

        def populate_run_data(self, context: RunnerContext):
            output.console_log("Config.populate_run_data() called!")
            return {
                'avg_cpu': 52.3,
                'avg_mem': 18.1
            }

    def setUp(self) -> None:
        self.runner_config = self.__class__.EmissionTrackerConfig()
        self.run_table = self.runner_config.create_run_table_model().generate_experiment_run_table()

    def tearDown(self) -> None:
        self.runner_config.clear()

    def test_config(self):
        self.runner_config.start_measurement(None)
        self.runner_config.interact(None)
        self.runner_config.stop_measurement(None)
        run_data = self.runner_config.populate_run_data(None)
        self.assertTrue(run_data[CCDataCols.EMISSIONS.name] > 0)
        self.assertTrue(run_data[CCDataCols.ENERGY_CONSUMED.name] > 0)
        self.assertTrue(run_data['avg_cpu'] == 52.3)
        self.assertTrue(run_data['avg_mem'] == 18.1)
        self.assertTrue( (Path(TestEmissionTrackerCombined.tmpdir) / 'emissions.csv').is_file() )
        print(run_data)


if __name__ == '__main__':
    unittest.main()
