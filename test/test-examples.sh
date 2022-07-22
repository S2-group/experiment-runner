#!/bin/bash

export PYTHONUNBUFFERED=1
export PYENV_VIRTUALENV_DISABLE_PROMPT=1

if ! command -v python &> /dev/null
then
    echo "Script ran from PyCharm sh shell. Setting python"
    # hacky way for `alias` in sh
    python () {
        "${PROJECT_DIR}"/python "$@"
    }
fi

set -e
examples=()
for directory in examples/*/ ; do
    if [ "$(basename $directory)" = "__pycache__" ]; then
        continue
    fi
    examples+=("$directory")
done


for example in "${examples[@]}"; do
    echo "Testing $example"

    echo " [*] Cleaning"
    rm -rf "$example/experiments"

    echo " [*] Executing"
    python experiment-runner/ "${example}/RunnerConfig.py"
done

