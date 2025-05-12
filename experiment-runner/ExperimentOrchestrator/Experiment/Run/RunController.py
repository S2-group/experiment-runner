import subprocess
import os

from ProgressManager.RunTable.Models.RunProgress import RunProgress
from EventManager.Models.RunnerEvents import RunnerEvents
from EventManager.EventSubscriptionController import EventSubscriptionController
from ExperimentOrchestrator.Architecture.Processify import processify
from ExperimentOrchestrator.Experiment.Run.IRunController import IRunController
from ProgressManager.Output.OutputProcedure import OutputProcedure as output

class RunController(IRunController):
    # Start EnergiBridge measurements
    def start_eb(self):
        if not self.config.self_measure:
            return

        eb_args = [self.config.self_measure_bin, "--summary"]

        if self.config.self_measure_logfile:
            eb_args += ["--output", 
                        os.path.join(self.run_context.run_dir.resolve(), self.config.self_measure_logfile)]
        else:
            eb_args += ["-o", "/dev/null"]

        eb_args += ["--", "sleep", "1000000"]

        try:
            self.eb_proc = subprocess.Popen(eb_args, stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE, text=True)
        except Exception as e:
            output.console_log_FAIL(f"Error while starting EnergiBridge:\n{e}")

    # Stop EnergiBridge  
    def stop_eb(self):
        if not self.config.self_measure or not self.eb_proc:
            return

        try:
            self.eb_proc.terminate()
            stdout, stderr = self.eb_proc.communicate()
            
            if stderr:
                output.console_log_FAIL(f"EnergiBridge error encountered:\n{stderr}")

            if "joules:" not in stdout:
                output.console_log_FAIL("EnergiBridge error: Could not extract joules from output")
            
            self.run_context.execute_run["self-measure"] = round(float(stdout.split(" ")[6]), 3)

        except Exception as e:
            output.console_log_FAIL(f"Failed to stop EnergiBridge:\n{e}")

    @processify
    def do_run(self):
        # Start EnergiBridge
        self.start_eb()

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

        # -- Stop run
        output.console_log_WARNING("Calling stop_run config hook")
        EventSubscriptionController.raise_event(RunnerEvents.STOP_RUN, self.run_context)

        # -- Collect data from measurements
        output.console_log_WARNING("Calling populate_run_data config hook")
        user_run_data = EventSubscriptionController.raise_event(RunnerEvents.POPULATE_RUN_DATA, self.run_context)
        
        # Stop EnergiBridge
        self.stop_eb()

        if user_run_data:
            # TODO: check if data columns exist and if yes, if they match
            updated_run_data = {**self.run_context.execute_run,
                                **user_run_data}  # shallowly-merged dictionary. Takes values from first; replacing matching keys with values from second.
        else:
            updated_run_data = self.run_context.execute_run

        updated_run_data['__done'] = RunProgress.DONE
        self.data_manager.update_row_data(updated_run_data)
