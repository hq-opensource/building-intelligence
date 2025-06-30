"""This package provides an interface for controlling smart home devices.

This package is the main entry point for the Home Assistant device interface service.
It is responsible for setting up the application and handling device control requests.

The main components of this package are:
- `app.py`: This is the main application entry point. It initializes the FastStream
  application, sets up the Redis broker, and includes the necessary routers for
  handling device control requests.

- `control`: This subpackage contains the core logic for device control.
  - `control/interface.py`: Defines the abstract `DeviceInterface` and provides
    concrete implementations for interacting with Home Assistant and a mock interface
    for testing.
  - `control/subscriber.py`: Sets up a Redis subscriber to listen for device
    control commands and delegates them to the appropriate device interface.
"""
