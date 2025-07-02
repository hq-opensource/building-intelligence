---
sidebar_position: 0
---

# Core API Introduction

The `core_api` package is the central hub for the building intelligence system's API. It is composed of several key sub-packages that work together to provide a comprehensive set of functionalities for managing building data, devices, and schedules.

## Sub-packages

### API

This package exposes the core API endpoints for interacting with the system. It includes modules for handling requests related to:

- **Building Data**: Endpoints for building-level data (e.g., total consumption, GRAP values).
- **Device Management**: Endpoints for device management (e.g., setpoints, schedules, state).
- **Forecast Data**: Endpoints for retrieving forecast data (e.g., non-controllable loads).
- **Historic Data**: Endpoints for retrieving historical data for various device types.
- **Preferences Data**: Endpoints for managing user preferences data.
- **Weather Data**: Endpoints for accessing historical and forecast weather data.

### Database

This package provides modules for handling all database interactions. It contains specialized query classes for retrieving:

- **Forecast Queries**: Handles RPC queries for forecast data.
- **Historic Queries**: Retrieves historical data from InfluxDB.
- **Preferences Queries**: Manages the retrieval of user preferences.
- **Weather Queries**: Retrieves historical and forecast weather data.

### Device

This package contains modules for managing and interacting with devices.

- **Helper**: Provides the `DeviceHelper` Enum for device classification and utility functions.
- **Historical**: Contains the `HistoricalDataReader` for retrieving historical device data.
- **Realtime**: Features the `RealtimeDataManager` for managing real-time device interactions.

### Schedule

This package offers a framework for managing and monitoring device schedules.

- **Device Scheduler**: Implements device-specific scheduling functionality.
- **Models**: Defines core data models and enumerations for scheduling.
- **Monitor**: Provides capabilities for monitoring and managing schedulers.
- **Weekly Scheduler**: Implements a scheduler for managing weekly recurring events.