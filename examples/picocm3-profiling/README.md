
# `PicoLog CM3` profiler

A simple Linux example that uses stress-ng on a storage device and measures power consumption 
using a [PicoLog CM3](https://github.com/tdurieux/EnergiBridge).

As an example program, a simple program is used that repeatedly checks 
if random numbers are prime or not.

## Requirements

A [PicoLog CM3](https://github.com/tdurieux/EnergiBridge) device is required with a clamp of
the correct variety for your task

The [PicoLog CM3 Driver](https://github.com/tdurieux/EnergiBridge) is assumed to be already installed.

Instructions to install the drivers for your operating system can be found [here]().

## Running

From the root directory of the repo, run the following command:

```bash
python experiment-runner/examples/picocm3-profiling/RunnerConfig.py
```

## Results

The results are generated in the `examples/picocm3-profiling/experiments` folder.
