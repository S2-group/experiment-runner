# Experiment-Runner

[![DOI](https://zenodo.org/badge/505379793.svg)](https://doi.org/10.5281/zenodo.15430328)

Experiment Runner is a generic framework to automatically execute measurement-based experiments on any platform. The experiments are user-defined, can be completely customized, and expressed in python code!

The technical details, main features, software architecture, and example experiment using Experiment Runner are presented in our [SCICO 2025 publication](https://www.sciencedirect.com/science/article/pii/S0167642325001546).

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

### Portability Across Users and Machines

When sharing experiments across different users or machines, hardcoded paths in configuration files can cause issues. Experiment Runner supports **environment variables** to make your experiments portable without code changes:

#### Available Environment Variables

- **`EXPERIMENT_RUNNER_OUTPUT_PATH`**: Directory where experiment results are stored
  - Default: `<config-directory>/experiments`
  - Example: `export EXPERIMENT_RUNNER_OUTPUT_PATH="/path/to/results"`

- **`ENERGIBRIDGE_PATH`**: Path to the EnergiBridge executable (for energy measurements)
  - Default: `/usr/local/bin/energibridge`
  - Example: `export ENERGIBRIDGE_PATH="/usr/local/bin/energibridge"`

- **`EXAMPLES_PATH`**: Directory for generating new config templates
  - Default: `<project-root>/examples`
  - Example: `export EXAMPLES_PATH="/home/user/my-experiments"`

#### Using Environment Variables

Set environment variables before running your experiment:

```bash
export EXPERIMENT_RUNNER_OUTPUT_PATH="/data/experiments"
export ENERGIBRIDGE_PATH="/opt/energibridge/bin/energibridge"
python experiment-runner/ MyRunnerConfig.py
```

Your configuration files automatically use these variables if set, with sensible defaults when they are not. This allows the same experiment to run on different machines without any code modifications.

**More information about the profilers and use cases can be found in the [Wiki tab](https://github.com/S2-group/experiment-runner/wiki).**

---
## Remote distribution

Experiment Runner supports **distributed execution across multiple machines** using a master–worker architecture.

### Architecture Overview

- One machine acts as the **Master (Orchestrator)**
  - Owns the experiment `run_table`
  - Assigns runs to workers via a REST API
  - Tracks progress and persists experiment state
  - Triggers lifecycle events (e.g. `AFTER_EXPERIMENT`) when finished

- Multiple machines act as **Workers**
  - Request tasks from the master
  - Execute runs locally using the configured experiment
  - Submit results back to the master

- Communication between master and workers is handled via a lightweight **Flask-based HTTP API**

### How to run it
Start the orchestrator on the master machine:
 ```bash
python experiment-runner/ examples/<example-dir>/<RunnerConfig*.py> --distribute master <host host_nr --port port_nr>
```
On each worker machine, connect to the master:
```bash
experiment-runner/ examples/<example-dir>/<RunnerConfig*.py> --distribute worker --master <orchestor_adress>
```
When the experiment finish it, the master would close automatically, the rest of the workers would need manually closing, they would close after 120s


## How to cite Experiment Runner

If Experiment Runner is helping your research, consider to cite it as follows, thank you!

``` 
@article{SCICO_2025,
  title = {{Experiment {Runner}: a {Tool} for the {Automatic} {Orchestration} of {Experiments} {Targeting} {Software} {Systems}}},
  issn = {0167-6423},
  journal = {Science of Computer Programming},
  author = {Max Karsten and {Andrei Calin} Dragomir and Radu Apsan and Vincenzo Stoico and Ivano Malavolta},
  year = {2025},
  pages = {103415},
  volume = {1},
  url = {https://www.sciencedirect.com/science/article/pii/S0167642325001546},
  doi = {https://doi.org/10.1016/j.scico.2025.103415}
}
``` 

### Contributing
If you want to develop a new feature or ER, or found some bug you want to report we would love to hear from you! Please refer to our [contribution guidelines](https://github.com/S2-group/experiment-runner/wiki/Contributing-to-ER) for information on how to submit PRs or bug reports.

