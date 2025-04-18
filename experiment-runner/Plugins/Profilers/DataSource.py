from abc import ABC, abstractmethod
from collections import UserDict
from collections.abc import Iterable # This import is only valid >= python 3.10 I think
from pathlib import Path
from typing import get_origin, get_args
import platform
import shlex
from enum import StrEnum
import shutil
import subprocess

class ParameterDict(UserDict):
    def valid_key(self, key):
        return  isinstance(key, str)            \
                or isinstance(key, tuple)       \
                or isinstance(key, list[str])
    
    def str_to_tuple(self, key):
        return tuple([key])

    def __setitem__(self, key, item):
        if not self.valid_key(key):
            raise RuntimeError("Unexpected key value")

        if isinstance(key, str):
            key = self.str_to_tuple(key)

        for params in self.data.keys():
            if set(key).issubset(params):
                raise RuntimeError("Keys cannot have duplicate elements")

        super().__setitem__(tuple(key), item)
    
    def __getitem__(self, key):
        if not self.valid_key(key):
            raise RuntimeError("Unexpected key type, expected `str` or `list[str]`")

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

    def __contains__(self, key):
        if isinstance(key, str):
            key = self.str_to_tuple(key)

        for params, val in self.data.items():
            if set(key).issubset(params):
                return True

        return False

class DataSource(ABC):
    def __init__(self):
        self._validate_platform()
        self.logfile = None

    def _validate_platform(self):
        if platform.system() in self.supported_platforms:
            return

        raise RuntimeError(f"One of: {self.supported_platforms} is required for this plugin")

    @property
    @abstractmethod
    def supported_platforms(self) -> list[str]:
        pass

    @property
    @abstractmethod
    def source_name(self) -> str:
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
        super().__init__()

        self.process = None
        self.args = None

    def __del__(self):
        if self.process:
            self.process.kill()
    
    @property
    @abstractmethod
    def parameters(self) -> ParameterDict:
        pass

    def _validate_platform(self):
        super()._validate_platform()
                
        if shutil.which(self.source_name) is None:
            raise RuntimeError(f"The {self.source_name} cli tool is required for this plugin")
    
    def _validate_start(self):
        if self.process.poll() != None:
            raise RuntimeError(f"{self.source_name} did not start correctly")

    def _validate_stop(self, stdout, stderr):
        if stderr:
            raise RuntimeWarning(f"{self.source_name} did not stop correctly, or encountered an error: {stderr}")
    
    # Should work well with single level type generics e.g. list[int]
    # TODO: Expand this to be more robust with other types
    def _validate_type(self, param, p_type):
        if p_type != str and not isinstance(param, StrEnum) and isinstance(param, Iterable):
            if type(param) != get_origin(p_type):
                return False
            
            if type(param[0]) != get_args(p_type)[0]:
                return False
            
            return True
        
        return isinstance(param, p_type)  

    def _validate_parameters(self, parameters: dict):
        for p, v in parameters.items():
            if p not in self.parameters:
                raise RuntimeError(f"Unexpected parameter: {p}")
            
            if self.parameters[p] == None:
                continue

            if not self._validate_type(v, self.parameters[p]):
                raise RuntimeError(f"Unexpected type: {type(v)} for parameter {p}, expected {self.parameters[p]}")

    def _format_cmd(self):
        self._validate_parameters(self.args)
        cmd = self.source_name
        
        # Transform the parameter dict into string format to be parsed by shlex
        for p, v in self.args.items():
            if v == None:
                cmd += f" {p}"
            elif isinstance(v, Iterable) and not (isinstance(v, StrEnum) or isinstance(v, str)):
                cmd += f" {p} {",".join(map(str, v))}"
            else:
                cmd += f" {p} {v}"

        return cmd

    def update_parameters(self, add: dict={}, remove: list[str]=[]):
        # Check if the new sets of parameters are sane
        self._validate_parameters(add)

        for p, v in add.items():
            self.args[p] = v

        for p in remove:
            if p in self.args.keys():
                del self.args[p]
        
        # Double check that our typeing is still valid
        self._validate_parameters(self.args)

    def start(self):
        try:
            self.process = subprocess.Popen(shlex.split(self._format_cmd()), 
                                            stdout=subprocess.PIPE, 
                                            stderr=subprocess.PIPE)
        except Exception as e:
            self.process.kill()
            raise RuntimeError(f"{self.source_name} process could not start: {e}")
        
        self._validate_start()

    def stop(self):
        if not self.process:
            return

        try:
            self.process.terminate()
            stdout, stderr = self.process.communicate(timeout=5)

        except Exception as e:
            self.process.kill()
            raise RuntimeError(f"{self.source_name} process could not stop {e}")
        
        self._validate_stop(stdout.decode("utf-8"), stderr.decode("utf-8"))
        return stdout.decode("utf-8")

class DeviceSource(DataSource):
    def __init__(self):
        super().__init__()
        self.device_handle = None

    def __del__(self):
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

