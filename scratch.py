import plistlib
import enum
import sys
from pathlib import Path
from pprint import pprint
from collections import UserDict
import pynvml as nvml
import time
import datetime

sys.path.insert(0, "./experiment-runner/Plugins/Profilers/")
from DataSource import CLISource, ParameterDict, DeviceSource

class NVML_Dev_ID_Types(enum.Enum):
    NVML_ID_INDEX   = 0
    NVML_ID_SERIAL  = 1
    NVML_ID_UUID    = 2

class NVML_Dev_Query_Types(enum.Enum):
    pass
class NVML_Dev_Config_Types(enum.Enum):
    pass

# General Unchanging stats
# We want to record:
# - Temp
# - Memory Usage
# - Utilization
# - Power Consuption
# - P state
# - Clock speed
# - Fan Speeds

# Query all dynamic stats via these generic methods? 
# nvmlReturn_t nvmlDeviceGetSamples ( nvmlDevice_t device, nvmlSamplingType_t type, unsigned long long lastSeenTimeStamp, nvmlValueType_t* sampleValType, unsigned int* sampleCount, nvmlSample_t* samples )
# nvmlReturn_t nvmlDeviceClearFieldValues ( nvmlDevice_t device, int  valuesCount, nvmlFieldValue_t* values )
# nvmlReturn_t nvmlDeviceGetFieldValues ( nvmlDevice_t device, int  valuesCount, nvmlFieldValue_t* values ) 

# # Power related stats
# nvmlReturn_t nvmlDeviceGetPowerUsage ( nvmlDevice_t device, unsigned int* power )
# nvmlReturn_t nvmlDeviceGetTotalEnergyConsumption ( nvmlDevice_t device, unsigned long long* energy )

# # Thermal Related settings
# nvmlReturn_t nvmlDeviceGetTemperature ( nvmlDevice_t device, nvmlTemperatureSensors_t sensorType, unsigned int* temp )
# nvmlReturn_t nvmlDeviceGetTemperatureThreshold ( nvmlDevice_t device, nvmlTemperatureThresholds_t thresholdType, unsigned int* temp )

# # Other random useful stuff
# nvmlReturn_t nvmlDeviceGetFanSpeed_v2 ( nvmlDevice_t device, unsigned int  fan, unsigned int* speed )
# nvmlReturn_t nvmlDeviceGetFanSpeed ( nvmlDevice_t device, unsigned int* speed )
# nvmlReturn_t nvmlDeviceGetUtilizationRates ( nvmlDevice_t device, nvmlUtilization_t* utilization )
# nvmlReturn_t nvmlDeviceGetPerformanceState ( nvmlDevice_t device, nvmlPstates_t* pState )
# nvmlReturn_t nvmlDeviceGetClock ( nvmlDevice_t device, nvmlClockType_t clockType, nvmlClockId_t clockId, unsigned int* clockMHz )

# # Supported states
# nvmlReturn_t nvmlDeviceGetSupportedGraphicsClocks ( nvmlDevice_t device, unsigned int  memoryClockMHz, unsigned int* count, unsigned int* clocksMHz )
# nvmlReturn_t nvmlDeviceGetSupportedMemoryClocks ( nvmlDevice_t device, unsigned int* count, unsigned int* clocksMHz )

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

nvml_fieldvalue_strings = {
    nvml.NVML_FI_DEV_TEMPERATURE_MEM_MAX_TLIMIT:  "Memory Max Temp",
    nvml.NVML_FI_DEV_TEMPERATURE_GPU_MAX_TLIMIT:  "GPU Max Temp",
    nvml.NVML_FI_DEV_TEMPERATURE_SLOWDOWN_TLIMIT: "Slowdown Temp",
    nvml.NVML_FI_DEV_TEMPERATURE_SHUTDOWN_TLIMIT: "Shutdown Temp",
    nvml.NVML_FI_DEV_POWER_AVERAGE:               "Power Average",
    nvml.NVML_FI_DEV_POWER_INSTANT:               "Power Instant"
}

nvml_sample_strings = {
        nvml.NVML_TOTAL_POWER_SAMPLES:          "Total Power",
        nvml.NVML_GPU_UTILIZATION_SAMPLES:      "GPU Util",
        nvml.NVML_MEMORY_UTILIZATION_SAMPLES:   "Memory Util",
        nvml.NVML_ENC_UTILIZATION_SAMPLES:      "Enc Util",
        nvml.NVML_DEC_UTILIZATION_SAMPLES:      "Dec Util",
        nvml.NVML_PROCESSOR_CLK_SAMPLES:        "Processor Clk",
        nvml.NVML_MEMORY_CLK_SAMPLES:           "Memory Clk",
        nvml.NVML_MODULE_POWER_SAMPLES:         "Module Power",
}

class NvidiaML(DeviceSource):
    source_name = "Nvidia Management Library"
    supported_platforms = ["Linux", "Windows"]
    
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
    
    def __init__(self):
        super().__init__()
        nvml.nvmlInit()
        self.device_config = None
    
    def _parse_field_value(self, field_value):
        match field_value.valueType:
            case nvml.NVML_VALUE_TYPE_UNSIGNED_LONG:
                return field_value.ulVal
            case nvml.NVML_VALUE_TYPE_UNSIGNED_LONG_LONG:
                return field_value.ullVal 
            case nvml.NVML_VALUE_TYPE_SIGNED_LONG_LONG:
                return field_value.sllVal
            case nvml.NVML_VALUE_TYPE_SIGNED_INT:
                return field_value.siVal
            case nvml.NVML_VALUE_TYPE_UNSIGNED_INT:
                return field_value.uiVal 
            case nvml.NVML_VALUE_TYPE_DOUBLE:
                return field_value.dVal
            case _:
                return None
    
    def _query_samples(self, handle, sample_type, latest_time):
        ret = None
        try:
            ret = nvml.nvmlDeviceGetSamples(handle, sample_type, latest_time)
        except nvml.NVMLError as e:
            print(f"[WARNING] Sampling failed for {nvml_sample_strings[sample_type]}: {e}")

        return ret
        
    def _query_fields(self, handle, field_ids=[]):
        values = None

        try:
            # Clear the values first, so we know they are fresh
            nvml.nvmlDeviceClearFieldValues(handle, field_ids)
            values = nvml.nvmlDeviceGetFieldValues(handle, field_ids)
        except nvml.NVMLError as e:
            print(f"[WARNING] Error querying field values {field_ids}: {e}")
            return None
        
        # Check the provided return codes
        ret = {}
        for f_value in values:
            if f_value.nvmlReturn != nvml.NVML_SUCCESS:
                print(f"[WARNING] Error querying field value {nvml_fieldvalue_strings[f_value.fieldId]}: {nvml.NVMLError(f_value.nvmlReturn)}")
                continue

            ret[nvml_fieldvalue_strings[f_value.fieldId]] = self._parse_field_value(f_value)

        return ret

    def query_device(self, handle, query_type):
        ret = None
        
        func = getattr(nvml, f"nvmlDeviceGet{query_type}")
        
        # When given a list of feild values
        if type(query_type) == list:
            return self._query_fields(query_type)

        try:
            match query_type:
                case "TemperatureThreshold":
                    ret = self._query_fields(handle, [nvml.NVML_FI_DEV_TEMPERATURE_MEM_MAX_TLIMIT,
                                                      nvml.NVML_FI_DEV_TEMPERATURE_GPU_MAX_TLIMIT,
                                                      nvml.NVML_FI_DEV_TEMPERATURE_SLOWDOWN_TLIMIT,
                                                      nvml.NVML_FI_DEV_TEMPERATURE_SHUTDOWN_TLIMIT])

                    if ret == {}:
                        # The new method has failed, revert to depricated features
                        for val, string in nvml_tempthr_strings.items():
                            try:
                                ret[string] = func(handle, val)
                            except:
                                pass
                case "Architecture":
                    ret = nvml_arch_strings[func(handle)]
                case "MinMaxClockOfPState":
                    ret = {}
                    for p_state in nvml.nvmlDeviceGetSupportedPerformanceStates(handle):
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

    # NVML supports 3 main different ways of acquiring stats:
    # Sampling, Field Values, and deviceGet queries
    # We support all of them, but it does require knowing which sources you need
    def _measure(self):
        pass
    
    def _print_stat(self, stat, value, unit=None):
        if unit is not None:
            print(f"{(stat+" ("+unit+")").ljust(40)}: {value}")
        else:
            print(f"{(stat).ljust(40)}: {value}")

    def list_devices(self, print_dev=False):
        devices = []
        for dev_idx in range(0, nvml.nvmlDeviceGetCount()):
            handle = nvml.nvmlDeviceGetHandleByIndex(dev_idx)
            devices.append({})
            
            for stat in self.config_stats:
                if "fan" in stat.lower() and devices[dev_idx].get("NumFans") == 0:
                    continue

                devices[dev_idx][stat] = self.query_device(handle, stat)
        
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

    def open_device(self, dev_id, id_type: NVML_Dev_ID_Types):
        # A bit more descriptive than the nvidia errors
        if id_type == NVML_Dev_ID_Types.NVML_ID_INDEX and \
            int(dev_id) >= nvml.nvmlDeviceGetCount():

            raise RuntimeError(f"GPU device index ({int(dev_id)}) larger than the number of devices {nvml.nvmlDeviceGetCount()}")
        
        try:
            match id_type:
                case NVML_Dev_ID_Types.NVML_ID_SERIAL:
                    self.device_handle = nvml.nvmlDeviceGetHandleBySerial(str(dev_id))
                case NVML_Dev_ID_Types.NVML_ID_UUID:
                    self.device_handle = nvml.nvmlDeviceGetHandleByUUID(str(dev_id))
                case NVML_Dev_ID_Types.NVML_ID_INDEX:
                    self.device_handle = nvml.nvmlDeviceGetHandleByIndex(int(dev_id))
        except nvml.NVMLError as e:
            raise RuntimeError(f"Could not get device with {str(id_type)} {dev_id}: {e}")
        
        self.device_config = {query: self.query_device(self.device_handle, query) \
                              for query in self.config_stats}

    def close_device(self):
        nvml.nvmlShutdown()
        self.device_config = None
    
    def set_mode(self):
        if not self.is_admin():
            raise RuntimeError("Admin permissions are required to change GPU configuration")

        if not self.device_handle:
            raise RuntimeError("A device must be selected before it can be queried")

        # Check and set the mode

    def parse_log():
        pass
    
    def start_log(self, timeout: int = 60, logfile: Path = None):
        if not self.device_handle:
            raise RuntimeError("A device must be selected before it can be queried")
        
        print('Logging...')
        if logfile:
            self.logfile = logfile
            o = open(self.logfile,'w')

        line = self.s.readline()
        n = 0
        timeout_start = time.time()
        
        while time.time() < timeout_start + timeout:
            pass

        try:
            o.close()
        except:
            pass

    def stop_log(self):
        pass

def main():
    source = NvidiaML()
    source.open_device(dev_id=0, id_type=NVML_Dev_ID_Types.NVML_ID_INDEX)
    #source.list_devices(print_dev=True)
    #source.query_device(source.device_handle, "TotalEnergyConsumption")
    #source._query_fields(source.device_handle, [nvml.NVML_FI_DEV_POWER_INSTANT])
    print(source._query_samples(source.device_handle, nvml.NVML_GPU_UTILIZATION_SAMPLES, 0))

if __name__ == "__main__":
    main()
