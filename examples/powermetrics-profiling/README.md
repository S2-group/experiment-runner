
# `powermetrics` profiler

A simple example using the OS X [powermetrics](https://developer.apple.com/library/archive/documentation/Performance/Conceptual/power_efficiency_guidelines_osx/PrioritizeWorkAtTheTaskLevel.html#//apple_ref/doc/uid/TP40013929-CH35-SW10) cli tool to measure the ambient power consumtption of the system.

## Requirements

Install the requirements to run:

```bash
pip install -r requirements.txt
```

## Running

From the root directory of the repo, run the following command:
NOTE: This program must be run as root, as powermetrics requires this

```bash
sudo python experiment-runner/ examples/powermetrics-profiling/RunnerConfig.py
```

## Results

The results are generated in the `examples/powermetrics-profiling/experiments` folder.
