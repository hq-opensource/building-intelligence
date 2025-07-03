from datetime import datetime, timedelta
from typing import Any, Dict

from faststream.redis import RedisBroker
from faststream.types import DecodedMessage

from common.database.redis import RedisClient
from common.util.logging import LoggingUtil


logger = LoggingUtil.get_logger(__name__)


class ForecastQueries:
    """A class to handle RPC queries for forecast data."""

    def __init__(self, redis_client: RedisClient, redis_broker: RedisBroker) -> None:
        """
        Initializes the ForecastQueries class.

        Args:
            redis_client (RedisClient): An instance of the Redis client.
            redis_broker (RedisBroker): An instance of the Redis broker.
        """
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
        """
        Uses RPC to request non-controllable loads data from the data engine.

        Args:
            start (datetime): The start time for the forecast.
            stop (datetime): The end time for the forecast.
            interval (int): The interval in minutes between data points.

        Returns:
            Dict[str, Any]: A dictionary containing the forecast data.
        """
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
        """
        Sends a request to the Redis broker and returns the response.

        Args:
            payload (Dict[str, Any]): The message payload.
            topic (str): The topic to publish the message to.

        Returns:
            DecodedMessage: The decoded response message.
        """
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

    def _round_up_to_10_minutes(self, dt: datetime) -> datetime:
        """
        Rounds up a datetime object to the nearest 10-minute interval.

        Args:
            dt (datetime): The datetime object to round up.

        Returns:
            datetime: The rounded up datetime object.
        """
        # Extract minutes and round up to the next 10-minute mark
        minutes = dt.minute
        remainder = minutes % 10
        if remainder == 0:
            return dt  # Already on a 10-minute mark
        minutes_to_add = 10 - remainder
        return (dt + timedelta(minutes=minutes_to_add)).replace(second=0, microsecond=0)
