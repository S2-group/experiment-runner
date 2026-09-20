import unittest
import tempfile
from pathlib import Path
import pandas as pd
import sys

sys.path.append("experiment-runner")

from ProgressManager.Validation.AnomaliesChecker import ResultsValidator, AnomalyReport

class TestAnomaliesChecker(unittest.TestCase):
    def create_run_folder(self, df):
        tmpdir = tempfile.TemporaryDirectory()
        run_dir = Path(tmpdir.name)
        csv_file = run_dir / "energibridge.csv"
        df.to_csv(csv_file, index=False)
        return tmpdir, run_dir

    def test_positive_values(self):
        df = pd.DataFrame({
            "CPU_ENERGY (J)": [10, 12, 15],
            "CORE0_ENERGY (J)": [1.5, 1.7, 2.0]
        })
        tmpdir, run_dir = self.create_run_folder(df)
        report = ResultsValidator.validate_output_log(
            run_dir,
            "run_1",
            {"workload": "light"}
        )
        self.assertFalse(report.has_anomalies())
        tmpdir.cleanup()

    def test_zero_value(self):
        df = pd.DataFrame({
            "CPU_ENERGY (J)": [10, 0, 15]
        })
        tmpdir, run_dir = self.create_run_folder(df)
        report = ResultsValidator.validate_output_log(
            run_dir,
            "run_1",
            {"workload": "light"}
        )
        self.assertTrue(report.has_anomalies())
        self.assertEqual(report.anomalies[0]["anomaly_type"], "zero")
        tmpdir.cleanup()

    def test_negative_value(self):
        df = pd.DataFrame({
            "CPU_ENERGY (J)": [10, -5, 15]
        })
        tmpdir, run_dir = self.create_run_folder(df)
        report = ResultsValidator.validate_output_log(
            run_dir,
            "run_1",
            {"workload": "medium"}
        )
        self.assertTrue(report.has_anomalies())
        self.assertEqual(report.anomalies[0]["anomaly_type"], "negative")
        tmpdir.cleanup()

    def test_nan_value(self):
        df = pd.DataFrame({
            "CPU_ENERGY (J)": [10, None, 15]
        })
        tmpdir, run_dir = self.create_run_folder(df)
        report = ResultsValidator.validate_output_log(
            run_dir,
            "run_1",
            {"workload": "heavy"}
        )
        self.assertTrue(report.has_anomalies())
        self.assertEqual(report.anomalies[0]["anomaly_type"], "NaN")

        tmpdir.cleanup()

    def test_missing_file(self):
        tmpdir = tempfile.TemporaryDirectory()
        run_dir = Path(tmpdir.name)
        report = ResultsValidator.validate_output_log(
            run_dir,
            "run_1",
            {"workload": "light"}
        )
        self.assertTrue(report.has_anomalies())
        self.assertEqual(report.anomalies[0]["anomaly_type"], "missing_file")
        tmpdir.cleanup()

    def test_generate_report(self):
        tmpdir = tempfile.TemporaryDirectory()
        experiment_path = Path(tmpdir.name)

        run0 = experiment_path / "run_0"
        run0.mkdir()

        pd.DataFrame({
            "CPU_ENERGY (J)": [10, 0, 15]
        }).to_csv(run0 / "energibridge.csv", index=False)

        run1 = experiment_path / "run_1"
        run1.mkdir()

        pd.DataFrame({
            "CPU_ENERGY (J)": [10, -5, 15]
        }).to_csv(run1 / "energibridge.csv", index=False)

        run_table = [
            {"__run_id": "run_0", "workload": "light", "brightness": "low"},
            {"__run_id": "run_1", "workload": "heavy", "brightness": "high"}
        ]
        final_report = AnomalyReport()

        for run in run_table:
            run_id = run["__run_id"]
            treatment_levels = {
                k: v for k, v in run.items()
                if not k.startswith("__")
            }
            run_dir = experiment_path / run_id
            run_report = ResultsValidator.validate_output_log(
                run_dir,
                run_id,
                treatment_levels
            )
            final_report.anomalies.extend(run_report.anomalies)

        self.assertTrue(final_report.has_anomalies())
        log_file = experiment_path / "energibridge.log"
        ResultsValidator.save_report_to_file(
            final_report,
            log_file
        )
        self.assertTrue(log_file.exists())
        print(log_file.read_text())
        tmpdir.cleanup()


if __name__ == "__main__":
    unittest.main()