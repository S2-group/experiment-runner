
# `PicoLog CM3` profiler

A simple Linux example that uses stress-ng on a storage device and measures power consumption 
using a [PicoLog CM3](https://www.picotech.com/download/manuals/PicoLogCM3CurrentDataLoggerUsersGuide.pdf).

As an example program, a simple program is used that repeatedly checks 
if random numbers are prime or not.

## Requirements

A [PicoLog CM3](https://www.picotech.com/download/manuals/PicoLogCM3CurrentDataLoggerUsersGuide.pdf) device is required with a clamp of
the correct variety for your task.

The [PicoLog CM3 Driver](https://www.picotech.com/downloads/linux) is assumed to be already installed.

Instructions to install the drivers for your operating system can be found [here](https://www.picotech.com/downloads/linux).

For this example program, [stress-ng](https://github.com/ColinIanKing/stress-ng) is additionally required as an example of something to measure, but this can be replaced with any other program, or simply a call to sleep if the device is not controlled through software.

Ensure you have the paremeters for stress-ng properly configured, such that an appropriate storage device is selected, and the PicoLog clamp has been correctly attached to the wire.

## Running

From the root directory of the repo, run the following commands:

```bash

# REQUIRED: Ensure this path matches where your PicoLog CM3 drivers are stored
export LD_LIBRARY_PATH="/opt/picoscope/lib" 

python experiment-runner/ examples/picocm3-profiling/RunnerConfig.py
```

## Results

The results are generated in the `examples/picocm3-profiling/experiments` folder.
There should be a unique log file for each variation in the experiment, as well as a run_table.csv file summarizing these log files.
