
# `powerjoular` profiler

A simple Linux example, that runs a python program and measures its CPU usage and power consumption using [PowerJoular](https://gitlab.com/joular/powerjoular).

As an example program, a simple program is used that repeatedly checks if random numbers are prime or not.

## Requirements

Install the requirements to run:

```bash
sudo apt install cpulimit
pip install -r requirements.txt
```

[PowerJoular](https://gitlab.com/joular/powerjoular) is assumed to be already installed.


## Running

From the root directory of the repo, run the following command:

```bash
python experiment-runner/ examples/linux-powerjoular-profiling/RunnerConfig.py
```

## Results

The results are generated in the `examples/linux-powerjoular-profiling/experiments` folder.

