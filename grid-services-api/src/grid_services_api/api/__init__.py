"""
This module aggregates the various API components for the Grid Services API.

It brings together the different functionalities from the following submodules:

- `day_ahead`: Endpoints for initiating day-ahead coordination and retrieving optimization status.
- `direct_control`: Endpoints for sending setpoints and power limits to devices.
- `flexibility`: Endpoints for estimating device flexibility.
- `mpc`: Endpoints for sending Model Predictive Control (MPC) requests.
- `paid_control`: Endpoints for paid setpoint requests and device control.
- `tariffs`: Endpoints for optimizing tariffs (flat, Time-of-Use, and consumption-shifting).
- `models`: Pydantic models that define the structure of API requests and responses.
- `publisher`: A utility for publishing RPC payloads to the Redis broker.

Together, these components, referenced by their filenames (`day_ahead.py`, `direct_control.py`, etc.),
form the core of the Grid Services API, enabling robust interaction with and control over grid-related services.
"""
