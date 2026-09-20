
# `PowerLetrics` profiler

This plugin servers as a ease of use wrapper for the Linux cli tool [powerletrics](https://github.com/green-kernel/powerletrics), that is modeled after
the OSX powermetrics utility.

## Requirements

[powerletrics](https://github.com/green-kernel/powerletrics) is assumed to be already installed.

## Running

From the root directory of the repo, run the following command:

```bash
python experiment-runner/ examples/powerletrics-profiling/RunnerConfig.py
```

## Results

The results are generated in the `examples/powerletrics-profiling/experiments` folder.

In case there are anomalies such as null, absent, or negative values, a report will be generated in the `examples/powerletrics-profiling/experiments` folder.