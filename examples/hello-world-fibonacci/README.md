
# Hello World Fibonacci

A simple platform independent example that runs three different fibonacci implementations, 
and measures their power consumption, runtime, and memory usage using [EnergiBridge](https://github.com/tdurieux/EnergiBridge).

Note that admin permissions are needed to make use of EnergiBridge.


## Running

From the root directory of the repo, run the following command:

```bash
python experiment-runner/ examples/hello-world-fibonacci/RunnerConfig.py
```

## Results

The results are generated in the `examples/hello-world-fibonacci/experiments` folder.

**!!! WARNING !!!**: COLUMNS IN THE `energibridge.csv` FILES CAN BE DIFFERENT ACROSS MACHINES.
ADJUST THE DATAFRAME COLUMN NAMES ACCORDINGLY.
