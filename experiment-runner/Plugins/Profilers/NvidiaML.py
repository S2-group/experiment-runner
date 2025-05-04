import enum
import time
import inspect
import json
import re
import pynvml as nvml
from pathlib import Path
import threading
from collections.abc import Callable

from Plugins.Profilers.DataSource import DeviceSource, ParameterDict

# Define a custom enum wrapper to help generating enums from the nvml enums
class NVML_EnumMeta(enum.EnumType):
    def __call__(cls, *args, prefix=None, suffix=None, **kwargs):
        # We are not creating a new enum here, execute normally
        if prefix is None and suffix is None:
            return super().__call__(*args, **kwargs)
        
        # Interpose on enum creation to have nice strings
        assert(prefix != None or suffix != None)

        cls.name_prefix = prefix
        cls.name_suffix = suffix
        
        members = {name: val 
                   for name, val in inspect.getmembers(nvml) 
                   if (True if not prefix else name.startswith(prefix))
                   and (True if not suffix else name.endswith(suffix))}

        return super().__call__(*args, names=members, **kwargs)

class NVML_Enum(enum.Enum, metaclass=NVML_EnumMeta):
    @property
    def name(self):
        name = self._name_
        if self.name_prefix:
            name = name.lstrip(self.name_prefix)
        if self.name_suffix:
            name = name.rstrip(self.name_suffix)

        return name.lower()

# Split the name on capital letters, capitalize the words and and underscores
def nvml_fn_to_name(func_name):
    return "NVML_" + "_".join(list(map(lambda x: x.upper(),
            re.findall("[A-Z](?:[a-z]+|[A-Z]*(?=[A-Z]|$))", func_name.split("_")[0]))))

query_fns    = {"static": # These values should remain the same durring execution
                ["Name", "UUID", "Serial", "Index", "Architecture",
                "NumGpuCores", "VbiosVersion", "Brand", "NumFans",
                "MemoryInfo", "BusType", "BoardId", "Attributes",
                "BoardPartNumber", "MinMaxFanSpeed", "ComputeMode",
                "PersistenceMode", "PowerManagementMode", "EnforcedPowerLimit",
                "PowerManagementLimit", "PowerManagementDefaultLimit",
                "PowerManagementLimitConstraints", "MaxCustomerBoostClock",
                "PowerSource", "TargetFanSpeed", "TemperatureThreshold",
                "SupportedPerformanceStates", "MaxClockInfo", "MinMaxClockOfPState"],
                "dynamic": # These values might change durring execution
                ["PowerUsage", "TotalEnergyConsumption", "Temperature",
                "FanSpeed_v2", "UtilizationRates", "PerformanceState",
                "ClockInfo"]}

# Shared type to allow passing of either
class NVML_Query(enum.Enum):
    pass
NVML_Static_Query       = NVML_Query("NVML_Static_Query", 
                               zip(list(map(nvml_fn_to_name, query_fns["static"])), query_fns["static"]))
NVML_Dynamic_Query      = NVML_Query("NVML_Dynamic_Query", 
                                zip(list(map(nvml_fn_to_name, query_fns["dynamic"])), query_fns["dynamic"]))
# There are a lot of these, generate them automatically
NVML_Field              = NVML_Enum("NVML_Field", prefix="NVML_FI_DEV_")
NVML_Sample             = NVML_Enum("NVML_Sample", prefix="NVML_", suffix="_SAMPLES")
NVML_Clock              = NVML_Enum("NVML_Clock", prefix="NVML_CLOCK_")
NVML_PowerSource        = NVML_Enum("NVML_PowerSource", prefix="NVML_POWER_SOURCE_")
NVML_Arch               = NVML_Enum("NVML_Arch", prefix="NVML_DEVICE_ARCH_")
NVML_TempThreshold      = NVML_Enum("NVML_TempThreshold", prefix="NVML_TEMPERATURE_THRESHOLD_")
NVML_API_Restriction    = NVML_Enum("NVML_API_Restriction", prefix="NVML_RESTRICTED_API_SET_")
NVML_Enable_State       = NVML_Enum("NVML_Enable_State", prefix="NVML_FEATURE_")
NVML_Compute_Mode       = NVML_Enum("NVML_Compute_Mode", prefix="NVML_COMPUTEMODE_")
NVML_GPU_Operation_Mode = NVML_Enum("NVML_GPU_Operation_Mode", prefix="NVML_GOM_")

class NVML_IDs(enum.Enum):
    NVML_ID_INDEX   = 0
    NVML_ID_SERIAL  = 1
    NVML_ID_UUID    = 2

NVML_CONFIG_PARAMETERS = {
    "APIRestriction":                   (NVML_API_Restriction, NVML_Enable_State),
    "ApplicationsClocks":               (int, int),
    "ComputeMode":                      (NVML_Compute_Mode,),
    "ConfComputeUnprotectedMemSize":    (int,),
    "EccMode":                          (NVML_Enable_State,),
    "FanSpeed_v2":                      (int, int),
    "GpcClkVfOffset":                   (int,),
    "GpuLockedClocks":                  (int, int),
    "GpuOperationMode":                 (NVML_GPU_Operation_Mode,),
    "MemClkVfOffset":                   (int,),
    "MemoryLockedClocks":               (int, int),
    "PersistenceMode":                  (NVML_Enable_State,),
    "PowerManagementLimit":             (int,)
}

class NvidiaML(DeviceSource):
    parameters = ParameterDict(NVML_CONFIG_PARAMETERS)
    source_name = "Nvidia Management Library"
    supported_platforms = ["Linux", "Windows"]

    def __init__(self,
                 sample_frequency: int      = 5000,
                 out_file: Path             = "nvml_out.json",
                 queries: list[NVML_Query]  = [NVML_Dynamic_Query.NVML_UTILIZATION_RATES,
                                               NVML_Dynamic_Query.NVML_POWER_USAGE],
                 fields: list[NVML_Field]   = [],
                 samples: list[NVML_Sample] = [],
                 settings: dict[str, tuple] = {}):
        super().__init__()
        
        # Initialize an instance of the library
        nvml.nvmlInit()

        self.device_config = None
        self.sample_frequency = sample_frequency
        self.logfile = out_file
        self.settings = settings
        self.handle_method = []

        # Threads require their own handle
        self.thread_handle = None
        self.main_handle  = None

        # Configure which measurements will be made by nvml
        self.measurements = {
            "queries": queries, 
            "fields": fields,
            "samples": samples
        }

        # This records the latest timestamp per sample type
        self.latest_timestamp = {sample.name: 0 for sample in NVML_Sample}
    
    @property
    def device_handle(self):
        if threading.current_thread().name == "DeviceWorker":
            return self.main_handle
        else:
            return self.thread_handle

    @device_handle.setter
    def device_handle(self, value):
        if threading.current_thread().name == "DeviceWorker":
            self.main_handle = value
        else:
            self.thread_handle = value

    def _print_stat(self, stat, value, unit=None):
        if unit is not None:
            print(f"{(stat+" ("+unit+")").ljust(40)}: {value}")
        else:
            print(f"{(stat).ljust(40)}: {value}")

    def _parse_value(self, value_type, nvml_value):
        match value_type:
            case nvml.NVML_VALUE_TYPE_UNSIGNED_LONG:
                return nvml_value.ulVal
            case nvml.NVML_VALUE_TYPE_UNSIGNED_LONG_LONG:
                return nvml_value.ullVal 
            case nvml.NVML_VALUE_TYPE_SIGNED_LONG_LONG:
                return nvml_value.sllVal
            case nvml.NVML_VALUE_TYPE_SIGNED_INT:
                return nvml_value.siVal
            case nvml.NVML_VALUE_TYPE_UNSIGNED_INT:
                return nvml_value.uiVal 
            case nvml.NVML_VALUE_TYPE_DOUBLE:
                return nvml_value.dVal
            case _:
                return None
    
    def _query_samples(self, handle, sample_type: NVML_Sample, latest_time: int):
        try:
            sample_type, samples = nvml.nvmlDeviceGetSamples(handle, sample_type, latest_time)
        except nvml.NVMLError as e:
            return e
            
        return [(sample.timeStamp, self._parse_value(sample_type, sample.sampleValue)) \
                for sample in samples]
        
    def _query_fields(self, handle, field_ids: list[NVML_Field]):
        ret = {}
        if len(field_ids) == 0:
            return ret
        
        # Convery enums to values
        field_ids = list(map(lambda x: x.value, field_ids));
        try:
            # Clear the values first, so we know they are fresh
            nvml.nvmlDeviceClearFieldValues(handle, field_ids)
            values = nvml.nvmlDeviceGetFieldValues(handle, field_ids)
        except nvml.NVMLError as e:
            raise RuntimeError(f"NVML Error querying field values {field_ids}: {e}")
        
        # Check the provided return codes
        for f_value in values:
            if f_value.nvmlReturn != nvml.NVML_SUCCESS:
                ret[NVML_Field(f_value.fieldId).name] = nvml.NVMLError(f_value.nvmlReturn)
            else:
                ret[NVML_Field(f_value.fieldId).name] = self._parse_field_value(f_value)

        return ret

    def _query_device(self, handle, query_type: NVML_Query | list[NVML_Field]):
        ret = None
        
        func = getattr(nvml, f"nvmlDeviceGet{query_type.value}")
        
        # When given a list of feild values
        if type(query_type) == list:
            return self._query_fields(query_type)

        try:
            match query_type.value:
                case "UtilizationRates":
                    util = func(handle)
                    ret = {f[0]: getattr(util, f[0]) for f in util._fields_} 
                case "Temperature":
                    # Theres only one temperature sensor listed in the enum
                    ret = func(handle, nvml.NVML_TEMPERATURE_GPU)
                case "FanSpeed_v2":
                    ret = {}
                    for fan in range(nvml.nvmlDeviceGetNumFans(handle)):
                        ret[fan] = func(handle, fan)
                case "GetClockInfo":
                    ret = {}
                    for clk_type in NVML_Clock:
                        ret[clk_type.name] = func(handle, clk_type.value)
                case "TemperatureThreshold":
                    ret = self._query_fields(handle, [NVML_Field.NVML_FI_DEV_TEMPERATURE_MEM_MAX_TLIMIT,
                                                      NVML_Field.NVML_FI_DEV_TEMPERATURE_GPU_MAX_TLIMIT,
                                                      NVML_Field.NVML_FI_DEV_TEMPERATURE_SLOWDOWN_TLIMIT,
                                                      NVML_Field.NVML_FI_DEV_TEMPERATURE_SHUTDOWN_TLIMIT])

                    # The new method has failed, revert to depricated features
                    if any(map(lambda x: isinstance(x, nvml.NVMLError), ret.values())):
                        ret = {}
                        for temp_type in NVML_TempThreshold:
                            try:
                                ret[temp_type.name] = func(handle, temp_type.value)
                            except:
                                pass
                case "Architecture":
                    ret = NVML_Arch(func(handle)).name
                case "MinMaxClockOfPState":
                    ret = {}
                    for p_state in nvml.nvmlDeviceGetSupportedPerformanceStates(handle):
                        ret[p_state] = {}
                        for clk_type in NVML_Clock:
                            ret[p_state][clk_type.name] = func(handle, pstate=p_state, clockType=clk_type.value)
                case "TargetFanSpeed":
                    ret = {}
                    for i in range(0, nvml.nvmlDeviceGetNumFans(handle)):
                        ret[i] = func(handle, i)
                case "PowerSource":
                    ret = NVML_PowerSource(func(handle)).name
                case "MaxClockInfo" | "MaxCustomerBoostClock":
                    ret = {}
                    for clk_type in NVML_Clock:
                        ret[clk_type.name] = func(handle, clk_type.value)
                case _:
                    ret = func(handle)

        except nvml.NVMLError as e:
            return e

        return ret

    def set_mode(self, settings: dict[str, tuple]):
        if not self.is_admin():
            raise RuntimeError("Admin permissions are required to change GPU configuration")

        if not self.device_handle:
            raise RuntimeError("A device must be selected before it can be configured")

        for setting, args in settings.items():
            if setting not in self.parameters:
                raise RuntimeError(f"Setting {setting} not supported")

            if tuple(map(type, args)) != self.parameters[setting]:
                raise RuntimeError(f"Arguments {args} not valid for setting {setting}")
            
            # Convert enums to values
            args = tuple(map(lambda x: x.value if isinstance(x, enum.Enum) else x, args))
            func = getattr(nvml, f"nvmlDeviceSet{setting}")
            ret = None
            
            try:
                ret = func(self.device_handle, *args)
            except nvml.NVMLError as e:
                print(f"[WARNING] Failed to set {setting}: {e}")

        return ret

    # Very important function, this sets what stats are measured when log is called
    def set_measurements(self, samples: list[NVML_Sample] = [],
                               fields:  list[NVML_Field] = [], 
                               queries: list[NVML_Query] = []):
        
        # Set new measurements if present
        if len(samples) > 0:
            self.measurements["samples"] = samples
        if len(fields) > 0:
            self.measurements["fields"] = fields
        if len(queries) > 0:
            self.measurements["queries"] = queries

    # NVML supports 3 main different ways of acquiring stats:
    # Sampling, Field Values, and deviceGet queries
    # We support all of them, but it does require knowing 
    # which sources you need, and which are supported by the device
    def measure(self):
        results = {}

        for sample in self.measurements["samples"]:
            timestamp = int(time.time_ns() // 1000)
            results[sample.name] = self._query_samples(self.device_handle, sample.value, self.latest_timestamp[sample.name])

            # Only remember valid timestamps
            if  not isinstance(results[sample.name], nvml.NVMLError) \
                and results[sample.name] != []:
                self.latest_timestamp[sample.name] = max(list(map(lambda x: x[0], results[sample.name])))

            # Wrap errors with a timestamp
            if isinstance(results[sample.name], nvml.NVMLError):
                results[sample.name] = (timestamp, results[sample.name])
        
        fields = self.measurements["fields"]
        timestamp = int(time.time_ns() // 1000)
        results |= { key: (timestamp, value)
                     for key, value in self._query_fields(self.device_handle, fields).items()}

        for query in self.measurements["queries"]:
            timestamp = int(time.time_ns() // 1000)
            results[query.name] = (timestamp, self._query_device(self.device_handle, query))
            
        return results

    def list_devices(self, print_dev=False):
        devices = []
        for dev_idx in range(0, nvml.nvmlDeviceGetCount()):
            handle = nvml.nvmlDeviceGetHandleByIndex(dev_idx)
            devices.append({})
            
            for stat in list(NVML_Static_Query): 
                if "fan" in stat.value.lower() and devices[dev_idx].get("NumFans") == 0:
                    continue

                devices[dev_idx][stat.value] = self._query_device(handle, stat)
        
        if not print_dev:
            return devices

        for i, stats in enumerate(devices):
            print(f"Device {dev_idx}:")

            for stat, value in stats.items():
                if value is None or isinstance(value, nvml.NVMLError):
                    continue

                match stat:
                    case stat if "temperature" in stat.lower():
                        self._print_stat(stat, value, "C")
                    case stat if "power" in stat.lower() and "source" not in stat.lower():
                        self._print_stat(stat, value, "mW")
                    case stat if "clock" in stat.lower():
                        self._print_stat(stat, value, "MHz")
                    case "MemoryInfo":
                        self._print_stat(stat, value.total, "total bytes")
                    case _:
                        self._print_stat(stat, value)
        
        return devices

    def open_device(self, dev_id: str | int, id_type: NVML_IDs):
        # A bit more descriptive than the nvidia errors
        if id_type == NVML_IDs.NVML_ID_INDEX and \
            int(dev_id) >= nvml.nvmlDeviceGetCount():
            raise RuntimeError(f"GPU device index ({int(dev_id)}) larger than the number of devices {nvml.nvmlDeviceGetCount()}")
        
        try:
            match id_type:
                case NVML_IDs.NVML_ID_SERIAL:
                    self.device_handle = nvml.nvmlDeviceGetHandleBySerial(str(dev_id))
                case NVML_IDs.NVML_ID_UUID:
                    self.device_handle = nvml.nvmlDeviceGetHandleByUUID(str(dev_id))
                case NVML_IDs.NVML_ID_INDEX:
                    self.device_handle = nvml.nvmlDeviceGetHandleByIndex(int(dev_id))
        except nvml.NVMLError as e:
            raise RuntimeError(f"Could not get device with {str(id_type)} {dev_id}: {e}")
        
        # Set any initial settings
        if len(self.settings) > 0:
            self.set_mode(self.settings)
        
        # Maintain some state
        self.handle_method = [dev_id, id_type]
        self.device_config = {query: self._query_device(self.device_handle, query) \
                              for query in NVML_Static_Query}

    def close_device(self):
        nvml.nvmlShutdown()
        self.device_config = None
        self.device_handle = None

    def log(self):
        # NVML Needs to be set up in each participating thread
        nvml.nvmlInit()
        self.open_device(*self.handle_method)
        
        # Perform some basic checks and initialization
        super().log()
        
        if  len(self.measurements["queries"]) == 0      \
            and len(self.measurements["fields"]) == 0   \
            and len(self.measurements["samples"]) == 0:
            raise RuntimeError("[ERROR] No measurements are are set to be collected, please call set_measurements()")
        
        log_data = {data_type.name: [] 
                    for measure in self.measurements.values() 
                    for data_type in measure}
        
        while not self.stop_thread.is_set():
            for res_type, value in self.measure().items():
                # Combine all results into the log
                if isinstance(value, list):
                    log_data[res_type].extend(value)
                else:
                    log_data[res_type].append(value)

            # Ensure measurement frequency
            time.sleep(self.sample_frequency/1000)
        
        # Convert errors to strings
        for category, values in log_data.items():
            log_data[category] = list(map(lambda x: (x[0], str(x[1])) if isinstance(x[1], nvml.NVMLError) else x, values))
        
        if self.logfile:
            with open(self.logfile, "w") as f:
                json.dump(log_data, f)
        
        # Clean up state and return values
        self.thread_queue.put(log_data)
        self.thread_queue.join()
        self.thread_handle = None
        nvml.nvmlShutdown()
        return 0

    @staticmethod
    def parse_log(logfile, remove_errors=False):
        with open(logfile, "r") as f:
            log_data = json.load(f)
        
        # Convery sub arrays back to tuples
        for category, values in log_data.items():
            log_data[category] = list(map(lambda x: (x[0], x[1]), values))

            if not remove_errors:
                continue
            
            error_strings = list(nvml.NVMLError._errcode_to_string.values())
            log_data[category] = list(filter(lambda x: x[1] not in error_strings, log_data[category]))

        return log_data

