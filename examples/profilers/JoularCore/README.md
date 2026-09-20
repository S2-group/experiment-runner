
# `JoularCore` profiler

The `RunnerConfig.py` contains a Linux example, that runs a python program and measures its CPU usage and power consumption using [JoularCore](https://github.com/joular/joularcore.git).

As an example program, a simple program is used that repeatedly checks if random numbers are prime or not.

## Requirements

[JoularCore](https://github.com/joular/joularcore.git) is assumed to be already installed and available in the system PATH.

## Running

From the root directory of the repo, run the following command:
**NOTE**: This program must be run as root, as powerjoular requires this for its use of Intel RAPL.

```bash
sudo python3 experiment-runner/ examples/joularcore-profiling/RunnerConfig.py
```

## Results

The results are generated in the `examples/joularcore-profiling/experiments` folder.

In case there are anomalies such as null, absent, or negative values, a report will be generated in the `examples/joularcore-profiling/experiments` folder
