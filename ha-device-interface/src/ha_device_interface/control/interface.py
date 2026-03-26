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
        if "temperature" in str(params):
            return 50.0
        if params.get("device", {}).get("type") == "space_heating":
            return 20.0
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


    def _resolve_ha_info(self, device_id: str, device_type: str, action: float = None, field: str = None) -> dict:
        """Resolves the HA entity ID, domain, service and payload details."""
        logger.debug(f"Resolving HA info for device_id={device_id}, device_type={device_type}, action={action}, field={field}")
        
        # Default info
        info = {
            "entity": f"sensor.{device_id}",
            "domain": "sensor",
            "service": "get_state",
            "get_attr": "state",
            "body": {"entity_id": f"sensor.{device_id}"}
        }

        # 1. Water Heater & Thermal Storage Logic
        if device_type in ["water_heater", "thermal_storage"] or device_id == "water_heater":
            if field in ["temperature_water_heater", "water_heater_temperature"]:
                info["entity"] = "sensor.sinope_technologies_rm3500zb_device_temperature"
                info["domain"] = "sensor"
            else:
                # Assuming thermal storage is also controlled via the same RMS3500ZB switch 
                # or a similar one. Based on devices.yaml, they might share entity names 
                # but here we follow the "Rosetta Stone"
                info["entity"] = "switch.sinope_technologies_rm3500zb"
                info["domain"] = "switch"
                if action is not None:
                    info["service"] = "turn_on" if action > 0 else "turn_off"
                    info["body"] = {"entity_id": info["entity"]}

        # 2. EV / Charger Logic
        elif "evduty" in device_id or device_type in ["on_off_ev_charger", "ev_charger_station", "electric_vehicle_v1g"]:
            info["entity"] = "number.evduty_borne_evduty_evc30_17286_meeb1_max_amp"
            info["domain"] = "number"
            if action is not None:
                # Convert kW to Amps (Assuming 240V Level 2 charging)
                # action is in kW, entity expects Amps (0-30 A)
                amp_value = round((action * 1000) / 240)
                # Ensure it's within the allowed 0-30A range and follows 1A steps
                amp_value = max(0, min(30, int(amp_value)))
                info["service"] = "set_value"
                info["body"] = {"entity_id": info["entity"], "value": amp_value}

        # 3. Space Heating Logic
        elif device_type == "space_heating":
            info["entity"] = f"climate.{device_id}"
            info["domain"] = "climate"
            info["get_attr"] = "temperature" # setpoint
            if action is not None:
                info["service"] = "set_temperature"
                info["body"] = {"entity_id": info["entity"], "temperature": action}

        # 4. Electric Storage Logic
        elif device_type == "electric_storage" or device_id == "electric_storage":
            if field in ["state_of_charge", "electric_storage_soc"]:
                info["entity"] = "sensor.battery_soc"
                info["domain"] = "sensor"
            else:
                info["entity"] = "sensor.battery_power"
                info["domain"] = "sensor"
            
            if action is not None:
                # Battery uses custom events via REST API
                # Convert kW to Watts (Assuming event expects Watts)
                watt_value = abs(int(action * 1000))
                event_name = "set_recharge_battery_power" if action >= 0 else "set_discharge_battery_power"
                info["domain"] = "events" # Specialized for the URL construction
                info["service"] = event_name
                info["body"] = {"power_value": watt_value}
        
        else:
            logger.warning(f"Device type {device_type} (id={device_id}) not explicitly covered in mapping. Using fallback.")

        return info

    def get(self, params: dict) -> float:
        """Gets the current state of a Home Assistant device."""
        device = params["device"]
        field = params.get("field", None)
        
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

        try:
            info = self._resolve_ha_info(device["entity_id"], device["type"], field=field)
            url = f"http://{self._host}:{self._port}/api/states/{info['entity']}"

            response = get(url, headers=headers)
            response.raise_for_status()

            data = response.json()
            logger.info("Device %s state successfully retrieved from %s", device["entity_id"], info['entity'])

            if info["get_attr"] == "state":
                device_state = data.get("state")
            else:
                device_state = data.get("attributes", {}).get(info["get_attr"], None)

            if isinstance(device_state, str):
                if device_state.lower() == "on":
                    return 1.0
                if device_state.lower() == "off":
                    return 0.0
                try:
                    return float(device_state)
                except (ValueError, TypeError):
                    return 0.0
            
            return float(device_state) if device_state is not None else 0.0
        except Exception as e:
            logger.error(f"Error getting state for device {device['entity_id']}: {e}")
            return 0.0

    def set(self, params: dict) -> None:
        """Sets the state of a Home Assistant device."""
        logger.info(f"Received set device state request: {params}")

        device = params["device"]
        action = params["action"]

        # Deactivate setpoints for thermostats (space_heating) as requested
        if device.get("type") == "space_heating":
            logger.info("Thermostat deactivation active: Skipping setpoint application for %s (setpoint: %s)", 
                        device.get("entity_id"), action)
            return

        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

        try:
            info = self._resolve_ha_info(device["entity_id"], device["type"], action=action)
            
            if info["domain"] == "sensor":
                logger.warning(f"Cannot SET state for sensor entity {info['entity']}. Skipping.")
                return

            # Specialized URL for events vs services
            api_type = "events" if info["domain"] == "events" else f"services/{info['domain']}"
            url = f"http://{self._host}:{self._port}/api/{api_type}/{info['service']}"

            logger.debug(f"Sending POST to {url} with body {info['body']}")
            response = post(url, headers=headers, json=info["body"])
            response.raise_for_status()
            
            logger.info("Device %s (%s) successfully requested to apply %s via %s", 
                        device["entity_id"], info["entity"], action, info["service"])
        except Exception as e:
            logger.error(f"Error setting state for device {device['entity_id']}: {e}")
