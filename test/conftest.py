"""
Global pytest configuration and shared fixtures for ALL tests

This file is automatically discovered by pytest and runs before any tests.
It contains:
1. Pytest plugins and configuration
2. Shared fixtures (reusable setup/teardown)
3. Hooks for test execution

WHY THIS MATTERS:
- Fixtures replace traditional setUp()/tearDown() methods
- Fixtures are more flexible: can be scoped (function, class, module, session)
- Shared fixtures prevent code duplication across test files
- conftest.py is the standard pytest way to organize test utilities
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add experiment-runner to Python path so tests can import it
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "experiment-runner"))


# ============================================================================
# FIXTURES - Reusable setup/teardown for tests
# ============================================================================
# A fixture is like a setUp() method that runs before each test
# Think of it as: "Here's the environment my test needs"

@pytest.fixture
def temp_dir():
    """
    Fixture: Create a temporary directory for test files
    
    SCOPE: "function" means a new temp directory for EACH test function
    
    WHY: Tests need isolated environments so they don't interfere with each other
         One test shouldn't modify another test's files
    
    USAGE in tests:
        def test_something(temp_dir):
            # temp_dir is a Path object pointing to a fresh temporary directory
            config_file = temp_dir / "RunnerConfig.py"
            config_file.write_text("...")
    
    CLEANUP: Automatically deleted after test completes (yield statement does this)
    """
    tmpdir = Path(tempfile.mkdtemp())
    yield tmpdir  # "yield" = pause here, run test, resume after
    # After test completes, cleanup happens below
    if tmpdir.exists():
        shutil.rmtree(tmpdir)


@pytest.fixture
def experiment_output_dir(temp_dir):
    """
    Fixture: Create directory structure expected by Experiment Runner
    
    This prepares a directory that Experiment Runner can write results to.
    
    STRUCTURE:
        temp_dir/
        └── experiments/          <- Where results go
            └── my_experiment/    <- One folder per experiment
                ├── run_table.csv
                ├── metadata.json
                └── run_0_repetition_0/
    """
    results_dir = temp_dir / "experiments"
    results_dir.mkdir(parents=True, exist_ok=True)
    return results_dir


@pytest.fixture
def env_vars_clean():
    """
    Fixture: Clean environment variables before/after test
    
    WHY: Some tests rely on environment variables (like EXPERIMENT_RUNNER_OUTPUT_PATH)
         We want a clean state so tests don't affect each other
    
    This saves original values, provides clean environment, then restores
    """
    # Save original environment
    original_env = os.environ.copy()
    
    yield  # Run test with clean environment
    
    # Restore original environment after test
    os.environ.clear()
    os.environ.update(original_env)


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """
    Hook: Runs once when pytest starts
    
    We use this to register custom markers (test categories)
    """
    config.addinivalue_line(
        "markers", 
        "system: System-level tests (real experiment execution)"
    )
    config.addinivalue_line(
        "markers",
        "integration: Integration tests (multiple components)"
    )
    config.addinivalue_line(
        "markers",
        "unit: Unit tests (single component with mocks)"
    )
    config.addinivalue_line(
        "markers",
        "slow: Tests that take a while to run"
    )


def pytest_collection_modifyitems(config, items):
    """
    Hook: Runs after tests are discovered, before they run
    
    This automatically assigns markers based on test location
    """
    for item in items:
        # If test is in system/, mark it as @pytest.mark.system
        if "system" in str(item.fspath):
            item.add_marker(pytest.mark.system)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)


# ============================================================================
# PYTEST COMMAND LINE OPTIONS
# ============================================================================
# These let users run specific test types:
# pytest -m system    (only system tests)
# pytest -m unit      (only unit tests)
# pytest -k shuffling (only tests with "shuffling" in name)

def pytest_addoption(parser):
    """
    Hook: Allows passing custom command line options to pytest
    """
    parser.addoption(
        "--real-profilers",
        action="store_true",
        default=False,
        help="Run tests that require real profiler installations"
    )
    parser.addoption(
        "--skip-slow",
        action="store_true",
        default=False,
        help="Skip slow system tests"
    )
