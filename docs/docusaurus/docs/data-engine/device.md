---
id: device
title: Device
sidebar_label: Device
---

The `data_engine.device` package provides modules for device-related functionalities, focusing on the classification and management of various device types within the system. This package is crucial for ensuring that devices are handled consistently and correctly across the application.

## DeviceType Enumeration

The `device_type.py` module defines the `DeviceType` enumeration, which provides a centralized and standardized way of categorizing all supported device types. This enumeration is used throughout the system to identify and manage devices such as EV chargers, energy storage systems, and heating units.

### Supported Device Types:

-   **ON_OFF_EV_CHARGER**: A simple electric vehicle charger that can be turned on or off.
-   **ELECTRIC_VEHICLE_V1G**: An electric vehicle with V1G (unidirectional charging) capabilities.
-   **ELECTRIC_VEHICLE_V2G**: An electric vehicle with V2G (vehicle-to-grid) capabilities, allowing it to both charge and discharge.
-   **ELECTRIC_STORAGE**: A stationary battery energy storage system.
-   **PHOTOVOLTAIC_GENERATOR_PVLIB**: A photovoltaic (solar) generator, with models based on the PVLIB library.
-   **SPACE_HEATING**: A device used for heating a space, such as a heat pump or electric heater.
-   **THERMAL_STORAGE**: A system for storing thermal energy, such as a hot water tank.
-   **WATER_HEATER**: A device specifically for heating water.