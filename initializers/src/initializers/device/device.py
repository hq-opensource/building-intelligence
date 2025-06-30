"""
This module defines the `DeviceType` Enum and the `DeviceHelper` class.

`DeviceType` enumerates various types of devices supported by the system,
while `DeviceHelper` provides static utility methods for querying and
manipulating lists of device dictionaries based on their type.
"""

from enum import Enum
from typing import Any, Dict, List


class DeviceType(Enum):
    """Enum that defines different device types.

    Every device created has a type associated with it. The type comes from this module.
    """

    ON_OFF_EV_CHARGER = "on_off_ev_charger"
    ELECTRIC_VEHICLE_V1G = "electric_vehicle_v1g"
    ELECTRIC_VEHICLE_V2G = "electric_vehicle_v2g"
    ELECTRIC_STORAGE = "electric_storage"
    PHOTOVOLTAIC_GENERATOR_PVLIB = "photovoltaic_generator_pvlib"
    SPACE_HEATING = "space_heating"
    THERMAL_STORAGE = "thermal_storage"
    WATER_HEATER = "water_heater"


class DeviceHelper:
    """
    A utility class providing helper methods for working with lists of device dictionaries.

    This class offers static methods to count, check for existence, and filter devices
    based on their `DeviceType`.
    """

    @staticmethod
    def count_devices_by_type(devices: List[Dict[str, Any]], device_type: DeviceType) -> int:
        """
        Counts the number of devices of a specific type within a list of device dictionaries.

        Args:
            devices (List[Dict[str, Any]]): A list where each dictionary represents a device,
                                            expected to have a "type" key.
            device_type (DeviceType): The `DeviceType` enum member to count.

        Returns:
            int: The total number of devices matching the specified `device_type`.
        """
        return sum(device.get("type") == device_type.value for device in devices)

    @staticmethod
    def has_device_type(devices: List[Dict[str, Any]], device_type: DeviceType) -> bool:
        """
        Checks if any device of the specified type exists within a list of device dictionaries.

        Args:
            devices (List[Dict[str, Any]]): A list where each dictionary represents a device,
                                            expected to have a "type" key.
            device_type (DeviceType): The `DeviceType` enum member to check for.

        Returns:
            bool: True if at least one device of the given `device_type` is found, False otherwise.
        """
        return device_type.value in [device["type"] for device in devices]

    @staticmethod
    def get_devices_of_type(devices: List[Dict[str, Any]], device_type: DeviceType) -> List[Dict[str, Any]]:
        """
        Retrieves all devices of a specified type from a list of device dictionaries.

        Args:
            devices (List[Dict[str, Any]]): A list where each dictionary represents a device,
                                            expected to have a "type" key.
            device_type (DeviceType): The `DeviceType` enum member to filter by.

        Returns:
            List[Dict[str, Any]]: A new list containing only the devices that match the
                                  specified `device_type`.
        """
        return [device for device in devices if device["type"] == device_type.value]
