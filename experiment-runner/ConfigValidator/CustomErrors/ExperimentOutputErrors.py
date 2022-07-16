from ConfigValidator.CustomErrors.BaseError import BaseError
from ExperimentOrchestrator.Misc.BashHeaders import BashHeaders

class ExperimentOutputFileDoesNotExistError(BaseError):
    def __init__(self):
        super().__init__("The " + BashHeaders.UNDERLINE + "experiment_path" + BashHeaders.ENDC + BashHeaders.FAIL + 
                            " (experiment output folder) exists, but the " + 
                            BashHeaders.UNDERLINE + "run_table.csv" + BashHeaders.ENDC + BashHeaders.FAIL +
                            " does not exist.\n" +
                            "Experiment-runner cannot restart!")