from abc import ABC, abstractmethod

from requests import get, post

from common.util.logging import LoggingUtil


logger = LoggingUtil.get_logger(__name__)


class DeviceInterface(ABC):
    @abstractmethod
    def get(self, params: dict) -> float:
        pass

    @abstractmethod
    def set(self, params: dict) -> None:
        pass


class MockDeviceInterface(DeviceInterface):
    def get(self, params: dict) -> float:
        logger.info(f"Received get device state request: {params}")
        return 1.0

    def set(self, params: dict) -> None:
        logger.info(f"Received set device state request: {params}")


class HomeAssistantDeviceInterface(DeviceInterface):
    _host: str
    _port: int
    _token: str

    def __init__(self, host: str, port: int, token: str) -> None:
        self._host = host
        self._port = port
        self._token = token

    def get(self, params: dict) -> float:
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
            "space_heating": {"entity_id": f"climate.{device['entity_id']}", "temperature": action},
            "on_off_ev_charger": {"entity_id": f"switch.{device['entity_id']}"},
            "electric_storage": {"power_value": abs(int(action))},
        }

        response = post(url, headers=headers, json=body[device["type"]])
        logger.info("Device %s requested to apply %s as setpoint", device["entity_id"], action)
        response.raise_for_status()
