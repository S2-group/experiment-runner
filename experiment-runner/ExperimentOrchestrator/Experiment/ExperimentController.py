import time
import multiprocessing

from ConfigValidator.Config.Models.Metadata import Metadata
from ProgressManager.Output.JSONOutputManager import JSONOutputManager
from ProgressManager.RunTable.Models.RunProgress import RunProgress
from ConfigValidator.Config.Models.OperationType import OperationType
from EventManager.Models.RunnerEvents import RunnerEvents
from ProgressManager.Output.CSVOutputManager import CSVOutputManager
from ExperimentOrchestrator.Experiment.Run.RunController import RunController
from ConfigValidator.Config.RunnerConfig import RunnerConfig
from ProgressManager.Output.OutputProcedure import OutputProcedure as output
from ConfigValidator.CustomErrors.ExperimentOutputErrors import ExperimentOutputPathAlreadyExistsError
from EventManager.EventSubscriptionController import EventSubscriptionController
from ConfigValidator.CustomErrors.ProgressErrors import AllRunsCompletedOnRestartError


###     =========================================================
###     |                                                       |
###     |                  ExperimentController                 |
###     |       - Init and perform runs of correct type         |
###     |       - Perform experiment overhead                   |
###     |       - Perform run overhead (time_btwn_runs)         |
###     |       - Signal experiment end (ClientRunner)          |
###     |                                                       |
###     |       * Experiment config that should be used         |
###     |         throughout the program is declared here       |
###     |         and should not be redeclared (only passed)    |
###     |                                                       |
###     =========================================================
class ExperimentController:

    def __init__(self, config: RunnerConfig, metadata: Metadata):
        self.config = config
        self.metadata = metadata

        self.csv_data_manager = CSVOutputManager(self.config.experiment_path)
        self.json_data_manager = JSONOutputManager(self.config.experiment_path)
        self.run_table = self.config.create_run_table()

        # Create experiment output folder, and in case that it exists, check if we can resume
        self.restarted = False
        try:
            self.config.experiment_path.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            # In order to resume a previous experiment, the following conditions must hold true:
            # 1. The column names of the stored run_table and the generated one must match
            # 2. The stored md5sum for the RunnerConfig-*.py must match the current one
            # If these match:
            #   3. Check for remaining "TODO" in the __done column

            existing_run_table = self.csv_data_manager.read_run_table()
            if not set(existing_run_table[0].keys()) == set(self.run_table[0].keys()):  # check column names
                raise ExperimentOutputPathAlreadyExistsError

            existing_metadata = self.json_data_manager.read_metadata()
            if existing_metadata.md5sum != self.metadata.md5sum:  # check md5sum
                raise ExperimentOutputPathAlreadyExistsError

            self.restarted = True

            # Fill in the run_table.
            # Note that the stored run_table has only a str() representation of the factor treatment levels
            for i, variation in enumerate(existing_run_table):
                upd_variation = self.run_table[i]  # variation that will be updated
                assert (i == int(variation['__run_id'][4:]))
                assert (i == int(upd_variation['__run_id'][4:]))

                for k in map(lambda factor: factor.get_factor_name(),
                             self.config.run_table_model.get_factors()):  # treatment levels remain the same
                    assert (str(upd_variation[k]) == str(variation[k]))

                for k in set(self.config.run_table_model.get_data_columns()).union(
                        ['__done']):  # update data columns and __done column
                    upd_variation[k] = variation[k]

            # Check if there was anything remaining
            todo_run_found = False

            for variation in self.run_table:
                if variation['__done'] != RunProgress.DONE:
                    todo_run_found = True
                    break

            if self.restarted and not todo_run_found:
                raise AllRunsCompletedOnRestartError

        if not self.restarted:
            self.csv_data_manager.write_run_table(self.run_table)
            self.json_data_manager.write_metadata(self.metadata)
        else:
            output.console_log_WARNING(">> WARNING << -- Experiment is restarted!")

        output.console_log_WARNING("Experiment run table created...")

    def do_experiment(self):
        output.console_log_OK("Experiment setup completed...")

        # -- Before experiment
        # TODO: From a user perspective, it would be nice to know if this is a restarted experiment or not (in case something failed)
        output.console_log_WARNING("Calling before_experiment config hook")
        EventSubscriptionController.raise_event(RunnerEvents.BEFORE_EXPERIMENT)

        # -- Experiment
        for variation in self.run_table:
            if variation['__done'] == RunProgress.DONE:
                continue

            output.console_log_WARNING("Calling before_run config hook")
            EventSubscriptionController.raise_event(RunnerEvents.BEFORE_RUN)

            run_controller = RunController(variation, self.config, (self.run_table.index(variation) + 1), len(self.run_table))
            perform_run = multiprocessing.Process(
                target=run_controller.do_run,
                args=[]
            )
            perform_run.start()
            perform_run.join()

            time_btwn_runs = self.config.time_between_runs_in_ms
            if time_btwn_runs > 0:
                output.console_log_bold(f"Run fully ended, waiting for: {time_btwn_runs}ms == {time_btwn_runs / 1000}s")
                time.sleep(time_btwn_runs / 1000)

            if self.config.operation_type is OperationType.SEMI:
                EventSubscriptionController.raise_event(RunnerEvents.CONTINUE)

        output.console_log_OK("Experiment completed...")

        # -- After experiment
        output.console_log_WARNING("Calling after_experiment config hook")
        EventSubscriptionController.raise_event(RunnerEvents.AFTER_EXPERIMENT)
