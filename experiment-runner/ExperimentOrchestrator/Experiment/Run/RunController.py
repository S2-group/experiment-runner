from ProgressManager.RunTable.Models.RunProgress import RunProgress
from EventManager.Models.RunnerEvents import RunnerEvents
from EventManager.EventSubscriptionController import EventSubscriptionController
from ExperimentOrchestrator.Architecture.Processify import processify
from ExperimentOrchestrator.Experiment.Run.IRunController import IRunController
from ProgressManager.Output.OutputProcedure import OutputProcedure as output

class RunController(IRunController):
    @processify
    def do_run(self):
        # -- Start run
        output.console_log_WARNING("Calling start_run config hook")
        EventSubscriptionController.raise_event(RunnerEvents.START_RUN, self.run_context)

        # -- Start measurement
        output.console_log_WARNING("... Starting measurement ...")
        EventSubscriptionController.raise_event(RunnerEvents.START_MEASUREMENT, self.run_context)

        # -- Start interaction
        output.console_log_WARNING("Calling interaction config hook")

        EventSubscriptionController.raise_event(RunnerEvents.INTERACT, self.run_context)
        output.console_log_OK("... Run completed ...")

        # -- Stop measurement
        output.console_log_WARNING("... Stopping measurement ...")
        EventSubscriptionController.raise_event(RunnerEvents.STOP_MEASUREMENT, self.run_context)

        output.console_log_WARNING("Calling populate_run_data config hook")
        updated_run_data = EventSubscriptionController.raise_event(RunnerEvents.POPULATE_RUN_DATA, self.run_context)
        if updated_run_data is None:
            row = self.run_context.run_variation
            row['__done'] = RunProgress.DONE
            self.data_manager.update_row_data(row)
        else:
            updated_run_data['__done'] = RunProgress.DONE
            self.data_manager.update_row_data(updated_run_data)

        # -- Stop run
        output.console_log_WARNING("Calling stop_run config hook")
        EventSubscriptionController.raise_event(RunnerEvents.STOP_RUN, self.run_context)
