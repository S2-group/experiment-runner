from abc import ABC
from collections import UserDict
import platform
import shutil

class ParameterDict(UserDict):
    def valid_key(self, key):
        return  isinstance(key, str)            \
                or isinstance(key, tuple)  \
                or isinstance(key, list[str])
    
    def str_to_tuple(self, key):
        return tuple([key])

    def __setitem__(self, key, item):
        if not self.valid_key(key):
            raise RuntimeError("Unexpected key value")

        for params in self.data.keys():
            if set(key).issubset(params):
                raise RuntimeError("Keys cannot have duplicate elements")
        
        if isinstance(key, str):
            key = self.str_to_tuple(key)

        super().__setitem__(tuple(key), item)
    
    def __getitem__(self, key):
        if not self.valid_key(key):
            raise RuntimeError("Unexpected key, expected `str` or `list[str]`")
            
        if isinstance(key, str):
            key = self.str_to_tuple(key)

        for params, val in self.data.items():
            if set(key).issubset(params):
                return val
               
        # Pass to default handler if we cant find it
        super().__getitem__(tuple(key))
    
    # Must pass entire valid key to delete element
    def __delitem__(self, key):
        if isinstance(key, str):
            key = self.str_to_tuple(key)

        super().__delitem__(tuple(key))

class DataSource(ABC):
    def __init__(self):
        self.__validate_platform()
        self.logfile = None

    def __validate_platform(self):
        for platform in self.supported_platforms:
            if "OSX" in platform.system():
                return

        raise RuntimeError(f"One of: {self.supported_platforms} is required for this plugin")

    @property
    @abstractmethod
    def supported_platforms(self): -> list[str]
        pass

    @property
    @abstractmethod
    def source_name(self): -> str
        pass
        
    @abstractmethod
    def __del__(self):
        pass

    @staticmethod
    @abstractmethod
    def parse_log():
        pass


class CLISource(DataSource):
    def __init__(self):
        self.super().__init__()

        self.process = None
        self.args = None
    
    @property
    @abstractmethod
    def parameters(self): -> ParameterDict
        pass

    def __validate_platform(self):
        self.super().__validate_platform()
                
        if shutil.which(self.source_name) is None:
            raise RuntimeError(f"The {self.source_name} cli tool is required for this plugin")
    
    def __validate_start(self, stdout, stderr):
        if stderr:
            raise RuntimeError(f"{self.source_name} did not start correctly")

    def __validate_stop(self, stdout, stderr):
        if stderr:
            raise RuntimeWarning(f"{self.source_name} did not stop correctly")
    
    def __validate_parameters(self, parameters):
        # TODO: Ensure types match here
        pass

    def __format_cmd(self):
        cmd = [self.source_name]
        
        # Add in the default parameters
        for p, v in self.default_parameters.items():
            #TODO: Parse a parameter dict into a string format
            pass
            
        return cmd

    def update_parameters(self, new_parameters: dict):
        for p, v in new_params.items():
            # TODO: parse parameters, add to parameter dict
            pass

    def start(self):
        try:
            self.pm_process = subprocess.Popen(self.__format_cmd(), 
                                               stdout=subprocess.PIPE, 
                                               stderr=subprocess.PIPE)

            stdout, stderr = subprocess.communicate()

        except Exception as e:
            raise RuntimeError(f"{self.source_name} process could not start: {e}")
        
        self.__validate_start(stdout, stderr)

    def stop(self):
        if not self.process:
            return

        try:
            self.process.terminate()
            stdout, stderr = self.process.communicate()

        except Exception as e:
            raise RuntimeError(f"{self.source_name} process could not stop {e}")
        
        self.__validate_stop(stdout, stderr)

class DeviceSource(DataSource):
    def __init__(self):
        self.super().__init__()
        self.device_handle = None

    def __del__():
        if self.device_handle:
            self.close_device()
    
    @abstractmethod
    def list_devices(self):
        pass

    @abstractmethod
    def open_device(self):
        pass
    
    @abstractmethod
    def close_device(self):
        pass
    
    @abstractmethod
    def set_mode(self):
        pass
    
    @abstractmethod
    def log(self, timeout: int = 60, logfile: Path = None):
        pass

