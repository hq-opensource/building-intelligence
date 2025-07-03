"""
This module handles RPC (Remote Procedure Call) answers related to forecaster requests.
It subscribes to forecast request topics, processes incoming requests,
and provides cached or newly computed forecasts for non-controllable loads.
It integrates with InfluxDB for data retrieval and Redis for caching and message brokering.
"""

import os

from datetime import datetime
from typing import Any, Dict

from faststream import Context
from faststream.redis import RedisRouter

from common.database.influxdb import InfluxManager
from common.database.redis import RedisClient
from common.util.logging import LoggingUtil
from data_engine.forecaster.forecast_retriever import ForecastRetriever


# Configure and start the logger
logger = LoggingUtil.get_logger(__name__)
logger.info("The Broker stream is starting at %s:", str(datetime.now().astimezone()))


# region to initialize InfluxDB, RedisDB, and Event broker
# Create the redis client
redis_password = os.getenv("REDIS_PASSWORD")
redis_host = os.getenv("REDIS_HOST")
redis_port = os.getenv("REDIS_PORT")

# Create the redis client
redis_client = RedisClient(redis_host, redis_port, redis_password)
labels_channels = redis_client.safe_read_from_redis("labels_channels")

# Data for the local Influx
influxdb_url = os.getenv("INFLUXDB_URL")
influxdb_org = os.getenv("INFLUXDB_ORG")
influxdb_token = os.getenv("INFLUXDB_TOKEN")
influx_manager = InfluxManager(influxdb_url, influxdb_org, influxdb_token)

# Redis event broker setup
forecast_router = RedisRouter(prefix=labels_channels["forecaster_prefix"])

# Define topics
forecast_request_topic = labels_channels["non_controllable_loads"]
# endregion to initialize InfluxDB, RedisDB, and Event broker


# Subscription to receive forecast requests and publish confirmation
@forecast_router.subscriber(forecast_request_topic)
async def non_controllable_loads_forecast_request(
    forecast_confirmation_request: Dict,
    broker: Any = Context(),  # noqa: B008
) -> Dict[str, Any]:
    """
    Handles incoming forecast requests for non-controllable loads.

    This function acts as a subscriber to the `forecast_request_topic`.
    It first checks if a cached forecast exists that matches the requested parameters.
    If a valid cached forecast is found, it is returned immediately.
    Otherwise, it computes a new forecast using the `ForecastRetriever`,
    caches the result, and then returns it.

    Args:
        forecast_confirmation_request (Dict): A dictionary containing the forecast request details,
                                              including a "message" and "params" (start, stop, interval).
        broker (Any): The FastStream broker context, used for connecting before publishing.

    Returns:
        Dict[str, Any]: A dictionary containing the forecast results or an error message
                        if the request message does not match expectations.
    """
    logger.info("Received forecast request: %s", forecast_confirmation_request)
    # Connect the broker before publishing
    await broker.connect()

    # Check if the request matches the expected command
    if forecast_confirmation_request["message"] == forecast_request_topic:
        # Check Redis for cached forecast
        serialized_cached_forecast = None
        try:
            cached_forecast = redis_client.safe_read_from_redis("day_ahead_forecast_cache")
            if (
                forecast_confirmation_request["params"]["start"] == cached_forecast["start"]
                and forecast_confirmation_request["params"]["stop"] == cached_forecast["stop"]
                and forecast_confirmation_request["params"]["interval"] == cached_forecast["interval"]
            ):
                serialized_cached_forecast = cached_forecast
                logger.info("A non controllable loads forecast already exists, returning cached response.")
            else:
                logger.info(
                    "A non controllable loads forecast exists, but the dates do not match. Computing forecast again."
                )
        except Exception as e:
            logger.error("Failed to retrieve cached forecast: %s", e)

        if serialized_cached_forecast:
            logger.info("Answering RPC with cached forecasts.")
            forecast_message = serialized_cached_forecast
            return forecast_message
        else:
            # Compute the forecast (using data engine capabilities)
            start = forecast_confirmation_request["params"]["start"]
            stop = forecast_confirmation_request["params"]["stop"]
            interval = forecast_confirmation_request["params"]["interval"]
            forecast_retriever = ForecastRetriever()
            forecast_results = forecast_retriever.non_controllable_loads_forecast(start, stop, interval)
            forecast_response = {"start": start, "stop": stop, "interval": interval, "forecast": forecast_results}

            redis_client.save_in_redis_with_expiration("day_ahead_forecast_cache", forecast_response, 86400)

            logger.info("Answering RPC with the non controllable loads forecast.")
            return forecast_response
    else:
        logger.warning(
            "The message %s on the topic %s does not return the non_controllable_loads_forecast.",
            forecast_confirmation_request["message"],
            forecast_request_topic,
        )
        logger.warning(
            "If you want the non_controllable_loads_forecast, use the message: %s instead on the topic %s.",
            labels_channels["non_controllable_loads_forecast"],
            forecast_request_topic,
        )
    received_message = forecast_confirmation_request["message"]
    error_message = (
        f"message {received_message} does not trigger the non_controllable_loads_forecast. Use proper message."
    )
    return {"content": error_message}
