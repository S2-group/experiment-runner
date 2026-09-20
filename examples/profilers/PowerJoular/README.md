
# `PowerJoular` profiler

A simple Linux example, that runs a python program and measures its CPU usage and power consumption using [PowerJoular](https://github.com/joular/powerjoular).

As an example program, a simple program is used that repeatedly checks if random numbers are prime or not.

## Requirements

Install the requirements to run:

```bash
sudo apt install cpulimit
pip install pandas
```

[PowerJoular](https://github.com/joular/powerjoular) is assumed to be already installed.

To avoid having to run the experiment with root permissions, you can set up PowerJoular to be used by a normal user by applying the same configuration to the compiled PowerJoular binary (default location: `/usr/bin/powerjoular`) as suggested in [EnergiBridge](https://github.com/tdurieux/EnergiBridge) README.

## Running

From the root directory of the repository, run the following command:
NOTE: This program must be run as root, as powerjoular requires this for its use of Intel RAPL.

```bash
python experiment-runner/ examples/PowerJoular/RunnerConfig.py
```

## Results

The results are generated in the `examples/linux-powerjoular-profiling/experiments` folder.

In case there are anomalies such as null, absent, or negative values, a report will be generated in the `examples/linux-powerjoular-profiling/experiments` folder.