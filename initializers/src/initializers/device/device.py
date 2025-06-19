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
    @staticmethod
    def count_devices_by_type(devices: List[Dict[str, Any]], device_type: DeviceType) -> int:
        """
        Count the number of devices of the specified type in the list.

        :param devices: List of dictionaries representing devices.
        :param device_type: The type of device to count.
        :return: The number of devices of the given type.
        """
        return sum(device.get("type") == device_type.value for device in devices)

    @staticmethod
    def has_device_type(devices: List[Dict[str, Any]], device_type: DeviceType) -> bool:
        """
        Check if the specified device type is in the list of devices.

        :param devices: List of dictionaries representing devices.
        :param device_type: The type of device.
        :return: If the device type is found in the list.
        """
        return device_type.value in [device["type"] for device in devices]

    @staticmethod
    def get_devices_of_type(devices: List[Dict[str, Any]], device_type: DeviceType) -> List[Dict[str, Any]]:
        """
        Get all devices of the specified type in the list.

        :param devices: List of dictionaries representing devices.
        :param device_type: The type of device to get.
        :return: The devices of the given type.
        """
        return [device for device in devices if device["type"] == device_type.value]
