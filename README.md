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

### Events

When a user experiment is run, the following list of events are raised in order automatically by Experiment Runner:

- `BEFORE_EXPERIMENT` - Invoked only once.
- For each variation, the following events are raised in order:
  1. `BEFORE_RUN` Invoked before each variation
  2. `START_RUN`
  3. `START_MEASUREMENT`
  4. `INTERACT`
  5. `CONTINUE` - Only to be used by `OperationType.SEMI` configs. (Not automatically subscribed to by the generated config.)
  6. `STOP_MEASUREMENT`
  7. `STOP_RUN`
  8. `POPULATE_RUN_DATA`
  9. Wait for `RunnerConfig.time_between_runs_in_ms` milliseconds
- `AFTER_EXPERIMENT` - Invoked only once.

*TODO: Add visualization similar to [robot-runner timeline of events](documentation/ICSE_2021.pdf)*

Variations are automatically created by the Experiment Runner in accordance to the user-defined run table (Factors, Treatment levels, and variation exclusions).

Further detailed description of the events and their expected callback behavior can be found in the generated config. One thing to notice in the config is that, each callback function that is associated with a variation, accepts a `context: RunnerContext` parameter that describes the current variation.

## Internal Details

The framework offers an automation of the infrastructure overhead for measurement-based empirical experiments, as a consequence of its design, produced by the following **design drivers**:

- **User Authority**: Give the user full authority over the experiment execution in the Python-based configuration file.
- **Focus on Orchestration**: Orchestrate the experiment on the basis of *events*. These events are characterized by their *moment of execution* in any experiment.
- **Focus on Supporting Infrastructure**: Offer the user all, potentially necessary, supporting features (e.g. factors and treatment levels).

Experiment Runner consists of the following **components**:

- **Experiment orchestrator**: Is in charge of executing the whole experiment according to the experiment configuration provided by the user.
- **Event manager**: Provides the user with subscribable events, to which callback methods can be set, which are called at the appropriate time by the Experiment Orchestrator.
- **Progress manager**: Keeps track of the execution of each run of the experiment.
- **Config Validator**: Provides a validation of a user's configuration file and checks system readiness.

*TODO: Add visualization similar to [robot-runner overview](documentation/overview.png)*

When Experiment Runner is passed a user-defined experiment config via command line arguments, it will:

- Validate the config
- Output the config's values as read by Experiment Runner in the console for user validation
- Create the experiment folder
- Create the run table (.csv), and persist it in the experiment folder
- Execute the experiment on a per-variation basis, going over each variation with its specified treatments in the run table.
