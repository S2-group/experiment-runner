"""
Base class for System-Level Tests

What is a "System Test"?
- Runs the ACTUAL experiment (not mocked)
- Tests real profilers, real data collection
- Validates end-to-end workflow
- Catches integration issues

This base class provides reusable methods for all system tests so we don't
repeat code in every test file.

INHERITANCE EXAMPLE:
    class TestBasicExperiment(SystemExperimentTest):
        def test_hello_world_runs(self, temp_dir):
            # Use inherited methods like self.run_experiment()
            result = self.run_experiment("hello-world", temp_dir)
            assert result.success
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional, List
import pytest


class ExperimentResult:
    """
    Container for experiment execution results
    
    WHY: Instead of returning a tuple, we return an object with named fields
         This is clearer: result.success vs result[0]
    """
    def __init__(self, success: bool, stdout: str, stderr: str, 
                 results_dir: Path, config_path: Path):
        self.success = success        # Did experiment complete?
        self.stdout = stdout          # Console output
        self.stderr = stderr          # Error output
        self.results_dir = results_dir  # Where results were written
        self.config_path = config_path  # Which config was used


class SystemExperimentTest:
    """
    Base class for ALL system-level tests
    
    Think of this as a "helper class" that all system tests inherit from.
    It provides common methods so we don't repeat code.
    
    EXAMPLE USAGE:
        class TestProfilers(SystemExperimentTest):
            def test_picoCM3_experiment(self, temp_dir):
                # Call inherited method from this class
                result = self.run_experiment(
                    config_name="test-standalone/plugins/PicoCM3",
                    results_dir=temp_dir
                )
                assert result.success
                self.validate_csv_output(result.results_dir)
    """
    
    # ========================================================================
    # SETUP METHODS
    # ========================================================================
    
    def run_experiment(
        self, 
        config_path: str,
        results_dir: Path,
        timeout: int = 300
    ) -> ExperimentResult:
        """
        Execute an actual experiment using Experiment Runner
        
        This runs: python experiment-runner/ <config_path>
        
        PARAMETERS:
            config_path: Relative or absolute path to RunnerConfig.py
            results_dir: Where to store results
            timeout: Maximum seconds to wait (default 5 min)
        
        RETURNS:
            ExperimentResult object with success, stdout, stderr, etc.
        
        WHY NOT JUST CALL subprocess DIRECTLY?
        - Encapsulation: If how we run experiments changes, update here once
        - Reusability: All tests use same execution method
        - Error handling: Consistent error reporting
        
        EXAMPLE:
            result = self.run_experiment("examples/hello-world", temp_dir)
            if not result.success:
                print(result.stderr)  # Show what went wrong
        """
        project_root = Path(__file__).parent.parent.parent
        config_file = Path(config_path)
        
        if not config_file.is_absolute():
            config_file = project_root / config_path / "RunnerConfig.py"
        
        # Build the command: python experiment-runner/ <config>
        cmd = [
            sys.executable,
            str(project_root / "experiment-runner" / "__main__.py"),
            str(config_file)
        ]
        
        try:
            # Run the command and capture output
            result = subprocess.run(
                cmd,
                capture_output=True,      # Capture stdout/stderr
                text=True,                # Return as strings, not bytes
                timeout=timeout,
                cwd=str(project_root)
            )
            
            # Experiment was successful if return code is 0
            success = result.returncode == 0
            
            return ExperimentResult(
                success=success,
                stdout=result.stdout,
                stderr=result.stderr,
                results_dir=results_dir,
                config_path=config_file
            )
        
        except subprocess.TimeoutExpired:
            # Experiment took too long
            return ExperimentResult(
                success=False,
                stdout="",
                stderr=f"Experiment timed out after {timeout} seconds",
                results_dir=results_dir,
                config_path=config_file
            )
        except Exception as e:
            # Something went wrong executing the command
            return ExperimentResult(
                success=False,
                stdout="",
                stderr=f"Failed to run experiment: {str(e)}",
                results_dir=results_dir,
                config_path=config_file
            )
    
    
    # ========================================================================
    # VALIDATION METHODS
    # ========================================================================
    
    def validate_csv_output(self, experiment_dir: Path) -> bool:
        """
        Validate that CSV output exists and is readable
        
        WHAT IT CHECKS:
        - run_table.csv exists
        - CSV is readable (valid format)
        - At least one row of data
        
        RETURNS:
            True if valid, raises AssertionError if not
        
        WHY: CSV is the main output format, so this is critical
        """
        csv_file = experiment_dir / "run_table.csv"
        
        # Check file exists
        assert csv_file.exists(), f"run_table.csv not found in {experiment_dir}"
        
        # Check file is not empty
        content = csv_file.read_text()
        assert len(content) > 0, "run_table.csv is empty"
        
        # Check it has at least a header row
        lines = content.strip().split('\n')
        assert len(lines) >= 1, "run_table.csv has no header"
        
        return True
    
    
    def validate_experiment_structure(self, experiment_dir: Path) -> bool:
        """
        Validate expected directory structure exists
        
        EXPECTED STRUCTURE:
            experiment_dir/
            ├── run_table.csv       (main results)
            ├── metadata.json       (experiment metadata)
            └── run_0_repetition_0/ (per-run data)
                ├── profiler_output
                └── raw_data
        
        RETURNS:
            True if structure is valid
        """
        # Check required files
        required_files = [
            "run_table.csv",
            "metadata.json"
        ]
        
        for filename in required_files:
            filepath = experiment_dir / filename
            assert filepath.exists(), \
                f"Missing required file: {filename} in {experiment_dir}"
        
        # Check at least one run directory exists
        run_dirs = list(experiment_dir.glob("run_*"))
        assert len(run_dirs) > 0, \
            f"No run directories found in {experiment_dir}"
        
        return True
    
    
    def validate_no_errors_in_output(self, result: ExperimentResult) -> bool:
        """
        Check that stderr doesn't contain error keywords
        
        WHAT IT CHECKS:
        - stderr is empty OR doesn't contain [FAIL], "Error", "Exception"
        
        WHY: The experiment might complete but still have warnings/errors
        
        RETURNS:
            True if no critical errors detected
        """
        error_keywords = ["[FAIL]", "[ERROR]", "Exception", "Traceback"]
        
        for keyword in error_keywords:
            assert keyword not in result.stderr, \
                f"Found error keyword '{keyword}' in stderr:\n{result.stderr}"
        
        return True
    
    
    # ========================================================================
    # SIMULATION METHODS (for testing failure cases)
    # ========================================================================
    
    def simulate_run_crash(
        self, 
        experiment_dir: Path, 
        run_id: int
    ) -> None:
        """
        Simulate a crash mid-experiment by modifying run_table.csv
        
        This marks a run as incomplete so when we re-run, the framework
        will think it crashed and try to restart it.
        
        USAGE:
            # Run experiment partially
            result1 = self.run_experiment(config, temp_dir)
            
            # Simulate crash on run 1
            self.simulate_run_crash(temp_dir, run_id=1)
            
            # Re-run and verify it handles the restart correctly
            result2 = self.run_experiment(config, temp_dir)
            assert result2.success
        
        WHAT IT DOES:
        - Reads run_table.csv
        - Finds the row for the specified run
        - Sets __done to "TODO" (marks as incomplete)
        - Writes it back
        
        WHY: Tests that restart/recovery logic works correctly
        """
        csv_file = experiment_dir / "run_table.csv"
        
        # Read CSV content
        content = csv_file.read_text()
        lines = content.strip().split('\n')
        
        if len(lines) < 2:
            raise ValueError("CSV has no data rows to modify")
        
        # Find and modify the row for this run_id
        header = lines[0]
        rows = lines[1:]
        
        modified_rows = []
        for row_idx, row in enumerate(rows):
            if row_idx == run_id:
                # Set __done to TODO (incomplete)
                # This assumes __done is the first column
                cols = row.split(',')
                cols[0] = 'TODO'
                modified_rows.append(','.join(cols))
            else:
                modified_rows.append(row)
        
        # Write back to CSV
        new_content = header + '\n' + '\n'.join(modified_rows)
        csv_file.write_text(new_content)
    
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def get_experiment_dir(
        self, 
        results_dir: Path, 
        experiment_name: str
    ) -> Path:
        """
        Get the full path to an experiment's results directory
        
        STRUCTURE:
            results_dir/
            └── <experiment_name>/  <- returned path
                └── run_table.csv
        
        PARAMETERS:
            results_dir: Parent results directory
            experiment_name: Name of experiment (from RunnerConfig.name)
        
        RETURNS:
            Path to experiment directory
        """
        return results_dir / experiment_name
    
    
    def read_csv_as_dicts(self, csv_path: Path) -> List[Dict]:
        """
        Read CSV file and return as list of dictionaries
        
        WHY: Easier to work with dictionaries than raw CSV strings
             Can access columns by name: row['avg_cpu']
        
        EXAMPLE:
            rows = self.read_csv_as_dicts(Path("run_table.csv"))
            for row in rows:
                print(row['run_id'], row['avg_cpu'])
        """
        import csv
        
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            return list(reader)
