---
id: device
title: Device
---

The `device` package provides common modules for device-related definitions and utilities.

It includes:
- `helper`: Defines the `DeviceHelper` Enum for categorizing device types and provides static utility methods for querying and manipulating device data.

## DeviceHelper

The `DeviceHelper` Enum is a central component for managing and categorizing various device types within the ecosystem. It provides a standardized set of device types, ensuring consistency across different modules and applications. In addition to defining device categories, the `DeviceHelper` also offers a collection of static utility methods that simplify common tasks related to querying and manipulating lists of device data.

### Device Types

The `DeviceHelper` Enum defines the following device types:

- **`ON_OFF_EV_CHARGER`**: Represents an EV charger that can be turned on or off.
- **`ELECTRIC_VEHICLE_V1G`**: A V1G-capable electric vehicle, allowing for controlled charging.
- **`ELECTRIC_VEHICLE_V2G`**: A V2G-capable electric vehicle, enabling bidirectional energy flow.
- **`ELECTRIC_STORAGE`**: A stationary battery or other electrical energy storage system.
- **`PHOTOVOLTAIC_GENERATOR_PVLIB`**: A photovoltaic generator, modeled using the `pvlib` library.
- **`SPACE_HEATING`**: A device used for heating a space, such as a heat pump or furnace.
- **`THERMAL_STORAGE`**: A system for storing thermal energy, like a hot water tank.
- **`WATER_HEATER`**: A device specifically for heating water.

### Utility Methods

The `DeviceHelper` class includes several static methods that provide convenient ways to work with lists of device data. These methods are designed to be reusable and help streamline common data manipulation tasks.

- **`device_exists(devices: List, device_id: str) -> bool`**
  
  This method checks if a device with a specific `entity_id` exists within a list of device dictionaries. It iterates through the list and returns `True` if a matching device is found, and `False` otherwise. This is useful for quickly verifying the presence of a device before performing further operations.

- **`count_devices_by_type(device_list: List, device_type: str) -> int`**

  This method counts the number of devices of a particular type within a list of device dictionaries. It is useful for gathering statistics about the composition of a device fleet, such as determining how many space heaters or electric vehicles are present.

- **`get_all_values_by_filtering_devices(device_list: list, filter_key: str, filter_value: str, target_key: str) -> List[str]`**

  This method allows you to extract specific values from a list of devices based on a filtering criterion. For example, you can use it to get all the `entity_id`s of devices with the type "space_heating". It iterates through the device list, filters them based on the provided key-value pair, and returns a list of values from the specified `target_key`.

By providing both a standardized set of device types and a suite of utility methods, the `DeviceHelper` simplifies device management and helps ensure consistency and reliability across the system.