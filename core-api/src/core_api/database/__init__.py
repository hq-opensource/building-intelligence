"""
The `database` package contains modules for querying the database.

It includes:
- `forecast_queries`: Handles RPC queries for forecast data.
- `historic_queries`: Retrieves historical data from InfluxDB.
- `preferences_queries`: Manages the retrieval of user preferences.
- `weather_queries`: Retrieves historical and forecast weather data.
"""

"""
The `core_api.database` package provides a suite of modules for handling
database interactions within the core API. It includes specialized query classes
for retrieving various types of data, such as forecasts, historical records,
user preferences, and weather data.

Modules:
- `forecast_queries.py`: Implements the `ForecastQueries` class, which handles
  RPC queries to the data engine for retrieving forecast data, particularly for
  non-controllable loads.

- `historic_queries.py`: Contains the `HistoricQueries` class, responsible for
  querying and retrieving historical data from InfluxDB for various device
  types and system metrics.

- `preferences_queries.py`: Provides the `PreferencesQueries` class, which
  manages the retrieval of user preferences from both InfluxDB and Redis,
  covering settings like comfort, occupancy, and device-specific preferences.

- `weather_queries.py`: Features the `WeatherQueries` class, designed to
  retrieve both historical and forecast weather data from InfluxDB, which is
  essential for accurate energy predictions and system optimization.
"""
