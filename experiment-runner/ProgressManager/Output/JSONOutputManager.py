from ConfigValidator.Config.Models.Metadata import Metadata
from ProgressManager.Output.BaseOutputManager import BaseOutputManager

import jsonpickle


class JSONOutputManager(BaseOutputManager):

    def write_metadata(self, metadata: Metadata):
        with open(self._experiment_path / "metadata.json", 'w') as json_file:
            json_file.write(jsonpickle.encode(metadata, indent=2))

    def read_metadata(self) -> Metadata:
        with open(self._experiment_path / "metadata.json", 'r') as json_file:
            json_data = json_file.read()
        return jsonpickle.decode(json_data)
