"""
The `core_api` package is the central hub for the building intelligence system's API.

It is composed of several key sub-packages that work together to provide a comprehensive
set of functionalities for managing building data, devices, and schedules.

Sub-packages:
    - `api`: This package exposes the core API endpoints for interacting with the system.
        - It includes modules for handling requests related to `building` data, `devices`
          management, `forecast_data` retrieval, `historic_data` access, user
          `preferences_data`, and `weather_data`.

    - `database`: This package provides modules for handling all database interactions.
        - It contains specialized query classes for retrieving `forecast_queries`,
          `historic_queries`, `preferences_queries`, and `weather_queries`.

    - `device`: This package contains modules for managing and interacting with devices.
        - The `helper` module provides device classification and utility functions.
        - The `historical` module is responsible for retrieving historical device data.
        - The `realtime` module manages real-time device control and data retrieval.

    - `schedule`: This package offers a framework for managing and monitoring device schedules.
        - The `device_scheduler` module handles device-specific scheduling.
        - The `models` module defines the data structures for scheduling.
        - The `monitor` module provides tools for monitoring schedulers.
        - The `weekly_scheduler` module manages recurring weekly schedules.
"""
