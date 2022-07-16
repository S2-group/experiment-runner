import time
import sys
from tabulate import tabulate
from ExperimentOrchestrator.Misc.DictConversion import class_to_dict
from ExperimentOrchestrator.Misc.BashHeaders import BashHeaders

###     =========================================================
###     |                                                       |
###     |                    OutputProcedure                    |
###     |       - Give a standard, in one place defined,        |
###     |         output format for use in the application      |
###     |                                                       |
###     |       * Any functionality regarding application       |
###     |         output should be added here                   |
###     |                                                       |
###     =========================================================
class OutputProcedure:
    runner = "[EXPERIMENT_RUNNER]: "

    @staticmethod
    def console_log(txt: str, empty_line=False):
        if empty_line:
            print(" " * 100)

        print(f"{OutputProcedure.runner} {txt}")

    @staticmethod
    def console_log_OK(txt: str, empty_line=False):
        txt = BashHeaders.OKGREEN + txt + BashHeaders.ENDC
        OutputProcedure.console_log(txt, empty_line)

    @staticmethod
    def console_log_WARNING(txt: str, empty_line=False):
        txt = BashHeaders.WARNING + txt + BashHeaders.ENDC
        OutputProcedure.console_log(txt, empty_line)

    @staticmethod
    def console_log_FAIL(txt: str, empty_line=False):
        txt = BashHeaders.FAIL + txt + BashHeaders.ENDC
        OutputProcedure.console_log(txt, empty_line)

    @staticmethod
    def console_log_bold(txt: str, empty_line=False):
        bold_text = f"\033[1m{txt}\033[0m"
        OutputProcedure.console_log(bold_text, empty_line)

    @staticmethod
    def console_log_tabulate_dict(d: dict):     # Used to output dictionary as readable, pretty table
        headers = ['Key', 'Value']
        data = [(k, v) for k, v in d.items()]
        print(f"\n\n{tabulate(data, headers=headers)}\n\n")

    @staticmethod
    def console_log_tabulate_class(class_to_dict):
        d = class_to_dict(class_to_dict)
        headers = ['Key', 'Value']
        data = [(k, v) for k, v in d.items()]
        print(f"\n\n{tabulate(data, headers=headers)}\n\n")

    @staticmethod
    def query_yes_no(question, default="yes") -> bool:
        """Ask a yes/no question via raw_input() and return their answer.

        "question" is a string that is presented to the user.
        "default" is the presumed answer if the user just hits <Enter>.
                It must be "yes" (the default), "no", or None (meaning
                an answer is required of the user).

        The "answer" return value is True for "yes" or False for "no".
        """
        valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
        if default is None:
            prompt = " [y/n] "
        elif default == "yes":
            prompt = " [Y/n] "
        elif default == "no":
            prompt = " [y/N] "
        else:
            raise ValueError(f"invalid default answer: {default}")

        while True:
            txt = question + prompt
            print(f"{OutputProcedure.runner} {BashHeaders.WARNING + txt + BashHeaders.ENDC}", end='')
            choice = input().lower().strip()
            if default is not None and choice == "":
                return valid[default]
            elif choice in valid:
                return valid[choice]
