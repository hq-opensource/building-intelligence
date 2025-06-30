"""
The `api` package provides the core API endpoints for the system.

It includes modules for handling:
- `building`: Endpoints for building-level data (e.g., total consumption, GRAP values).
- `devices`: Endpoints for device management (e.g., setpoints, schedules, state).
- `forecast_data`: Endpoints for retrieving forecast data (e.g., non-controllable loads).
- `historic_data`: Endpoints for retrieving historical data for various device types.
- `models`: Data models and enumerations for the API.
- `preferences_data`: Endpoints for managing user preferences data.
- `weather_data`: Endpoints for accessing historical and forecast weather data.
"""

"""
The `core_api.api` package provides the core API endpoints for the system,
handling requests related to building data, device management, data retrieval,
and user preferences. It serves as the primary interface for interacting with
the system's functionalities.

Modules:
- `building.py`: Exposes endpoints for accessing building-level data, such as
  total energy consumption and Grid Response and Protection (GRAP) values.

- `devices.py`: Provides a comprehensive set of endpoints for managing individual
  devices, including adjusting setpoints, scheduling dispatches, and retrieving
  device lists and states.

- `forecast_data.py`: Offers endpoints for retrieving various types of forecast
  data, with a focus on non-controllable loads, enabling proactive energy
  management.

- `historic_data.py`: Allows for the retrieval of historical data for different
  device types and system-level metrics, supporting analysis and reporting.

- `models.py`: Defines the data models and enumerations used throughout the API
  for request and response validation, ensuring data consistency and clarity.

- `preferences_data.py`: Provides endpoints for managing user preferences data,
  allowing for the retrieval of settings related to comfort, occupancy, and
  device-specific behaviors.

- `weather_data.py`: Exposes endpoints for accessing both historical and forecast
  weather data, which is crucial for accurate energy predictions and system
  optimization.
"""
