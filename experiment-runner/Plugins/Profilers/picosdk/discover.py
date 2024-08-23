#
# Copyright (C) 2018 Pico Technology Ltd. See LICENSE file for terms.
#
from Plugins.Profilers.picosdk.errors import DeviceNotFoundError
from Plugins.Profilers.picosdk.plcm3 import plcm3


# the A drivers are faster to enumerate devices, so search them first.
drivers = [
    plcm3
]


def find_unit():
    """Search for, open and return the first device connected, on any driver."""
    for driver in drivers:
        try:
            device = driver.open_unit()
        except DeviceNotFoundError:
            continue
        return device
    raise DeviceNotFoundError("Could not find any devices on any drivers.")


def find_all_units():
    """Search for, open and return ALL devices on ALL pico drivers (supported in this SDK wrapper)."""
    devices = []
    for driver in drivers:
        try:
            device = driver.open_unit()
        except DeviceNotFoundError:
            continue
        devices.append(device)
    if not devices:
        raise DeviceNotFoundError("Could not find any devices on any drivers.")
    return devices
