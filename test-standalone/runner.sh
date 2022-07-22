#!/bin/bash

export PYTHONUNBUFFERED=1
export PYENV_VIRTUALENV_DISABLE_PROMPT=1
export PYTHONPATH="$PYTHONPATH:${PROJECT_DIR}/experiment-runner:${PROJECT_DIR}/test-standalone"

if ! command -v python &> /dev/null
then
    echo "Script ran from PyCharm sh shell. Setting python"
    # hacky way for `alias` in sh
    python () {
        "${PROJECT_DIR}"/python "$@"
    }
fi

set -e
tests=( # TODO: gather_tests recursively
  "${PROJECT_DIR}/test-standalone/core/shuffling"
  "${PROJECT_DIR}/test-standalone/core/arbitrary-objects"
  "${PROJECT_DIR}/test-standalone/plugins/CodecarbonWrapper/individual"
  "${PROJECT_DIR}/test-standalone/plugins/CodecarbonWrapper/combined"
)

echo "CWD: $(pwd)"
for test in "${tests[@]}"; do
    echo "Testing $test"

    echo " [*] Cleaning"
    rm -rf "$test/experiments"

    echo " [*] Executing"
    python experiment-runner/ "$test/RunnerConfig.py"

    # Simulate a crash
    if [ -f "$test/Crasher.py" ]; then
        echo " [*] Modifying generated run table to simulate a crash"
        python "$test/Crasher.py"

        echo " [*] Re-running experiment"
        python experiment-runner/ "$test/RunnerConfig.py"
    fi

    echo " [*] Validating"
    python "$test/Validator.py"
    echo " [*] $test SUCCESS"
done

