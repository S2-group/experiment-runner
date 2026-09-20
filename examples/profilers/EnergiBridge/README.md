# `EnergiBridge` profiler

A simple Linux/macOS example, that runs a python program and measures its CPU usage and power consumption using [EnergiBridge](https://github.com/tdurieux/EnergiBridge) through the EnergiBridge plugin.

As a target, a simple program is used that repeatedly checks if random numbers are prime or not.

## Requirements

[EnergiBridge](https://github.com/tdurieux/EnergiBridge) is assumed to be already installed.
To install EnergiBridge, please follow the instructions on the GitHub repo.

## Running

From the root directory of the repo, run the following command:

```bash
python3 experiment-runner/ examples/profilers/EnergiBridge/RunnerConfig.py
```

## Results

The results are generated in the `examples/profilers/EnergiBridge/experiments` folder.
In case there are anomalies such as null, absent, or negative values, a report will be generated in the `examples/profilers/EnergiBridge/experiments` folder.
**!!! WARNING !!!**: COLUMNS IN THE `energibridge.csv` FILES CAN BE DIFFERENT ACROSS MACHINES.
ADJUST THE DATAFRAME COLUMN NAMES ACCORDINGLY.

