"""This module defines the interface for controlling smart home devices.

It includes an abstract base class `DeviceInterface` that defines the contract for device
control, as well as concrete implementations for Home Assistant devices and a mock
interface for testing purposes. This module is essential for abstracting the details of
device communication and providing a consistent way to interact with different types of
devices.
"""

from abc import ABC, abstractmethod

from requests import get, post

from common.util.logging import LoggingUtil


logger = LoggingUtil.get_logger(__name__)


class DeviceInterface(ABC):
    """Abstract base class for a device interface.

    This class defines the contract for device interfaces, which are responsible for
    getting and setting device states.
    """

    @abstractmethod
    def get(self, params: dict) -> float:
        """Gets the current state of a device.

        Args:
            params (dict): A dictionary of parameters specifying the device and the desired state.

        Returns:
            float: The current state of the device.
        """
        pass

    @abstractmethod
    def set(self, params: dict) -> None:
        """Sets the state of a device.

        Args:
            params (dict): A dictionary of parameters specifying the device and the desired state.
        """
        pass


class MockDeviceInterface(DeviceInterface):
    """A mock implementation of the DeviceInterface for testing purposes."""

    def get(self, params: dict) -> float:
        """Logs the get request and returns a mock value.

        Args:
            params (dict): A dictionary of parameters specifying the device and the desired state.

        Returns:
            float: A mock value of 1.0.
        """
        logger.info(f"Received get device state request: {params}")
        return 1.0

    def set(self, params: dict) -> None:
        """Logs the set request.

        Args:
            params (dict): A dictionary of parameters specifying the device and the desired state.
        """
        logger.info(f"Received set device state request: {params}")


class HomeAssistantDeviceInterface(DeviceInterface):
    """A device interface for Home Assistant.

    This class implements the DeviceInterface for Home Assistant devices, allowing to get and set their states
    by communicating with the Home Assistant API.
    """

    _host: str
    _port: int
    _token: str

    def __init__(self, host: str, port: int, token: str) -> None:
        """Initializes the HomeAssistantDeviceInterface.

        Args:
            host (str): The hostname or IP address of the Home Assistant instance.
            port (int): The port number of the Home Assistant API.
            token (str): The long-lived access token for the Home Assistant API.
        """
        self._host = host
        self._port = port
        self._token = token

    def get(self, params: dict) -> float:
        """Gets the current state of a Home Assistant device.

        This method sends a GET request to the Home Assistant API to retrieve the current state of a device.
        The device and the desired state are specified in the `params` dictionary.

        Args:
            params (dict): A dictionary of parameters specifying the device and the desired state.
                It must contain a "device" key with a dictionary of device information, including the "entity_id"
                and "type". It can also contain an optional "field" key to specify a particular field to retrieve.

        Returns:
            float: The current state of the device.
        """
        device = params["device"]
        field = params.get("field", None)

        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

        url_suffix = {
            "water_heater": f"switch.{device['entity_id']}",
            "space_heating": f"climate.{device['entity_id']}",
            "on_off_ev_charger": f"switch.{device['entity_id']}",
            "electric_storage_soc": "sensor.battery_soc",
            "electric_storage_power": "sensor.battery_power",
            "water_heater_temperature": f"sensor.{device['entity_id']}_temperature",
        }

        state_to_get = {
            "water_heater": "state",
            "space_heating": "temperature",
            "on_off_ev_charger": "state",
            "electric_storage": "state",
        }

        if field is not None:
            suffix = url_suffix[field]
        else:
            suffix = url_suffix[device["type"]]

        url = f"http://{self._host}:{self._port}/api/states/{suffix}"

        response = get(url, headers=headers)
        response.raise_for_status()

        logger.info("Device %s state successfully retrieved", device["entity_id"])

        if state_to_get[device["type"]] == "state":
            device_state = response.json().get(state_to_get[device["type"]])
        else:
            device_state = response.json().get("attributes", {}).get(state_to_get[device["type"]], None)

        if isinstance(device_state, str) and device_state.lower() in ["on", "off"]:
            return 1.0 if device_state.lower() == "on" else 0.0
        else:
            return float(device_state)

    def set(self, params: dict) -> None:
        """Sets the state of a Home Assistant device.

        This method sends a POST request to the Home Assistant API to set the state of a device.
        The device, the desired state, and the action to perform are specified in the `params` dictionary.

        Args:
            params (dict): A dictionary of parameters specifying the device and the desired state.
                It must contain a "device" key with a dictionary of device information, including the "entity_id"
                and "type", and an "action" key with the action to perform.
        """
        logger.info(f"Received set device state request: {params}")

        device: dict = params["device"]
        action = params["action"]

        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

        url_suffix = {
            "water_heater": f"services/switch/{'turn_on' if action else 'turn_off'}",
            "space_heating": "services/climate/set_temperature",
            "on_off_ev_charger": f"services/switch/{'turn_on' if action else 'turn_off'}",
            "electric_storage": f"events/{'set_recharge_battery_power' if action >= 0 else 'set_discharge_battery_power'}",
        }

        url = f"http://{self._host}:{self._port}/api/{url_suffix[device['type']]}"

        body = {
            "water_heater": {"entity_id": f"switch.{device['entity_id']}"},
            "space_heating": {
                "entity_id": f"climate.{device['entity_id']}",
                "temperature": action,
            },
            "on_off_ev_charger": {"entity_id": f"switch.{device['entity_id']}"},
            "electric_storage": {"power_value": abs(int(action))},
        }

        response = post(url, headers=headers, json=body[device["type"]])
        logger.info("Device %s requested to apply %s as setpoint", device["entity_id"], action)
        response.raise_for_status()
