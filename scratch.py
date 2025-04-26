import enum
import sys
from pathlib import Path
import pynvml as nvml
import time
import inspect

from collections.abc import Callable

sys.path.insert(0, "./experiment-runner/Plugins/Profilers/")
from DataSource import CLISource, ParameterDict, DeviceSource

nvml_clock_strings = {
    nvml.NVML_CLOCK_GRAPHICS:   "GraphicsClock",
    nvml.NVML_CLOCK_SM:         "StramingMultiproessorClock",
    nvml.NVML_CLOCK_MEM:        "MemoryClock",
    nvml.NVML_CLOCK_VIDEO:      "VideoClock",
}

nvml_powersource_strings = {
    nvml.NVML_POWER_SOURCE_AC:          "AC",
    nvml.NVML_POWER_SOURCE_BATTERY:     "Battery",
    nvml.NVML_POWER_SOURCE_UNDERSIZED:  "Undersized",
}

nvml_arch_strings = {
    nvml.NVML_DEVICE_ARCH_KEPLER:   "Kepler",
    nvml.NVML_DEVICE_ARCH_MAXWELL:  "Maxwell",
    nvml.NVML_DEVICE_ARCH_PASCAL:   "Pascal",
    nvml.NVML_DEVICE_ARCH_VOLTA:    "Volta",
    nvml.NVML_DEVICE_ARCH_TURING:   "Turing",
    nvml.NVML_DEVICE_ARCH_AMPERE:   "Ampere",
    nvml.NVML_DEVICE_ARCH_ADA:      "Ada",
    nvml.NVML_DEVICE_ARCH_HOPPER:   "Hopper",
    nvml.NVML_DEVICE_ARCH_BLACKWELL:"Blackwell",
    nvml.NVML_DEVICE_ARCH_T23X:     "Orin",
    nvml.NVML_DEVICE_ARCH_UNKNOWN:  "Unknown"
}

# Need these for legacy temperature support
nvml_tempthr_strings = {
    nvml.NVML_TEMPERATURE_THRESHOLD_SHUTDOWN:       "Shutdown Temp",
    nvml.NVML_TEMPERATURE_THRESHOLD_SLOWDOWN:       "Slowdown Temp",
    nvml.NVML_TEMPERATURE_THRESHOLD_GPU_MAX:        "GPU Max Temp",
    nvml.NVML_TEMPERATURE_THRESHOLD_MEM_MAX:        "Memory Max Temp",
    nvml.NVML_TEMPERATURE_THRESHOLD_ACOUSTIC_MIN:   "Acoustic Min Temp",
    nvml.NVML_TEMPERATURE_THRESHOLD_ACOUSTIC_CURR:  "Acoustic Current Temp",
    nvml.NVML_TEMPERATURE_THRESHOLD_ACOUSTIC_MAX:   "Acoustic Max Temp",
}

class NVML_ID_Types(enum.Enum):
    NVML_ID_INDEX   = 0
    NVML_ID_SERIAL  = 1
    NVML_ID_UUID    = 2

class NVML_Query_Types(enum.Enum):
    NVML_POWER_USAGE    = "PowerUsage"
    NVML_TOTAL_ENERGY   = "TotalEnergyConsumption"
    NVML_TEMPERATURE    = "Temperature"
    NVML_FAN_SPEED      = "GetFanSpeed_v2"
    NVML_UTILIZATION    = "UtilizationRates"
    NVML_PSTATE         = "PerformanceState"
    NVML_CLOCK          = "GetClockInfo"

class NVML_Sample_Types(enum.Enum):
    NVML_TOTAL_POWER     = nvml.NVML_TOTAL_POWER_SAMPLES
    NVML_GPU_UTILIZATION = nvml.NVML_GPU_UTILIZATION_SAMPLES
    NVML_MEM_UTILIZATION = nvml.NVML_MEMORY_UTILIZATION_SAMPLES
    NVML_ENC_UTILIZATION = nvml.NVML_ENC_UTILIZATION_SAMPLES
    NVML_DEC_UTILIZATION = nvml.NVML_DEC_UTILIZATION_SAMPLES
    NVML_PROCESSOR_CLK   = nvml.NVML_PROCESSOR_CLK_SAMPLES
    NVML_MEMORY_CLK      = nvml.NVML_MEMORY_CLK_SAMPLES
    NVML_MODULE_POWER    = nvml.NVML_MODULE_POWER_SAMPLES

# There are a lot of these, extract then automatically
NVML_Field_Types = enum.Enum("NVML_Field_Types",
                            {
                                name: val 
                                for name, val in inspect.getmembers(nvml) 
                                if name.startswith("NVML_FI_")
                            })

# These are the setting functions
dev_commands = ["APIRestriction",
                "ApplicationsClocks",
                "ComputeMode",
                "ConfComputeUnprotectedMemSize",
                "EccMode",
                "FanSpeed",
                "GpcClkVfOffset",
                "GpuLockedClocks",
                "GpuOperationMode",
                "MemClkVfOffset",
                "MemoryLockedClocks",
                "PersistenceMode",
                "PowerManagementLimit"]

class NVML_Dev_Config_Types(enum.Enum):
    pass    

class NvidiaML(DeviceSource):
    source_name = "Nvidia Management Library"
    supported_platforms = ["Linux", "Windows"]

    # These are the static query functions
    config_stats = ["Name",
                    "UUID",
                    "Serial",
                    "Index",
                    "Architecture", 
                    "NumGpuCores",
                    "VbiosVersion",
                    "Brand",
                    "NumFans",
                    "MemoryInfo",
                    "BusType",
                    "BoardId",
                    "Attributes",
                    "BoardPartNumber",
                    "MinMaxFanSpeed",
                    "ComputeMode",
                    "PersistenceMode",
                    "PowerManagementMode",
                    "EnforcedPowerLimit",
                    "PowerManagementLimit",
                    "PowerManagementDefaultLimit",
                    "PowerManagementLimitConstraints",
                    "MaxCustomerBoostClock",
                    "PowerSource",
                    "TargetFanSpeed",
                    "TemperatureThreshold",
                    "SupportedPerformanceStates",
                    "MaxClockInfo",
                    "MinMaxClockOfPState"]
    
    def __init__(self,
                 sample_frequency: int  = 5000,
                 out_file: Path         = "nvml_out.csv"):
        super().__init__()
        
        # Initialize an instance of the library
        nvml.nvmlInit()

        self.device_config = None
        self.sample_frequency = sample_frequency
        self.logfile = out_file
        
        # Configure a few default stats to collect
        self.measurements = {
            "queries": [NVML_Query_Types.NVML_UTILIZATION, 
                        NVML_Query_Types.NVML_PSTATE, 
                        NVML_Query_Types.NVML_TEMPERATURE,
                        NVML_Query_Types.NVML_POWER_USAGE], 
            "fields": [NVML_Field_Types. NVML_FI_DEV_ENERGY,
                       NVML_Field_Types.NVML_FI_DEV_MEMORY_TEMP],
            "samples": [NVML_Sample_Types.NVML_PROCESSOR_CLK,
                        NVML_Sample_Types.NVML_MEMORY_CLK,
                        NVML_Sample_Types.NVML_MODULE_POWER]
        }

        # This records the latest timestamp per sample type
        self.latest_timestamp = {}

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
    
    def _query_samples(self, handle, sample_type, latest_time):
        ret = None
        try:
            sample_type, samples = nvml.nvmlDeviceGetSamples(handle, sample_type, latest_time)
        except nvml.NVMLError as e:
            print(f"[WARNING] Sampling failed for {NVML_Sample_Types(sample_type).name}: {e}")
            return None
            
        ret = {}
        for sample in samples:
            ret[sample.timeStamp] = self._parse_value(sample_type, sample.sampleValue)

        return ret
        
    def _query_fields(self, handle, field_ids=[]):
        values = None

        try:
            # Clear the values first, so we know they are fresh
            nvml.nvmlDeviceClearFieldValues(handle, field_ids)
            values = nvml.nvmlDeviceGetFieldValues(handle, field_ids)
        except nvml.NVMLError as e:
            raise RuntimeError(f"NVML Error querying field values {field_ids}: {e}")
        
        # Check the provided return codes
        ret = {}
        for f_value in values:
            if f_value.nvmlReturn != nvml.NVML_SUCCESS:
                #print(f"[WARNING] Error querying field value {NVML_Field_Types(f_value.fieldId).name}: {nvml.NVMLError(f_value.nvmlReturn)}")
                ret[NVML_Field_Types(f_value.field).name] = None
            else:
                ret[NVML_Field_Types(f_value.field).name] = self._parse_field_value(f_value)

        return ret

    def _query_device(self, handle, query_type):
        ret = None
        
        func = getattr(nvml, f"nvmlDeviceGet{query_type}")
        
        # When given a list of feild values
        if type(query_type) == list:
            return self._query_fields(query_type)

        try:
            match query_type:
                case "GetTemperature":
                    # Theres only one temperature sensor listed in the enum
                    ret = func(handle, nvml.NVML_TEMPERATURE_GPU)
                case "FanSpeed_v2":
                    ret = {}
                    for fan in range(self.device_config["NumFans"]):
                        ret[fan] = func(handle, fan)
                case "GetClockInfo":
                    ret = {}
                    for val, string in nvml_clock_strings.items():
                        ret[string] = func(handle, val)
                case "TemperatureThreshold":
                    ret = self._query_fields(handle, [nvml.NVML_FI_DEV_TEMPERATURE_MEM_MAX_TLIMIT,
                                                      nvml.NVML_FI_DEV_TEMPERATURE_GPU_MAX_TLIMIT,
                                                      nvml.NVML_FI_DEV_TEMPERATURE_SLOWDOWN_TLIMIT,
                                                      nvml.NVML_FI_DEV_TEMPERATURE_SHUTDOWN_TLIMIT])
                    
                    # The new method has failed, revert to depricated features
                    if ret == {}:
                        for val, string in nvml_tempthr_strings.items():
                            try:
                                ret[string] = func(handle, val)
                            except:
                                pass
                case "Architecture":
                    ret = nvml_arch_strings[func(handle)]
                case "MinMaxClockOfPState":
                    ret = {}
                    for p_state in self.device_config["SupportedPerformanceStates"]:
                        ret[p_state] = {}
                        for val, string in nvml_clock_strings.items():
                            ret[p_state][string] = func(handle, pstate=p_state, clockType=val)
                case "TargetFanSpeed":
                    ret = {}
                    for i in range(0, nvml.nvmlDeviceGetNumFans(handle)):
                        ret[i] = func(handle, i)
                case "PowerSource":
                    ret = nvml_powersource_strings[func(handle)]
                case "MaxClockInfo" | "MaxCustomerBoostClock":
                    ret = {}
                    for val, string in nvml_clock_strings.items():
                        ret[string] = func(handle, val)
                case _:
                    ret = func(handle)

        except nvml.NVMLError as e:
            print(f"[WARNING] Query type {query_type} failed: {e}")
            return None

        return ret

    # Very important function, this sets what stats are measured when log is called
    def set_measurements(self, samples: list[NVML_Sample_Types] = [],
                               fields:  list[NVML_Field_Types] = [], 
                               queries: list[NVML_Query_Types] = []):
        
        self.measurements = {
            "samples":  samples,
            "fields": fields,
            "queries": queries
        }

    # NVML supports 3 main different ways of acquiring stats:
    # Sampling, Field Values, and deviceGet queries
    # We support all of them, but it does require knowing 
    # which sources you need, and which are supported by the device
    def measure(self):
        samples = self.measurements["samples"]
        fields = self.measurements["fields"]
        queries = self.measurements["queries"]

        results = {}
        for sample in samples:
            results[sample.name] = self._query_samples(self.device_handle, sample.value, self.latest_timestamp[sample])
            self.latest_timestamp[sample] = None


        results |= self._query_fields(self.device_handle, list(map(lambda x: x.value, fields)))

        for query in queries:
            results[query.name] = self._query_device(self.device_handle, query.value)
        
        return results

    def list_devices(self, print_dev=False):
        devices = []
        for dev_idx in range(0, nvml.nvmlDeviceGetCount()):
            handle = nvml.nvmlDeviceGetHandleByIndex(dev_idx)
            devices.append({})
            
            for stat in self.config_stats:
                if "fan" in stat.lower() and devices[dev_idx].get("NumFans") == 0:
                    continue

                devices[dev_idx][stat] = self._query_device(handle, stat)
        
        if not print_dev:
            return devices

        for i, stats in enumerate(devices):
            print(f"Device {dev_idx}:")

            for stat, value in stats.items():
                if value is None:
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

    def open_device(self, dev_id, id_type: NVML_ID_Types):
        # A bit more descriptive than the nvidia errors
        if id_type == NVML_ID_Types.NVML_ID_INDEX and \
            int(dev_id) >= nvml.nvmlDeviceGetCount():
            raise RuntimeError(f"GPU device index ({int(dev_id)}) larger than the number of devices {nvml.nvmlDeviceGetCount()}")
        
        try:
            match id_type:
                case NVML_ID_Types.NVML_ID_SERIAL:
                    self.device_handle = nvml.nvmlDeviceGetHandleBySerial(str(dev_id))
                case NVML_ID_Types.NVML_ID_UUID:
                    self.device_handle = nvml.nvmlDeviceGetHandleByUUID(str(dev_id))
                case NVML_ID_Types.NVML_ID_INDEX:
                    self.device_handle = nvml.nvmlDeviceGetHandleByIndex(int(dev_id))
        except nvml.NVMLError as e:
            raise RuntimeError(f"Could not get device with {str(id_type)} {dev_id}: {e}")
        
        self.device_config = {query: self._query_device(self.device_handle, query) \
                              for query in self.config_stats}

    def close_device(self):
        nvml.nvmlShutdown()
        self.device_config = None
    
    def set_mode(self, settings={}):
        if not self.is_admin():
            raise RuntimeError("Admin permissions are required to change GPU configuration")

        if not self.device_handle:
            raise RuntimeError("A device must be selected before it can be configured")

        # TODO: Check and set some number of settings
    
    def log(self, timeout: int = 60, logfile: Path = None, finished_fn: Callable[[], bool] = None):
        if not self.device_handle:
            raise RuntimeError("A device must be selected before it can be queried")
        
        if  len(self.measurements["queries"]) == 0      \
            and len(self.measurements["fields"]) == 0   \
            and len(self.measurements["samples"]) == 0:
            raise RuntimeError("[ERROR] No measurements are are set to be collected, please call set_measurements()")
        
        log_data = {}

        if logfile:
            self.logfile = logfile

        print('Logging...')
        
        timeout_start = time.time()     
        finished_checker = finished_fn if finished_fn != None else lambda: time.time() < timeout_start + timeout
        
        # Ensure the PicoLog always gets closed
        while finished_checker():
            res = self.measure()

            # TODO: Add the results to the big array log_data
            for res, value in res.items():
                log_data[res].append(value)

            # Ensure measurement frequency
            time.sleep(self.sample_frequency/1000)

    def parse_log(self):
        # TODO: Csv read in log
        pass

def main():
    source = NvidiaML()
    source.open_device(dev_id=0, id_type=NVML_ID_Types.NVML_ID_INDEX)
    #source.list_devices(print_dev=True)
    source._query_device(source.device_handle, "PowerUsage")
    #source._query_fields(source.device_handle, [nvml.NVML_FI_DEV_POWER_INSTANT])
    #print(source._query_samples(source.device_handle, nvml.NVML_MODULE_POWER_SAMPLES, 0))

if __name__ == "__main__":
    main()
