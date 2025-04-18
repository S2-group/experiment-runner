import Plugins.Profilers.picosdk.library as library
from Plugins.Profilers.picosdk.constants import make_enum
from ctypes import c_uint32, c_void_p, c_int16, c_uint16

class Plcm3lib(library.Library):
    def __init__(self):
        super(Plcm3lib, self).__init__("plcm3")

plcm3 = Plcm3lib()

def _plcm3Channels():
    PLCM3_CHANNEL_1 = 1
    PLCM3_CHANNEL_2 = 2
    PLCM3_CHANNEL_3 = 3
    PLCM3_MAX_CHANNELS = PLCM3_CHANNEL_3
    return {k.upper(): v for k, v in locals().items() if k.startswith("PLCM3")}
	
plcm3.PLCM3Channels = _plcm3Channels()

plcm3.PICO_INFO = {
    "PICO_DRIVER_VERSION" : 0,
    "PICO_USB_VERSION" : 1,
    "PICO_HARDWARE_VERSION" : 2,
    "PICO_VARIANT_INFO" : 3,
    "PICO_BATCH_AND_SERIAL" : 4,
    "PICO_CAL_DATE" : 5,
    "PICO_KERNEL_VERSION" : 6,
    "PICO_MAC_ADDRESS" : 11
}

plcm3.PLCM3DataTypes = make_enum([
    'PLCM3_OFF',
    'PLCM3_1_MILLIVOLT',
    'PLCM3_10_MILLIVOLTS',
    'PLCM3_100_MILLIVOLTS',
    'PLCM3_VOLTAGE',
    'PLCM3_MAX_DATA_TYPES'
    ])

plcm3.PLCM3IpDetailsType = make_enum([
    'PLCM3_IDT_GET',
    'PLCM3_IDT_SET',
    ])

def _plcm3CommunicationType():
    PLCM3_CT_USB = 0x00000001
    PLCM3_CT_ETHERNET = 0x00000002
    PLCM3_CT_ALL = 0xFFFFFFFF
    return {k.upper(): v for k, v in locals().items() if k.startswith("PLCM3")}
	
plcm3.PLCM3CommunicationType = _plcm3CommunicationType()

doc = """
    PICO_STATUS PLCM3CloseUnit
    (
        int16_t handle
    );
    This routine disconnects the driver from the device
"""
plcm3.make_symbol("_CloseUnit_", "PLCM3CloseUnit", c_uint32, [c_int16], doc)

doc = """
    PICO_STATUS PLCM3Enumerate
    (
        int8_t * details,
        uint32_t * length,
        PLCM3_COMMUNICATION_TYPE type
    );
    This routine returns a list of all the attached PicoLog CM3 devices of the specified port type.
"""
plcm3.make_symbol("_Enumerate_", "PLCM3Enumerate", c_uint32, [c_void_p, c_void_p, c_uint32], doc)

doc = """
    PICO_STATUS PLCM3GetUnitInfo
    (
        int16_t handle,
        int8_t * string,
        int16_t stringLength,
        int16_t * requiredSize,
        PICO_INFO info
    );
    This routine obtains information on a specified device.
"""
plcm3.make_symbol("_GetUnitInfo_", "PLCM3GetUnitInfo", c_uint32, [c_int16, c_void_p, c_int16, c_void_p, c_uint32], doc)

doc = """
    PICO_STATUS PLCM3GetValue
    (
        int16_t handle,
        PLCM3_CHANNELS channel,
        int32_t * value
    );
    Once you open the driver and define some channels, the driver begins to take continuous readings from the
    PicoLog CM3. When you call this routine, it immediately sets data to the most recent reading for the specified
    channel.
"""
plcm3.make_symbol("_GetValue_", "PLCM3GetValue", c_uint32, [c_int16, c_uint32, c_void_p], doc)

doc = """
    PICO_STATUS PLCM3OpenUnit
    (
        int16_t * handle,
        int8_t * serial
    );
    This routine obtains a handle for the PicoLog CM3 device with the given serial number.
    If you wish to use more than one device, you must call the routine once for each of them.`
"""
plcm3.make_symbol("_OpenUnit_", "PLCM3OpenUnit", c_uint32, [c_void_p, c_void_p], doc)

doc = """
    PICO_STATUS PLCM3IpDetails
    (
        int16_t handle,
        int16_t * enabled,
        int8_t * ipaddress,
        uint16_t * length,
        uint16_t * listeningPort,
        PLCM3_IP_DETAILS_TYPE type
    );
    This routine either reads or writes the IP details of a specified device. The type argument controls whether the
    operation is a read or a write.
"""
plcm3.make_symbol("_IpDetails_", "PLCM3IpDetails", c_uint32, [c_int16, c_void_p, c_void_p, c_void_p, c_void_p, c_uint32], doc)

doc = """
    PICO_STATUS PLCM3OpenUnitViaIp
    (
        int16_t * handle,
        int8_t * serial,
        int8_t * ipAddress
    );
    This routine obtains a handle for the Ethernet-connected PicoLog CM3 device, identified by either its IP address
    or its serial number.
    · Using IP address identification, a device anywhere on the internet or local network can be opened.
    · Using serial number identification, only a device on the local network can be opened.
    If you wish to use more than one PicoLog CM3, you must call the routine once for each device.
"""
plcm3.make_symbol("_OpenUnitViaIp_", "PLCM3OpenUnitViaIp", c_uint32, [c_void_p, c_void_p, c_void_p], doc)

doc = """
    PICO_STATUS PLCM3SetChannel
    (
        int16_t handle,
        PLCM3_CHANNELS channel,
        PLCM3_DATA_TYPES type
    );
    This routine configures a single channel of the specified PicoLog CM3. It can be called any time after calling
    PLCM3OpenUnit.
    The fewer channels selected, the more frequently they will be updated. Measurement takes around 720 ms per
    active channel.
"""
plcm3.make_symbol("_SetChannel_", "PLCM3SetChannel", c_uint32, [c_int16, c_uint32, c_uint32], doc)

doc = """
    PICO_STATUS PLCM3SetMains
    (
        int16_t handle,
        uint16_t sixty_hertz (for 50 Hz set to 0; for 60 Hz set to 1)
    )
    This routine is used to inform the driver of the local mains (line) frequency. This helps the driver to filter out
    electrical noise.
"""
plcm3.make_symbol("_SetMains_", "PLCM3SetMains", c_uint32, [c_int16, c_uint16], doc)

