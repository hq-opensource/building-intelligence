---
sidebar_position: 2
---

# Control

The `control` subpackage is the core of the `ha-device-interface` service, providing the necessary tools to manage and interact with smart home devices. It is composed of two main modules: `interface.py` and `subscriber.py`.

## `interface.py`

This module defines the contract for device control through the abstract base class `DeviceInterface`. This class ensures that all device implementations adhere to a common structure, which includes the following methods:

- **`get(params: dict) -> float`**: Retrieves the current state of a device.
- **`set(params: dict) -> None`**: Sets a new state for a device.

The module also provides two concrete implementations of the `DeviceInterface`:

- **`HomeAssistantDeviceInterface`**: Interacts with the Home Assistant API to control devices. It handles the communication details, such as authentication and request formatting, allowing for seamless integration with a Home Assistant instance.
- **`MockDeviceInterface`**: A mock implementation used for testing purposes. It simulates the behavior of a real device, which is useful for development and debugging without requiring a physical device.

## `subscriber.py`

This module is responsible for handling incoming device control requests. It sets up a Redis subscriber that listens on dedicated channels for `get` and `set` commands. When a message is received, the subscriber instantiates the appropriate device interface—based on the application's configuration—and executes the requested command.

This architecture allows for a decoupled and scalable system where new device types can be easily added without modifying the core logic of the application.