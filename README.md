# Experiment-Runner

Experiment Runner is a generic framework to automatically execute measurement-based experiments on any platform. The experiments are user-defined, can be completely customized, and expressed in python code!

*(Experiment Runner is a generalization of our previous successful tool, [Robot Runner](https://github.com/S2-group/robot-runner), for which you can read more in our [ICSE 2021 tool demo paper](https://github.com/S2-group/robot-runner/tree/master/documentation/ICSE_2021.pdf).)*

## Features

- **Run Table Model**: Framework support to easily define an experiment's measurements with Factors, their Treatment levels, exclude certain combinations of Treatments, and add data columns for storing aggregated data.
- **Restarting**: If an experiment was not entirely completed on the last invocation (e.g. some variations crashes), experiment runner can be re-invoked to finish any remaining experiment variations.
- **Persistency**: Raw and aggregated experiment data per variation can be persistently stored.
- **Operational Types**: Two operational types: `AUTO` and `SEMI`, for more fine-grained experiment control.
- **Progress Indicator**: Keeps track of the execution of each run of the experiment
- **Target and profiler agnostic**: Can be used with any target to measure (e.g. ELF binary, .apk over adb, etc.) and with any profiler (e.g. WattsUpPro, etc.)

## Requirements

The framework has been tested with Python3 version 3.8, but should also work with any higher version. It has been tested under Linux and macOS. It does **not** work on Windows (at the moment).

To get started:

```bash
git clone https://github.com/S2-group/experiment-runner.git
cd experiment-runner/
pip install -r requirements.txt
```

To verify installation, run:

```bash
python experiment-runner/ examples/hello-world/RunnerConfig.py
```

## Running

In this section, we assume as the current working directory, the root directory of the project.

### Starting with the examples

To run any of the examples, run the following command:

```bash
python experiment-runner/ examples/<example-dir>/<RunnerConfig*.py>
```

Each example is accompanied with a README for further information. It is recommended to start with the [hello-world](examples/hello-world) example to also test your installation. 

Note that once you successfully run an experiment, the framework will not allow you to run the same experiment again under, giving the message:

```log
[FAIL]: EXPERIMENT_RUNNER ENCOUNTERED AN ERROR!
The experiment was restarted, but all runs are already completed.
```

This is to prevent you from accidentally overwriting the results of a previously run experiment! In order to run again the experiment, either delete any previously generated data (by default "experiments/" directory), or modify the config's `name` variable to a different name.

### Creating a new experiment

First, generate a config for your experiment:

```bash
python experiment-runner/ config-create [directory]
```

When running this command, where `[directory]` is an optional argument, a new config file with skeleton code will be generated in the given directory. The default location is the `examples/` directory. This config is similar to the [hello-world](examples/hello-world) example.

Feel free to move the generated config to any other directory. You can modify its contents and write python code to define your own measurement-based experiment(s). At this stage, you might find useful the [linux-ps-profiling](examples/linux-ps-profiling) example.

Once the experiment has been coded, the experiment can be executed by Experiment Runner. To do this, run the following command:

```bash
python experiment-runner/ <MyRunnerConfig.py>
```

The results of the experiment will be stored in the directory `RunnerConfig.results_output_path/RunnerConfig.name` as defined by your config variables.

**More information about the profilers and use cases can be found in the [Wiki tab](https://github.com/S2-group/experiment-runner/wiki).**

