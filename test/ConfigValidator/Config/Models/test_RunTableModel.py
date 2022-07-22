import unittest
import itertools

from ConfigValidator.Config.Models.FactorModel import FactorModel
from ConfigValidator.Config.Models.RunTableModel import RunTableModel
from ConfigValidator.CustomErrors.BaseError import BaseError
from ProgressManager.RunTable.Models.RunProgress import RunProgress


class TestRunTableModelDuplicateNames(unittest.TestCase):

    def test_duplicate_factor_names(self):
        try:
            RunTableModel(
                factors=[
                    FactorModel("example_factor1", ['example_treatment1', 'example_treatment2', 'example_treatment3']),
                    FactorModel("example_factor1", [True, False]),
                ]
            )
            self.assert_(False)
        except BaseError:
            pass

    def test_duplicate_data_columns(self):
        try:
            RunTableModel(
                factors=[
                    FactorModel("example_factor1", ['example_treatment1', 'example_treatment2', 'example_treatment3']),
                    FactorModel("example_factor2", [True, False]),
                ],
                data_columns=['data_col1', 'data_col2', 'data_col1']
            )
            self.assert_(False)
        except BaseError:
            pass


class TestRunTableModelSimple(unittest.TestCase):
    def setUp(self):
        self.runTableModel = RunTableModel(
            factors=[
                FactorModel("example_factor1", ['example_treatment1', 'example_treatment2', 'example_treatment3']),
                FactorModel("example_factor2", [True, False]),
            ],
            data_columns=['avg_cpu', 'avg_mem'],
            shuffle=True
        )

    def test_generate_experiment_run_table(self):
        table = self.runTableModel.generate_experiment_run_table()
        for run in table:
            self.assertIn('__run_id', run)
            self.assertIn('__done', run)
            self.assertEquals(run['__done'], RunProgress.TODO)
            for factor in self.runTableModel.get_factors():
                self.assertIn(factor.factor_name, run)
                treatment_level = run[factor.factor_name]
                self.assertIn(treatment_level, factor.treatments)
            for data_col in self.runTableModel.get_data_columns():
                self.assertIn(data_col, run)


class TestRunTableModelExclusions(unittest.TestCase):
    def setUp(self):
        factor1 = FactorModel("example_factor1", [i for i in range(6)])
        factor2 = FactorModel("example_factor2", [i for i in range(6)])
        self.factor1 = factor1
        self.factor2 = factor2

        self.runTableModel = RunTableModel(
            factors=[factor1, factor2],
            exclude_variations=[
                {factor1: [0, 1, 2]},  # Exclude any experiments that have levels 0,1,2 for factor1.
                {factor1: [3], factor2: [4]},  # Exclude pair (3,4) (but NOT (4,3))
                {factor1: [3, 4], factor2: [5]},  # Excludes (3,5) and (4,5)
            ],
        )

    def test_generate_experiment_run_table(self):
        table = self.runTableModel.generate_experiment_run_table()
        full_table = itertools.product(self.factor1.treatments, self.factor2.treatments)
        for run in table:
            pair = (run['example_factor1'], run['example_factor2'])
            self.assertIn(pair, full_table)
            self.assertNotIn(run['example_factor1'], [0, 1, 2])
            self.assertNotIn(pair, [
                (3, 4), (3, 5), (4, 5)
            ])


if __name__ == '__main__':
    unittest.main()
