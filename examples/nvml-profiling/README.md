
# `Nvidia Management Library` profiling

This profiler is a convenience wrapper for the [Nvidia Management Library python library](https://pypi.org/project/nvidia-ml-py/), which is intended for monitoring an managing GPU states. It is also the underlying interface for the nvidia-smi tool. This plugin is intended to make using this library more streamlined, and tries to do much of the heavy lifting for collecting data from the different sources provided by NVML.

Please refer to the documentation for more information on what metrics are provided.

Primarily we support:
- [Some device queries](https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html#group__nvmlDeviceQueries)
- [Some device commands](https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceCommands.html#group__nvmlDeviceCommands)
- [Field value queries](https://docs.nvidia.com/deploy/nvml-api/group__nvmlFieldValueQueries.html#group__nvmlFieldValueQueries)
- [Sampling queries](https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceStructs.html#group__nvmlDeviceStructs_1gcef9440588e5d249cded88ce3efcc6b5)

## Requirements

[A compatible Nvidia GPU](https://docs.nvidia.com/deploy/nvml-api/nvml-api-reference.html#nvml-api-reference). Keep in mind that NVML supports many different generations and types of GPUs. As such many features may or may not be available depending on which GPU you have. 

The NVML library, installed as part of the GPU driver on Windows / Linux.

The [Nvidia Management Library python library](https://pypi.org/project/nvidia-ml-py/).

## Running

From the root directory of the repo, run the following command:

```bash
python experiment-runner/ examples/nvml-profiling/RunnerConfig.py
```

## Results

The results are generated in the `examples/nvml-profiling/experiments` folder, in json format.
