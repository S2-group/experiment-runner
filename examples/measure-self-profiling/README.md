# Self Measurement with `EnergiBridge`

A simple Linux example, of how to enable the self-measurement feature of experiment-runner.

We use the [EnergiBridge](https://github.com/tdurieux/EnergiBridge) program to measure power consuption
of the entire system while performing any experiment.

As an example program, we simply sleep for a number of seconds while

## Requirements

[EnergiBridge](https://github.com/tdurieux/EnergiBridge) is assumed to be already installed.
To install EnergiBridge, please follow the instructions on their GitHub repo.

By default we assume that (on Linux) your EnergiBridge binary executable is located at /usr/local/bin/energibridge.
If you have installed it in a different location you can specify this in RunnerConfig.

## Running

Set RunnerConfig to True in your RunnerConfig.
Optionally set self_measure_bin to the path of your executable.

From the root directory of the repo, run the following command:

```bash
python experiment-runner/ examples/energibridge-profiling/RunnerConfig.py
```

## Results

The results are generated in the `examples/energibridge-profiling/experiments` folder.

**!!! WARNING !!!**: COLUMNS IN THE `energibridge.csv` FILES CAN BE DIFFERENT ACROSS MACHINES.
ADJUST THE DATAFRAME COLUMN NAMES ACCORDINGLY.

