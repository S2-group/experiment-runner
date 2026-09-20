import sys
import ast
import os
import shutil
import importlib
import importlib.util
from pathlib import Path
from typing import List, Dict, Tuple, Optional,Set
from ConfigValidator.CustomErrors.BaseError import BaseError
from ProgressManager.Output.OutputProcedure import OutputProcedure as output

class RequirementCheckResult:    
    def __init__(self, name: str, requirement_type: str):
        self.name = name
        self.requirement_type = requirement_type
        self.installed = False
        self.error_message = ""
        self.version = None
    
    def mark_failure(self, error: str):
        self.installed = False
        self.error_message = error

###     =========================================================
###     |                                                       |
###     |                  RequirementsValidator:               |
###     |                                                       |
###     |       - Checks the following requirements:            |
###     |           - Framework requirements (python versions   |
###     |               and packages from requirements.txt)     |
###     |           - External tools availability in Path       |
###     |           - Experiment-specific requirements          |
###     |                                                       |
###     |        *Validates all requirements for an             |
###     |           experiment before execution.                |
###     |                                                       |
###     =========================================================
PROFILER_DEPS = {
    "AndroidDebugBridge":{
        "tools": ["adb"],
        "python_modules": [],
    },
    "JoularCore": {
        "tools": ["java"],
        "python_modules": ["jpype"],
    },
    "PowerJoular": {
        "tools": ["java"],
        "python_modules": [],
    },
    "EnergiBridge": {
        "tools": ["energibridge"],
        "python_modules": [],
    },
    "NvidiaML": {
        "tools": ["nvidia-smi"],
        "python_modules": ["pynvml"],
    },
    "PowerMetrics": {
        "tools": ["powermetrics"],
        "python_modules": [],
    },
    "PowerLetrics": {
        "tools": ["powermetrics"],
        "python_modules": [],
    },
    "Ps": {
        "tools": ["ps"],
        "python_modules": [],
    },
    "PicoCM3": {
        "tools": [],
        "python_modules": ["picosdk"],
    },
    "CodecarbonWrapper": {
        "tools": [],
        "python_modules": ["codecarbon"],
    },
    "WattsUpPro": {
        "tools": [],
        "python_modules": ["serial"],
    },
}

class RequirementsValidator:
    
    def __init__(self, config_file_path: Path):
        self.config_file_path = config_file_path
        self.config_dir = config_file_path.parent
        self.framework_root = self._find_framework_root()
        self.results: List[RequirementCheckResult] = []
        self.failed_checks: List[RequirementCheckResult] = []
    
    @staticmethod
    def _find_framework_root() -> Path:
        """Find the root of the experiment-runner framework"""
        cwd = Path.cwd()
        
        if (cwd / 'experiment-runner').exists():
            return cwd
        if (cwd / 'requirements.txt').exists():
            return cwd
        
        for parent in cwd.parents:
            if (parent / 'experiment-runner').exists():
                return parent
            if (parent / 'requirements.txt').exists():
                return parent
        
        return cwd
    
    def validate_all(self) -> bool:
        """
        Run all validation checks. Returns True if all pass, False otherwise.
        Raises BaseError with details if any critical checks fail.
        """
        try:
            # Check Python version
            self._validate_python_version()
            # Check requirements.txt
            self._validate_framework_requirements()
            # Check experiment-specific requirements
            self._validate_plugin_requirements_file()
            self._check_profiler_external_deps()
            # Check MSR module and permissions
            self._validate_msr_module()
            self._validate_msr_permissions()
            self._validate_perf_permissions()

            # Results
            return self._report_results()
        
        except BaseError:
            raise
        except Exception as e:
            raise BaseError(f"Validation error: {str(e)}")
    
    def _validate_perf_permissions(self):
        """Check if the user has permission to access performance counters"""
        
        result = RequirementCheckResult("perf_event_paranoid", "system")
        perf_file = Path("/proc/sys/kernel/perf_event_paranoid")
        
        if not perf_file.exists():
            return

        value = int(perf_file.read_text().strip())

        if value >= 2:
            result.mark_failure(
                "Check Troubleshooting.md: perf_event_paranoid is too restrictive.\n"
                f"perf_event_paranoid={value}\n"
                "Hardware performance counters are restricted.\n"
            )
            self.failed_checks.append(result)
        self.results.append(result)

    def _validate_msr_module(self):
        """Check if the MSR kernel module is loaded"""
        
        msr_path = Path("/dev/cpu/0/msr")
        result = RequirementCheckResult("MSR module", "system")
        if not msr_path.exists():
            result.mark_failure(
                "Check Troubleshooting.md: MSR kernel module not loaded.\n"
                "MSR kernel module not loaded.\n"
            )
            self.failed_checks.append(result)
        self.results.append(result)

    def _validate_msr_permissions(self):
        """Check if the user has permission to read MSR registers"""
        
        result = RequirementCheckResult("MSR permissions","system")
        msr_path = "/dev/cpu/0/msr"

        if not os.access(msr_path, os.R_OK):
            result.mark_failure(
                "Check Troubleshooting.md: No permission to read MSR registers.\n"
                "No permission to read MSR registers.\n"
            )
            self.failed_checks.append(result)
        self.results.append(result)
    
    def _validate_python_version(self):
        """Check Python version compatibility"""        
        
        python_version = sys.version_info
        result = RequirementCheckResult(f"Python {python_version.major}.{python_version.minor}", "system")
        
        # Framework requires Python 3.8+
        if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
            result.mark_failure(
                f"Python 3.8+ required. Current: {python_version.major}.{python_version.minor}"
            )
        self.results.append(result)
    
    def _validate_framework_requirements(self):
        """Check framework dependencies from requirements.txt"""        
        requirements_file = self.framework_root / "requirements.txt"
        result = RequirementCheckResult("Framework requirements", "python_module")
        
        if not requirements_file.exists():
            output.console_log_WARNING("  requirements.txt not found")
            return
        with open(requirements_file) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                # Parse requirement: package_name or package_name==version
                package_spec = line.split('==')[0].split('>=')[0].split('<=')[0].split('>')[0].split('<')[0]
                package_name = package_spec.strip()
                
                result = RequirementCheckResult(package_name, "python_module")
                try:
                    # Try to import the module
                    module = importlib.import_module(package_name)
                    version = getattr(module, '__version__', 'unknown')
                except ImportError as e:
                    result.mark_failure(f"Cannot import: {str(e)}")
                    self.failed_checks.append(result)                
                self.results.append(result)
    
    def _check_profiler_external_deps(self):
        """Check experiment-specific plugins required"""        
        used_profilers = self.extract_used_profilers(self.config_file_path)

        for profiler in used_profilers:
            if profiler not in PROFILER_DEPS:
                output.console_log_WARNING(f"Unknown profiler '{profiler}'")
                continue

            dependencies = PROFILER_DEPS[profiler]

            for tool in dependencies["tools"]:
                result = RequirementCheckResult(f"{profiler}:{tool}", "system_tool")

                if not shutil.which(tool):
                    result.mark_failure(f"Missing tool '{tool}'")
                    self.failed_checks.append(result)
                self.results.append(result)

            for module in dependencies["python_modules"]:
                result = RequirementCheckResult(f"{profiler}:{module}", "python_module")
                try:
                    importlib.import_module(module)
                except ImportError:
                    result.mark_failure(f"Missing Python module '{module}'")
                    self.failed_checks.append(result)
                self.results.append(result)

    @staticmethod
    def extract_used_profilers(config_file: Path) -> list[str]:
        """Extract the names of profilers used in the config file by parsing import statements."""
        profilers = []

        with open(config_file, "r") as f:
            for line in f:
                line = line.strip()

                if line.startswith("from Plugins.Profilers."):
                    profiler = (
                        line.split("from Plugins.Profilers.")[1]
                        .split(" import ")[0]
                        .strip()
                    )
                    profilers.append(profiler)

        return profilers
    
    def _validate_plugin_requirements_file(self):
        """Check experiment-specific dependencies from experiment's requirements.txt"""
        for requirements_file in self.framework_root.rglob("requirements.txt"):
            if requirements_file == self.framework_root / "requirements.txt":
                continue
            with open(requirements_file) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    package_name = (
                        line.split("==")[0]
                        .split(">=")[0]
                        .split("<=")[0]
                        .split(">")[0]
                        .split("<")[0]
                        .strip()
                    )
                    result = RequirementCheckResult(package_name,"plugin_requirement")

                    try:
                        importlib.import_module(package_name)
                    except ImportError:
                        result.mark_failure(f"'{package_name}' required by "f"{requirements_file} is not installed")
                        self.failed_checks.append(result)
                    self.results.append(result)

    def _report_results(self):
        if self.failed_checks:
            message = []
            message.append("=" * 50)
            message.append("EXPERIMENT VALIDATION FAILED")
            message.append("=" * 50)

            for idx, check in enumerate(self.failed_checks,start=1):
                message.append("")
                message.append(f"[{idx}] {check.name}")
                message.append(check.error_message)
            raise BaseError(
                "\n".join(message)
            )
        return True

def validate_experiment_requirements(config_file_path: Path) -> bool:
    validator = RequirementsValidator(config_file_path)
    return validator.validate_all()