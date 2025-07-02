---
sidebar_position: 2
---

# Database Module

The `database` package contains modules for querying the database. It provides a suite of modules for handling database interactions within the core API. It includes specialized query classes for retrieving various types of data, such as forecasts, historical records, user preferences, and weather data.

## Forecast Queries

The `ForecastQueries` class handles RPC queries to the data engine for retrieving forecast data, particularly for non-controllable loads.

### Methods

- `load_ec_non_controllable_loads_forecast(start, stop, interval)`: Uses RPC to request non-controllable loads data from the data engine.

## Historic Queries

The `HistoricQueries` class is responsible for querying and retrieving historical data from InfluxDB for various device types and system metrics.

### Methods

- `load_tz_temperature_historic(start, stop, entity_id)`: Retrieves the historic temperature for a given thermal zone.
- `load_tz_setpoint_historic(start, stop, entity_id)`: Retrieves the historic setpoint for a given thermal zone.
- `load_tz_electric_consumption(start, stop, entity_id)`: Retrieves the electric consumption of a specific thermal zone.
- `load_vehicle_consumption_historic(start, stop)`: Retrieves consumption historic for the electric vehicle.
- `load_ec_non_controllable_loads_historic(start, stop)`: Builds and retrieves the non-controllable consumption.

## Preferences Queries

The `PreferencesQueries` class manages the retrieval of user preferences from both InfluxDB and Redis, covering settings like comfort, occupancy, and device-specific preferences.

### Methods

- `load_preferences(device_id, start, stop, preference_type, sampling_in_minutes)`: Loads preferences for a specific device.
- `load_comfort_setpoints(device_id, start, stop, sampling_in_minutes)`: Loads comfort setpoints preferences.
- `load_electric_battery_soc_preferences(device_id, start, stop, sampling_in_minutes)`: Loads electric battery state of charge preferences.
- `load_occupancy_preferences(device_id, start, stop, sampling_in_minutes)`: Loads occupancy preferences.
- `load_vehicle_branched_preferences(device_id, start, stop, sampling_in_minutes)`: Loads vehicle branched preferences.
- `load_vehicle_soc_preferences(device_id, start, stop, sampling_in_minutes)`: Loads vehicle state of charge preferences.
- `load_water_heater_consumption_preferences(device_id, start, stop, sampling_in_minutes)`: Loads water heater consumption preferences.

## Weather Queries

The `WeatherQueries` class is designed to retrieve both historical and forecast weather data from InfluxDB, which is essential for accurate energy predictions and system optimization.

### Methods

- `retrieve_weather_forecast(start, stop, variable, interval)`: Retrieves the forecast of a weather variable between start and stop times.
- `retrieve_weather_historic(start, stop, variable, measurement, interval)`: Retrieves the weather historic data.