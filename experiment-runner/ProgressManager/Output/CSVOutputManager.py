from ProgressManager.RunTable.Models.RunProgress import RunProgress
from ConfigValidator.CustomErrors.ExperimentOutputErrors import ExperimentOutputFileDoesNotExistError
from ProgressManager.Output.OutputProcedure import OutputProcedure as output
from ProgressManager.Output.BaseOutputManager import BaseOutputManager

from tempfile import NamedTemporaryFile
import shutil
import csv
import os
import pwd
import getpass
from typing import Dict, List


class CSVOutputManager(BaseOutputManager):
    def read_run_table(self) -> List[Dict]:
        read_run_table = []
        try:
            with open(self._experiment_path / 'run_table.csv', 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    # if value was integer, stored as string by CSV writer, then convert back to integer.
                    for key, value in row.items():
                        if value.isnumeric():
                            row[key] = int(value)

                        if key == '__done':
                            row[key] = RunProgress[value]

                    read_run_table.append(row)
            
            return read_run_table
        except:
            raise ExperimentOutputFileDoesNotExistError

    def write_run_table(self, run_table: List[Dict]):
        try:
            with open(self._experiment_path / 'run_table.csv', 'w', newline='') as myfile:
                writer = csv.DictWriter(myfile, fieldnames=list(run_table[0].keys()))
                writer.writeheader()
                for data in run_table:
                    data['__done'] = data['__done'].name
                    writer.writerow(data)
        except:
            raise ExperimentOutputFileDoesNotExistError

    # TODO: Nice To have
    def shuffle_experiment_run_table(self):
        pass
    
    def update_row_data(self, updated_row: dict):
        tempfile = NamedTemporaryFile(mode='w', delete=False)

        with open(self._experiment_path / 'run_table.csv', 'r') as csvfile, tempfile:
            reader = csv.DictReader(csvfile, fieldnames=list(updated_row.keys()))
            writer = csv.DictWriter(tempfile, fieldnames=list(updated_row.keys()))

            for row in reader:
                if row['__run_id'] == updated_row['__run_id']:
                    # When the row is updated, it is an ENUM value again.
                    # Write as human-readable: enum_value.name
                    updated_row['__done'] = updated_row['__done'].name
                    writer.writerow(updated_row)
                else:
                    writer.writerow(row)

        shutil.move(tempfile.name, self._experiment_path / 'run_table.csv')
        
        # Change permissions so the files can be accessed if run as root (needed for some plugins)
        user = pwd.getpwnam(getpass.getuser())
        os.chown(self._experiment_path / "run_table.csv", user.pw_uid, user.pw_gid)

        output.console_log_WARNING(f"CSVManager: Updated row {updated_row['__run_id']}")

        # with open(self.experiment_path + '/run_table.csv', 'w', newline='') as myfile:
        #     wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
        #     wr.writerow(updated_row)

    # for row in reader:
    # if name == row['name']:
    #     row['name'] = input("enter new name for {}".format(name))
    # # write the row either way
    # writer.writerow({'name': row['name'], 'number': row['number'], 'address': row['address']})
