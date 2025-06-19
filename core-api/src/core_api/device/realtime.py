from typing import Any, Dict

from faststream.redis import RedisBroker
from faststream.types import DecodedMessage

from common.database.influxdb import InfluxManager
from common.database.redis import RedisClient
from common.device.helper import DeviceHelper
from common.util.logging import LoggingUtil


logger = LoggingUtil.get_logger(__name__)


class RealtimeDataManager:
    def __init__(self, influx_manager: InfluxManager, redis_client: RedisClient) -> None:
        # Define database clients
        self._influx_manager = influx_manager
        self._redis_client = redis_client

        # Read labels for databases
        self._labels_influx = redis_client.safe_read_from_redis("influxdb_mapping")

        # Read devices
        self._devices = redis_client.safe_read_from_redis("user_devices")

        # Redis topic prefix
        labels_channels = redis_client.safe_read_from_redis("labels_channels")
        control_prefix = labels_channels["control_prefix"]

        # Define topics and messages
        self._get_state_request_topic = control_prefix + labels_channels["control"]["get"]
        self._set_state_request_topic = control_prefix + labels_channels["control"]["set"]

    def has_device(self, device_id: str) -> bool:
        return DeviceHelper.device_exists(self._devices, device_id)

    async def set_device_state(self, broker: RedisBroker, device_id: str, action_to_apply: float) -> None:
        device_type = self._get_device_type_using_entity_id(device_id)
        payload = {"device": {"type": device_type, "entity_id": device_id}, "action": action_to_apply}

        await self._publish(broker, payload=payload, topic=self._set_state_request_topic)

    async def get_device_state(self, broker: RedisBroker, entity_id: str, field: str | None = None) -> float:
        device_type = self._get_device_type_using_entity_id(entity_id)
        payload: dict[str, Any] = {"device": {"entity_id": entity_id, "type": device_type}}
        if field is not None:
            payload["field"] = field

        return await self._send_request(broker, payload, self._get_state_request_topic)  # type: ignore

    async def _send_request(self, broker: RedisBroker, payload: Dict[str, Any], topic: str) -> DecodedMessage:
        await broker.connect()
        try:
            rpc_response_message = await broker.request(message=payload, channel=topic)

            logger.info(f"Sent request to the redis broker: {payload}")

            # Decode the response message
            decoded_response = await rpc_response_message.decode()
            return decoded_response
        except Exception as e:
            logger.error("Error sending request to broker: %s", e)
            raise
        finally:
            await broker.close()  # We need to close each time or else we get an event loop error

    async def _publish(self, broker: RedisBroker, payload: Dict[str, Any], topic: str) -> None:
        await broker.connect()
        try:
            await broker.publisher(channel=topic).publish(payload)
            logger.info(f"Published message to the redis broker: {payload}")
        except Exception as e:
            logger.error("Error publishing to broker: %s", e)
            raise
        finally:
            await broker.close()  # We need to close each time or else we get an event loop error

    def _get_device_type_using_entity_id(self, entity_id: str) -> str:
        for device in self._devices:
            if device["entity_id"] == entity_id:
                return device["type"]

        raise ValueError(f"Device with entity_id {entity_id} not found")
