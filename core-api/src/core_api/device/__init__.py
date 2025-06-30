"""
The `device` package contains modules for managing and interacting with devices.

It includes:
- `helper`: Provides the `DeviceHelper` Enum for device classification and utility functions.
- `historical`: Contains the `HistoricalDataReader` for retrieving historical device data.
- `realtime`: Features the `RealtimeDataManager` for managing real-time device interactions.
"""

"""
The `core_api.device` package provides a comprehensive suite of modules for
managing and interacting with various devices within the system. It includes
functionalities for device classification, historical data retrieval, and real-time
device control.

Modules:
- `helper.py`: Implements the `DeviceHelper` class, which offers utility functions
  for device-related operations, such as checking for device existence, counting
  devices by type, and filtering device lists.

- `historical.py`: Contains the `HistoricalDataReader` class, responsible for
  retrieving historical data for a wide range of devices from InfluxDB. It
  provides specialized methods for different device types, ensuring accurate
  data extraction.

- `realtime.py`: Features the `RealtimeDataManager` class, designed to manage
  real-time interactions with devices. This includes setting device states and
  retrieving current data through a Redis message broker, enabling dynamic
  device control.
"""
