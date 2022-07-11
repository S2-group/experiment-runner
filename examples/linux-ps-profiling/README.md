
# `ps` profiler

A simple Linux example, that runs an ELF binary and measures its CPU usage using [ps](https://man7.org/linux/man-pages/man1/ps.1.html).

As an example ELF binary, a simple C program is used that repeatedly checks if random numbers are prime or not.

## Requirements

Install the requirements to run:

```bash
sudo apt install cpulimit gcc
pip install -r requirements.txt
```

## Running

From the root directory of the repo, run the following command:

```bash
python experiment-runner/ examples/linux-ps-profiling/RunnerConfig.py
```

## Results

The results are generated in the `examples/linux-ps-profiling/experiments` folder.

