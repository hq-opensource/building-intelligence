from datetime import datetime, timedelta
from typing import Any, Dict

from faststream.redis import RedisBroker
from faststream.types import DecodedMessage

from common.database.redis import RedisClient
from common.util.logging import LoggingUtil


logger = LoggingUtil.get_logger(__name__)


class ForecastQueries:
    """Saves the RPC queries to retrieve forecast data from the data engine."""

    def __init__(self, redis_client: RedisClient, redis_broker: RedisBroker) -> None:
        # Redis topic prefix
        labels_channels = redis_client.safe_read_from_redis("labels_channels")
        forecaster_prefix = labels_channels["forecaster_prefix"]

        # Define topics and messages
        self._message_topic = labels_channels["non_controllable_loads"]
        self._get_state_request_topic = forecaster_prefix + self._message_topic
        # Create broker
        self._broker = redis_broker

    async def load_ec_non_controllable_loads_forecast(
        self, start: datetime, stop: datetime, interval: int = 10
    ) -> Dict[str, Any]:
        """Uses the RPC to call the data engine and resquest the non controllable loads data."""
        # Make the RPC to retrieve the non-controllable loads forecast
        payload: dict[str, Any] = {
            "message": self._message_topic,
            "params": {
                "start": self._round_up_to_10_minutes(start.astimezone()).isoformat(),
                "stop": self._round_up_to_10_minutes(stop.astimezone()).isoformat(),
                "interval": interval,
            },
        }

        non_controllable_loads_forecast = await self._send_request(payload=payload, topic=self._get_state_request_topic)
        return non_controllable_loads_forecast

    async def _send_request(self, payload: Dict[str, Any], topic: str) -> DecodedMessage:
        await self._broker.connect()
        try:
            rpc_response_message = await self._broker.request(message=payload, channel=topic)

            logger.info("Sent device measurement request to the redis broker.")

            # Decode the response message
            decoded_response = await rpc_response_message.decode()
            return decoded_response
        except Exception as e:
            logger.error("Error publishing device function to broker: %s", e)
            raise
        finally:
            await self._broker.close()  # We need to close each time or else we get an event loop error

    # Function to round up to the nearest 10-minute interval
    def _round_up_to_10_minutes(self, dt: datetime) -> datetime:
        # Extract minutes and round up to the next 10-minute mark
        minutes = dt.minute
        remainder = minutes % 10
        if remainder == 0:
            return dt  # Already on a 10-minute mark
        minutes_to_add = 10 - remainder
        return (dt + timedelta(minutes=minutes_to_add)).replace(second=0, microsecond=0)
