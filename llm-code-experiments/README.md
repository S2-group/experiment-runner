# `EnergiBridge` profiler

A simple Linux example, that runs a python program and measures its CPU usage
and power consumption using [EnergiBridge](https://github.com/tdurieux/EnergiBridge)

As an example program, a simple program is used that repeatedly checks 
if random numbers are prime or not.

## Requirements

[EnergiBridge](https://github.com/tdurieux/EnergiBridge) is assumed to be already installed.

To install EnergiBridge, please follow the instructions on their GitHub repo.


## Running

From the root directory of the repo, run the following command:

```bash
python experiment-runner/ llm-code-experiments/RunnerConfig.py
```

## Results

The results are generated in the `llm-code-experiments/experiments` folder.

**!!! WARNING !!!**: COLUMNS IN THE `energibridge.csv` FILES CAN BE DIFFERENT ACROSS MACHINES.
ADJUST THE DATAFRAME COLUMN NAMES ACCORDINGLY.

