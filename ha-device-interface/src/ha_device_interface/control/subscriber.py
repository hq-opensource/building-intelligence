"""This module is responsible for handling device control requests.

It sets up a Redis subscriber to listen for messages on specific channels and
delegates the requests to the appropriate device interface implementation. The module
supports different device interface implementations, such as Home Assistant and a mock
interface, which can be configured through environment variables. This allows for a
flexible and extensible architecture for controlling smart home devices.
"""

import os

from datetime import datetime

from faststream.redis import RedisRouter

from common.database.redis import RedisClient
from common.util.logging import LoggingUtil
from ha_device_interface.control.interface import DeviceInterface


logger = LoggingUtil.get_logger(__name__)
logger.info("The Device Controller is starting at %s:", str(datetime.now().astimezone()))


# Create the redis client
redis_password = os.getenv("REDIS_PASSWORD")
redis_host = os.getenv("REDIS_HOST")
redis_port = os.getenv("REDIS_PORT")
redis_client = RedisClient(redis_host, redis_port, redis_password)

# Read the channels configuration from Redis
labels_channels = redis_client.safe_read_from_redis("labels_channels")


# Redis event broker setup
device_interface_router = RedisRouter(prefix=labels_channels["control_prefix"])

# Define topics and messages
get_state_request_topic = labels_channels["control"]["get"]
set_state_request_topic = labels_channels["control"]["set"]

device_interface_implementation = os.getenv("DEVICE_INTERFACE_IMPLEMENTATION", "ha")

device_controller: DeviceInterface

if device_interface_implementation == "ha":
    from ha_device_interface.control.interface import HomeAssistantDeviceInterface

    ha_host = str(os.getenv("HA_HOST"))
    ha_port = int(os.getenv("HA_PORT", 8123))
    ha_token = str(os.getenv("HA_TOKEN"))
    device_controller = HomeAssistantDeviceInterface(ha_host, ha_port, ha_token)
elif device_interface_implementation == "mock":
    from ha_device_interface.control.interface import MockDeviceInterface

    device_controller = MockDeviceInterface()
else:
    raise ValueError(f"Invalid device controller implementation: {device_interface_implementation}")


@device_interface_router.subscriber(get_state_request_topic)
async def handle_get_state_request(get_state_request: dict) -> float:
    """Handles get state requests for devices.

    This function is a subscriber to the `get_state_request_topic`, which listens for messages
    requesting the current state of a device. It then calls the `get` method of the `device_controller`
    to retrieve the state and returns it.

    Args:
        get_state_request (dict): A dictionary containing the request parameters,
            which specify the device and the desired state.

    Returns:
        float: The current state of the device.
    """
    return device_controller.get(get_state_request)


@device_interface_router.subscriber(set_state_request_topic)
async def handle_set_state_request(set_state_request: dict) -> None:
    """Handles set state requests for devices.

    This function is a subscriber to the `set_state_request_topic`, which listens for messages
    requesting to set the state of a device. It then calls the `set` method of the `device_controller`
    to apply the requested state.

    Args:
        set_state_request (dict): A dictionary containing the request parameters,
            which specify the device and the desired state.
    """
    device_controller.set(set_state_request)
