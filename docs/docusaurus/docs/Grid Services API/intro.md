---
sidebar_position: 1
---

# Grid Services API

The Grid Services API is a peripheral service responsible for exposing endpoints that interact with various grid-related functionalities.

## Overview

The main application, defined in `app.py`, is a FastAPI instance that orchestrates the different components of the API. It sets up the Redis broker for asynchronous communication, reads necessary channel labels from Redis for dynamic topic creation, and includes the API routers that define the endpoints for different services.

## Submodules

The Grid Services API is composed of the following submodules:

### API

This package contains the core logic for the API. It is composed of several submodules that handle specific functionalities:

- **`day_ahead.py`**: Manages day-ahead coordination processes.
- **`direct_control.py`**: Provides endpoints for direct load control of devices.
- **`flexibility.py`**: Handles requests for estimating device flexibility.
- **`mpc.py`**: Exposes endpoints for Model Predictive Control (MPC) requests.
- **`paid_control.py`**: Manages paid setpoint requests and device control.
- **`tariffs.py`**: Provides endpoints for optimizing various dynamic tariffs.
- **`models.py`**: Defines the Pydantic models for data validation and structure across the API.
- **`publisher.py`**: Contains a utility for publishing RPC payloads to the Redis broker, which is used by the other API modules.

### HTML

This package contains the HTML file for the root endpoint of the API, served by `app.py`.

The main application (`app.py`) ties these components together, creating a robust and well-structured API for interacting with grid services. The application is started using uvicorn and can be run as the main entry point.