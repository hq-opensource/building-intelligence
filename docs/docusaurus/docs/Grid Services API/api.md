---
sidebar_position: 2
---

# API

This module aggregates the various API components for the Grid Services API.

It brings together the different functionalities from the following submodules:

- **`day_ahead`**: Endpoints for initiating day-ahead coordination and retrieving optimization status.
- **`direct_control`**: Endpoints for sending setpoints and power limits to devices.
- **`flexibility`**: Endpoints for estimating device flexibility.
- **`mpc`**: Endpoints for sending Model Predictive Control (MPC) requests.
- **`paid_control`**: Endpoints for paid setpoint requests and device control.
- **`tariffs`**: Endpoints for optimizing tariffs (flat, Time-of-Use, and consumption-shifting).
- **`models`**: Pydantic models that define the structure of API requests and responses.
- **`publisher`**: A utility for publishing RPC payloads to the Redis broker.

Together, these components form the core of the Grid Services API, enabling robust interaction with and control over grid-related services.

## Day Ahead Coordination

This module defines the API endpoints for Day Ahead Coordination within the Grid Services API. It provides functionalities to initiate day-ahead coordination processes and retrieve the optimization status from the Model Predictive Control (MPC) system.

### Endpoints

- `POST /coordinatedac`: Initiates the Day Ahead Coordination grid function. This endpoint triggers the day-ahead coordination process, which involves calculating prices and preparing an RPC payload for the MPC system.
- `POST /request_optimization_status`: Retrieves the current optimization status from the MPC system.

## Direct Load Control

This module defines the API endpoints for Direct Load Control within the Grid Services API. It provides functionalities to directly control devices by sending setpoints and power limits to subscribed users or devices.

### Endpoints

- `POST /write_device_type_setpoint`: Sends a fixed setpoint to all subscribed devices of a specific type.
- `POST /power_limit`: Sends power limits to subscribed users or devices.

## Flexibility Requests

This module defines the API endpoints for Flexibility Requests within the Grid Services API. It provides functionalities to request and estimate the flexibility of connected devices, typically for direct load control purposes.

### Endpoints

- `GET /getflexibility`: Requests the flexibility from all subscribed users or devices.