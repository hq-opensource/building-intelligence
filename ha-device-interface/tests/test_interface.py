from unittest.mock import Mock, patch

import pytest

from ha_device_interface.control.interface import HomeAssistantDeviceInterface


@pytest.fixture
def ha_device_interface() -> HomeAssistantDeviceInterface:
    return HomeAssistantDeviceInterface(host="localhost", port=8123, token="test_token")


def test_get_device_state(ha_device_interface: HomeAssistantDeviceInterface) -> None:
    params = {"device": {"entity_id": "test_device", "type": "water_heater"}, "variable": None}
    mock_response = Mock()
    mock_response.json.return_value = {"state": "on"}
    mock_response.raise_for_status = Mock()

    with patch("ha_device_interface.control.interface.get", return_value=mock_response) as mock_get:
        state = ha_device_interface.get(params)
        mock_get.assert_called_once_with(
            "http://localhost:8123/api/states/switch.test_device",
            headers={
                "Authorization": "Bearer test_token",
                "Content-Type": "application/json",
            },
        )
        assert state == pytest.approx(1.0)


def test_set_device_state(ha_device_interface: HomeAssistantDeviceInterface) -> None:
    params = {"device": {"entity_id": "test_device", "type": "water_heater"}, "action": True}
    mock_response = Mock()
    mock_response.raise_for_status = Mock()

    with patch("ha_device_interface.control.interface.post", return_value=mock_response) as mock_post:
        ha_device_interface.set(params)
        mock_post.assert_called_once_with(
            "http://localhost:8123/api/services/switch/turn_on",
            headers={
                "Authorization": "Bearer test_token",
                "Content-Type": "application/json",
            },
            json={"entity_id": "switch.test_device"},
        )
