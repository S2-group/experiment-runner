from abc import ABC
from collections import UserDict
import platform
import shutil

class DataSource(ABC):
    def __init__(self):
        self.__validate_platform()

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

    @abstractmethod
    @staticmethod
    def parse_log():
        pass

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

class ParameterDict(UserDict):
    def __setitem__(self, key, item):
        pass

    def __getitem__(self, key):
        pass

    def __delitem__(self, key):
        pass

class CLISource(DataSource):
    def __init__(self):
        self.super().__init__()
        self.process = None
        self.default_args = None
        self.additional_args = None
        
    def __validate_platform(self):
        self.super().__validate_platform()
                
        if shutil.which("powermetrics") is None:
            raise RuntimeError(f"The {self.source_name} cli tool is required for this plugin")
    
    def __validate_start(self, stdout, stderr):
        if stderr:
            raise RuntimeError(f"{self.source_name} did not start correctly")

    def __validate_stop(self, stdout, stderr):
        if stderr:
            raise RuntimeWarning(f"{self.source_name} did not stop correctly")

    @abstractmethod
    def __format_cmd(self):
        pass
    
    @abstractmethod
    def update_parameters(self, new_parameters: dict):
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

 

