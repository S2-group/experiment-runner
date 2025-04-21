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

# Query all dynamic stats via these generic methods? 
# nvmlReturn_t nvmlDeviceGetSamples ( nvmlDevice_t device, nvmlSamplingType_t type, unsigned long long lastSeenTimeStamp, nvmlValueType_t* sampleValType, unsigned int* sampleCount, nvmlSample_t* samples )
# nvmlReturn_t nvmlDeviceClearFieldValues ( nvmlDevice_t device, int  valuesCount, nvmlFieldValue_t* values )
# nvmlReturn_t nvmlDeviceGetFieldValues ( nvmlDevice_t device, int  valuesCount, nvmlFieldValue_t* values ) 
#
# # Power related stats
# nvmlReturn_t nvmlDeviceGetPowerManagementDefaultLimit ( nvmlDevice_t device, unsigned int* defaultLimit )
# nvmlReturn_t nvmlDeviceGetPowerManagementLimit ( nvmlDevice_t device, unsigned int* limit )
# nvmlReturn_t nvmlDeviceGetPowerManagementLimitConstraints ( nvmlDevice_t device, unsigned int* minLimit, unsigned int* maxLimit )
# nvmlReturn_t nvmlDeviceGetPowerManagementMode ( nvmlDevice_t device, nvmlEnableState_t* mode )
# nvmlReturn_t nvmlDeviceGetPowerSource ( nvmlDevice_t device, nvmlPowerSource_t* powerSource )
# nvmlReturn_t nvmlDeviceGetPowerState ( nvmlDevice_t device, nvmlPstates_t* pState )
# nvmlReturn_t nvmlDeviceGetPowerUsage ( nvmlDevice_t device, unsigned int* power )
# nvmlReturn_t nvmlDeviceGetTotalEnergyConsumption ( nvmlDevice_t device, unsigned long long* energy )
# # Thermal Related settings
# nvmlReturn_t nvmlDeviceGetTemperature ( nvmlDevice_t device, nvmlTemperatureSensors_t sensorType, unsigned int* temp )
# nvmlReturn_t nvmlDeviceGetTemperatureThreshold ( nvmlDevice_t device, nvmlTemperatureThresholds_t thresholdType, unsigned int* temp )
# nvmlReturn_t nvmlDeviceGetThermalSettings ( nvmlDevice_t device, unsigned int  sensorIndex, nvmlGpuThermalSettings_t* pThermalSettings )
# # Other random useful stuff
# nvmlReturn_t nvmlDeviceGetFanSpeed_v2 ( nvmlDevice_t device, unsigned int  fan, unsigned int* speed )
# nvmlReturn_t nvmlDeviceGetMinMaxClockOfPState ( nvmlDevice_t device, nvmlClockType_t type, nvmlPstates_t pstate, unsigned int* minClockMHz, unsigned int* maxClockMHz )
# nvmlReturn_t nvmlDeviceGetClockInfo ( nvmlDevice_t device, nvmlClockType_t type, unsigned int* clock )
# nvmlReturn_t nvmlDeviceGetUtilizationRates ( nvmlDevice_t device, nvmlUtilization_t* utilization )
# nvmlReturn_t nvmlDeviceGetPerformanceState ( nvmlDevice_t device, nvmlPstates_t* pState )
# nvmlReturn_t nvmlDeviceGetMaxClockInfo ( nvmlDevice_t device, nvmlClockType_t type, unsigned int* clock )
# nvmlReturn_t nvmlDeviceGetAttributes_v2 ( nvmlDevice_t device, nvmlDeviceAttributes_t* attributes )
# nvmlReturn_t nvmlDeviceGetClock ( nvmlDevice_t device, nvmlClockType_t clockType, nvmlClockId_t clockId, unsigned int* clockMHz )
# nvmlReturn_t nvmlDeviceGetFanSpeed ( nvmlDevice_t device, unsigned int* speed )
# # Supported states
# nvmlReturn_t nvmlDeviceGetSupportedGraphicsClocks ( nvmlDevice_t device, unsigned int  memoryClockMHz, unsigned int* count, unsigned int* clocksMHz )
# nvmlReturn_t nvmlDeviceGetSupportedMemoryClocks ( nvmlDevice_t device, unsigned int* count, unsigned int* clocksMHz )
# nvmlReturn_t nvmlDeviceGetSupportedPerformanceStates ( nvmlDevice_t device, nvmlPstates_t* pstates, unsigned int  size )
#
#
class NvidiaML(DeviceSource):
    source_name = "Nvidia Management Library"
    supported_platforms = ["Linux", "Windows"]
    
    config_stats = ["ComputeMode",
                    "UUID",
                    "Index",
                    "Brand",
                    "BusType",
                    "Architecture",
                    "BoardId",
                    "BoardPartNumber",
                    "MinMaxFanSpeed",
                    "Name",
                    "NumFans",
                    "NumGpuCores",
                    "Serial",
                    "VbiosVersion",
                    "PersistenceMode",
                    "EnforcedPowerLimit",
                    "MemoryInfo"]
                    #"MaxClockInfo",
                    #"MaxCustomerBoostClock",
                    #"TargetFanSpeed"]
    
    def __init__(self):
        super().__init__()
        nvml.nvmlInit()
    
    def query_device(self, handle, query_type, *args, **kwargs):
        ret = None
        
        func = getattr(nvml, f"nvmlDeviceGet{query_type}")

        try:
            ret = func(handle)
        except nvml.NVMLError as e:
            print(f"[WARNING] Stat type {query_type}: {e}")
            # maybe a warning here about which stats are supported
            pass
        
        return ret

    def list_devices(self):
        devices = []
        for dev_idx in range(0, nvml.nvmlDeviceGetCount()):
            handle = nvml.nvmlDeviceGetHandleByIndex(dev_idx)
            devices.append({})

            for stat in self.config_stats:
                devices[dev_idx][stat] = self.query_device(handle, stat)

                # Some stats require a bit of special handling
                match stat:
                    case "MemoryInfo":
                        pass
                    case "MaxClockInfo":
                        pass
                    case "MaxCustomerBoostClock":
                        pass
                    case "TargetFanSpeed":
                        pass
        
        print(devices)
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

    def close_device(self):
        nvml.nvmlShutdown()
    
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
    source.list_devices()

if __name__ == "__main__":
    main()
