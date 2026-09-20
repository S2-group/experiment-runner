"""
EXAMPLE: Basic System Tests

This file demonstrates how to write system-level tests using the new framework.

KEY CONCEPTS:
1. Tests inherit from SystemExperimentTest (base class with helper methods)
2. Tests use fixtures from conftest.py (temp_dir, env_vars_clean)
3. Tests run REAL experiments, not mocked versions
4. Each test is independent (isolated temp directories)

RUN THESE TESTS:
    pytest test/system/test_basic_run.py              # Run all tests in this file
    pytest test/system/test_basic_run.py::TestBasicRuns::test_hello_world
    pytest test/system/test_basic_run.py -v           # Verbose output
    pytest test/system/test_basic_run.py -s           # Show print statements
"""

import pytest
from pathlib import Path
from test.system.base_system_test import SystemExperimentTest


class TestBasicRuns(SystemExperimentTest):
    """
    Test suite: Basic experiment execution
    
    Each method is a test. Pytest runs them and reports:
    - PASSED: test completed successfully
    - FAILED: assertion failed
    - ERROR: exception raised
    """
    
    @pytest.mark.system
    def test_hello_world_experiment_runs(self, temp_dir):
        """
        TEST 1: Can we run the hello-world example?
        
        SETUP:
        - temp_dir: pytest fixture (see conftest.py) provides fresh directory
        
        WHAT IT DOES:
        1. Run the hello-world experiment
        2. Check that it completes successfully
        3. Verify output directory exists
        
        HOW PYTEST WORKS:
        - Calls fixture: temp_dir is created
        - Runs test function
        - If any 'assert' fails, test FAILS
        - Cleanup: temp_dir is deleted
        
        EXAMPLE OUTPUT:
            PASSED test_hello_world_experiment_runs
            
        If it fails:
            FAILED test_hello_world_experiment_runs
            AssertionError: assert False == True
            ...stderr output...
        """
        # Step 1: Run the actual experiment
        result = self.run_experiment(
            config_path="examples/hello-world",
            results_dir=temp_dir
        )
        
        # Step 2: Assert it was successful
        # If this fails, test fails with clear error
        assert result.success, f"Experiment failed!\nStderr: {result.stderr}"
        
        # Step 3: Verify no errors in output
        self.validate_no_errors_in_output(result)
        
        # Step 4: Verify results directory exists
        assert (temp_dir / "experiments").exists(), \
            "Results directory was not created"
    
    
    @pytest.mark.system
    def test_hello_world_output_structure(self, temp_dir):
        """
        TEST 2: Does hello-world create the expected output structure?
        
        WHAT IT CHECKS:
        - run_table.csv exists and has content
        - Directory structure is correct
        - All required files are present
        """
        # Run experiment
        result = self.run_experiment(
            config_path="examples/hello-world",
            results_dir=temp_dir
        )
        
        # Get the experiment directory
        # (assumes experiment is named "new_runner_experiment" by default)
        exp_dir = temp_dir / "experiments" / "new_runner_experiment"
        
        # Validate structure
        self.validate_experiment_structure(exp_dir)
        self.validate_csv_output(exp_dir)
    
    
    @pytest.mark.system
    def test_fibonacci_experiment_runs(self, temp_dir):
        """
        TEST 3: Test a different example (fibonacci)
        
        WHY: Tests should be specific, not generic
             Each example might have different requirements
        """
        result = self.run_experiment(
            config_path="examples/hello-world-fibonacci",
            results_dir=temp_dir
        )
        
        assert result.success, f"Fibonacci experiment failed:\n{result.stderr}"
        self.validate_no_errors_in_output(result)
    
    
    @pytest.mark.system
    @pytest.mark.slow
    def test_multiple_sequential_runs(self, temp_dir):
        """
        TEST 4: Can we run multiple experiments in sequence?
        
        @pytest.mark.slow decorator means:
        - pytest -m slow      (run ONLY slow tests)
        - pytest --skip-slow  (skip slow tests)
        
        WHY: Some tests are slow. During development, you might skip them.
             Use for comprehensive testing before submitting.
        """
        # Run first experiment
        result1 = self.run_experiment(
            config_path="examples/hello-world",
            results_dir=temp_dir
        )
        assert result1.success, f"First run failed: {result1.stderr}"
        
        # Run second experiment (different name to avoid conflicts)
        # This tests that framework can handle multiple experiments
        result2 = self.run_experiment(
            config_path="examples/hello-world-fibonacci",
            results_dir=temp_dir
        )
        assert result2.success, f"Second run failed: {result2.stderr}"


class TestRestartRecovery(SystemExperimentTest):
    """
    Test suite: Experiment restart/recovery on crash
    
    These tests verify that if an experiment crashes mid-way,
    we can resume it and it completes correctly.
    """
    
    @pytest.mark.system
    @pytest.mark.slow
    def test_restart_after_simulated_crash(self, temp_dir):
        """
        TEST 5: Can framework recover from a crash?
        
        SCENARIO:
        1. Run experiment partially
        2. Simulate a crash (mark a run as incomplete)
        3. Re-run and verify it continues from where it left off
        
        WHY: Real-world experiments can crash. Framework should handle this gracefully.
        """
        # Step 1: Run initial experiment
        result1 = self.run_experiment(
            config_path="test-standalone/core/shuffling",
            results_dir=temp_dir
        )
        assert result1.success, f"Initial run failed: {result1.stderr}"
        
        # Step 2: Simulate crash by marking run 1 as incomplete
        exp_dir = temp_dir / "experiments" / "new_runner_experiment"
        self.simulate_run_crash(exp_dir, run_id=1)
        
        # Verify the crash was simulated
        csv_rows = self.read_csv_as_dicts(exp_dir / "run_table.csv")
        assert csv_rows[1]['__done'] == 'TODO', \
            "Crash simulation didn't mark run as incomplete"
        
        # Step 3: Re-run experiment (should continue from run 1)
        result2 = self.run_experiment(
            config_path="test-standalone/core/shuffling",
            results_dir=temp_dir
        )
        assert result2.success, f"Recovery run failed: {result2.stderr}"
        
        # Step 4: Verify all runs are now complete
        csv_rows = self.read_csv_as_dicts(exp_dir / "run_table.csv")
        for row in csv_rows:
            assert row['__done'] == 'DONE', \
                f"Run not completed: {row}"


# ============================================================================
# DEMONSTRATION: How fixtures work
# ============================================================================

class TestFixtureDemonstration:
    """
    This class shows HOW FIXTURES WORK in pytest
    
    Fixtures are like setUp() but more powerful.
    They can:
    - Provide test data
    - Create temporary resources
    - Handle cleanup automatically
    """
    
    def test_temp_dir_fixture(self, temp_dir):
        """
        This test receives 'temp_dir' fixture automatically.
        
        Pytest:
        1. Creates temp directory
        2. Passes it to this function as 'temp_dir' parameter
        3. Runs this test
        4. Cleans up temp directory
        5. Test done!
        """
        # temp_dir is a Path object pointing to fresh directory
        assert temp_dir.is_dir()
        assert len(list(temp_dir.iterdir())) == 0  # Empty
        
        # Create a file
        test_file = temp_dir / "test.txt"
        test_file.write_text("Hello!")
        
        # Verify it exists
        assert test_file.exists()
        
        # After this test ends, temp_dir is automatically deleted
    
    
    def test_experiment_output_dir_fixture(self, experiment_output_dir):
        """
        This test receives 'experiment_output_dir' fixture.
        
        This fixture creates the directory structure that
        Experiment Runner expects:
            experiments/
            └── my_experiment/
        """
        # The fixture creates experiments/ directory
        assert experiment_output_dir.exists()
        assert experiment_output_dir.parent.name == "experiments"


# ============================================================================
# ADVANCED: Parameterized tests
# ============================================================================

class TestParameterized(SystemExperimentTest):
    """
    Parameterized tests run the same test with different inputs.
    
    WHY: Avoid writing the same test multiple times with different configs.
         One test function runs multiple times with different parameters.
    """
    
    @pytest.mark.parametrize("example_name", [
        "hello-world",
        "hello-world-fibonacci",
    ])
    @pytest.mark.system
    def test_all_examples_run(self, example_name, temp_dir):
        """
        This test runs TWICE:
        - Once with example_name="hello-world"
        - Once with example_name="hello-world-fibonacci"
        
        PYTEST PARAMETRIZE SYNTAX:
        @pytest.mark.parametrize("param_name", [list of values])
        def test_something(param_name, other_fixtures):
            ...
        
        BENEFIT:
        - DRY (Don't Repeat Yourself)
        - Easier to add new test cases
        - Clear pass/fail for each variant
        """
        result = self.run_experiment(
            config_path=f"examples/{example_name}",
            results_dir=temp_dir
        )
        assert result.success, f"{example_name} failed: {result.stderr}"
