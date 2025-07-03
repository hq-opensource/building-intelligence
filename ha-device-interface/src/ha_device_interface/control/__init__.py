"""This package provides the core functionality for controlling smart home devices.

It is composed of two main submodules: `interface.py` and `subscriber.py`.

The `interface.py` submodule defines the abstract `DeviceInterface`, which establishes
a contract for all device control implementations. It specifies the essential `get` and
`set` methods for interacting with devices. This submodule also includes concrete
implementations:
- `HomeAssistantDeviceInterface`: Interacts with the Home Assistant API.
- `MockDeviceInterface`: A mock implementation used for testing purposes.

The `subscriber.py` submodule is responsible for handling incoming device control
requests. It sets up a Redis subscriber that listens on dedicated channels for `get` and
`set` commands. Based on the application's configuration, it instantiates the
appropriate device interface (e.g., `HomeAssistantDeviceInterface`) and uses it to
execute the requested commands.
"""
