"""
This module defines the DeviceType enumeration, which categorizes various types of
devices managed within the system. Each device instance is associated with one of
these predefined types, ensuring consistent classification and handling across the application.
"""

from enum import Enum


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
