"""
The `common` package encapsulates shared modules and utilities that are used across
multiple components of the building intelligence system. It promotes code reuse and
provides centralized implementations for database interactions, device management,
and logging.

Sub-packages:
    - `database`: This package contains modules for interacting with various databases.
        - The `influxdb` submodule provides a client for managing and querying
          time-series data in InfluxDB.
        - The `redis` submodule offers a simplified client for interacting with
          a Redis database, handling tasks like JSON serialization.

    - `device`: This package centralizes device-related definitions and helper utilities.
        - The `helper` submodule defines the `DeviceHelper` Enum for categorizing
          device types and provides static methods for common device operations.

    - `util`: This package provides common utility modules for the application.
        - The `logging` submodule offers a utility for configuring and retrieving
          standardized logger instances, ensuring consistent logging practices.
"""
