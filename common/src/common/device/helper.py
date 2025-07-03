"""
This module defines the DeviceHelper Enum, which categorizes various device types.

It also provides static utility methods for querying and manipulating lists of device data,
such as checking for device existence, counting devices by type, and extracting specific
values based on filtering criteria.
"""

from enum import Enum
from typing import List


class DeviceHelper(Enum):
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

    @staticmethod
    def device_exists(devices: List, device_id: str) -> bool:
        """
        Checks if a device with the specified entity ID exists within a list of device dictionaries.

        Args:
            devices (List): A list of dictionaries, where each dictionary represents a device.
            device_id (str): The entity ID of the device to search for.

        Returns:
            bool: True if a device with the given `device_id` is found, False otherwise.
        """
        return any(device.get("entity_id") == device_id for device in devices)

    @staticmethod
    def count_devices_by_type(device_list: List, device_type: str) -> int:
        """
        Counts the number of devices of a specific type within a list of device dictionaries.

        Args:
            device_list (List): A list of dictionaries, where each dictionary represents a device.
            device_type (str): The type of device to count (e.g., "space_heating").

        Returns:
            int: The total number of devices that match the specified `device_type`.
        """
        return sum(device.get("type") == device_type for device in device_list)

    @staticmethod
    def get_all_values_by_filtering_devices(
        device_list: list, filter_key: str, filter_value: str, target_key: str
    ) -> List[str]:
        """
        Extracts values of a `target_key` from devices in a list that match a specific `filter_key` and `filter_value`.

        This method iterates through a list of device dictionaries and returns a list of values
        corresponding to the `target_key` for all devices that satisfy the filtering criteria.

        Args:
            device_list (list): A list of dictionaries, where each dictionary represents a device.
            filter_key (str): The key to use for filtering devices (e.g., "type").
            filter_value (str): The value that `filter_key` must match for a device to be included.
            target_key (str): The key whose values are to be extracted from the filtered devices (e.g., "entity_id").

        Returns:
            List[str]: A list of extracted `target_key` values from the filtered devices.
        """
        return [
            device.get(target_key)
            for device in device_list
            if device.get(filter_key) == filter_value and target_key in device
        ]
