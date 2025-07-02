---
sidebar_position: 3
---

# Device Module

The `device` package provides a comprehensive suite of modules for managing and interacting with various devices within the system. It includes functionalities for device classification, historical data retrieval, and real-time device control.

## Device Helper

The `helper.py` module implements the `DeviceHelper` class, which offers utility functions for device-related operations.

### Device Types (Enum)

The `DeviceHelper` enum defines the following device types:

- `ON_OFF_EV_CHARGER`
- `ELECTRIC_VEHICLE_V1G`
- `ELECTRIC_VEHICLE_V2G`
- `ELECTRIC_STORAGE`
- `PHOTOVOLTAIC_GENERATOR_PVLIB`
- `SPACE_HEATING`
- `THERMAL_STORAGE`
- `WATER_HEATER`

### Static Methods

- `device_exists(devices, device_id)`: Checks if a device with the specified ID exists in a list of devices.
- `count_devices_by_type(device_list, device_type)`: Counts the number of devices of a specific type in a list.
- `get_all_values_by_filtering_devices(device_list, filter_key, filter_value, target_key)`: Retrieves a list of values for a `target_key` from a list of devices, filtered by a `filter_key` and `filter_value`.

## Historical Data Reader

The `historical.py` module contains the `HistoricalDataReader` class, responsible for retrieving historical data for a wide range of devices from InfluxDB.

### Methods

- `get_historical_data(start, stop, devices)`: Retrieves historical data for a list of devices. It uses helper methods to get data based on the device type.

## Realtime Data Manager

The `realtime.py` module features the `RealtimeDataManager` class, designed to manage real-time interactions with devices. This includes setting device states and retrieving current data through a Redis message broker.

### Methods

- `has_device(device_id)`: Checks if a device exists.
- `set_device_state(broker, device_id, action_to_apply)`: Sets the state of a device by publishing a message to the Redis broker.
- `get_device_state(broker, entity_id, field)`: Gets the state of a device by sending a request to the Redis broker.