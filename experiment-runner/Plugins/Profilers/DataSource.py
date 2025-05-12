from abc import ABC, abstractmethod
from collections import UserDict
from collections.abc import Iterable, Callable # This import is only valid >= python 3.10 I think
from pathlib import Path
from typing import get_origin, get_args
import platform
import shlex
import os
import ctypes
from enum import StrEnum
import shutil
import ctypes
import os
import subprocess
import threading
import queue

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

class ValueRef:
    def __init__(self, value):
        self.value = value

class DataSource(ABC):
    def __init__(self):
        self._validate_platform()

    def _validate_platform(self):
        if platform.system() in self.supported_platforms:
            return

        raise RuntimeError(f"One of: {self.supported_platforms} is required for this plugin")
    
    def is_admin(self):
        try:
            return os.getuid() == 0
        except:
            return ctypes.windll.shell32.IsUserAdmin() == 1

    def is_admin(self):
        try:
            return os.getuid() == 0
        except:
            return ctypes.windll.shell32.IsUserAdmin() == 1

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

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @staticmethod
    @abstractmethod
    def parse_log(logfile):
        pass

class CLISource(DataSource):
    def __init__(self):
        super().__init__()
        
        self.requires_admin = False

        self.process = None
        self.args = None
        self._logfile = ValueRef(None)

        super().__init__()

    def __del__(self):
        if self.process:
            self.process.kill()
    
    @property
    def logfile(self):
        return self._logfile.value
    
    @logfile.setter
    def logfile(self, value):
        self._logfile.value = value

    @property
    @abstractmethod
    def parameters(self) -> ParameterDict:
        pass

    def _validate_platform(self):
        super()._validate_platform()
                
        if shutil.which(self.source_name) is None       \
            and not os.access(self.source_name, os.X_OK):
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

        if self.requires_admin:
            cmd = f"sudo {cmd}"
        
        # Transform the parameter dict into string format to be parsed by shlex
        for p, v in self.args.items():
            if v == None:
                cmd += f" {p}"
            elif isinstance(v, ValueRef):
                cmd += f" {p} {v.value}"
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

    def stop(self, wait=False):
        if not self.process:
            return

        try:
            if not wait:
                self.process.terminate()
            
            stdout, stderr = self.process.communicate(timeout=None if wait else 5)

        except Exception as e:
            self.process.kill()
            raise RuntimeError(f"{self.source_name} process could not stop {e}")
        
        self._validate_stop(stdout.decode("utf-8"), stderr.decode("utf-8"))
        return stdout.decode("utf-8")

class DeviceSource(DataSource):
    def __init__(self):
        super().__init__()

        self.device_handle = None
        self.process = None
        self.sample_frequency=None

        # Create the pipe that implements graceful shutdown
        self.stop_thread = threading.Event()
        self.thread_queue = queue.Queue(maxsize=1)

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
    def log(self):
        if not self.device_handle:
            raise RuntimeError("A device must be selected before it can be queried")
        
        if threading.current_thread().name != "DeviceWorker":
            raise RuntimeError("Dont call log directly, call start() to begin logging")

    def start(self):
        if self.process:
            raise RuntimeError("This module has already been started. Call stop() to start again")

        try:
            self.process = threading.Thread(target=self.log,
                                            name="DeviceWorker")

            self.process.start()
        except Exception as e:
            self.process.terminate()
            raise RuntimeError(f"Could not start logging process: {e}")

    def stop(self):
        if not self.process:
            return

        if not self.process.is_alive():
            raise RuntimeError("Process terminated early, check configuration")
        
        ret = None
        timeout = self.sample_frequency * 2
        try:
            # Send the shutdown signal
            self.stop_thread.set()
            ret = self.thread_queue.get(block=True, timeout=timeout)
            self.thread_queue.task_done()

            self.process.join(timeout)
        except:
            raise RuntimeError("An error occured while joining the thread")

        if self.process.is_alive():
            raise RuntimeError("The device thread could not be stopped")

        self.stop_thread.clear()
        self.process = None

        return ret


