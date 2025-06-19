import os

from datetime import datetime
from time import sleep
from typing import Any, Dict

from faststream import Context
from faststream.redis import RedisRouter

from common.database.influxdb import InfluxManager
from common.database.redis import RedisClient
from common.util.logging import LoggingUtil
from data_engine.database.RetrieveDataForCloud import RetrieveDataForCloud


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
forecast_request_topic = labels_channels["forecast_request"]

# endregion to initialize InfluxDB, RedisDB, and Event broker

logger = LoggingUtil.get_logger(__name__)


# Subscription to receive forecast requests and publish confirmation
@forecast_router.subscriber(forecast_request_topic)
async def send_telemetry_periodically(forecast_confirmation_request: dict, broker=Context()) -> Dict[str, Any]:  # noqa: B008
    """Handles the forecast request and sends confirmation upon completion."""
    logger.info("Received forecast request: %s", forecast_confirmation_request)
    # Connect the broker before publishing
    await broker.connect()


def send_telemetry_periodically(retriever: RetrieveDataForCloud, interval: int = 30) -> None:
    """Function to send telemetry data periodically."""
    while True:
        telemetry = retriever.retrieve_all_data(start_range=interval * -1)
        # TODO fix this
        device.send_telemetry_data(telemetry)
        sleep(interval)
