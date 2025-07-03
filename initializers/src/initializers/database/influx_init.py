"""
This module provides the `InfluxInit` class for initializing InfluxDB.

It handles the connection to an InfluxDB instance and the creation of
necessary buckets for storing weather and user simulation data,
leveraging Redis for configuration labels.
"""

from influxdb_client import BucketRetentionRules, InfluxDBClient

from common.database.redis import RedisClient
from common.util.logging import LoggingUtil


logger = LoggingUtil.get_logger(__name__)


class InfluxInit:
    """
    Initializes InfluxDB client and creates necessary buckets for storing simulation and weather data.

    This class handles the setup of InfluxDB, including connecting to the database
    and ensuring that required data buckets (for weather and user simulation data)
    are present. It leverages Redis to retrieve InfluxDB mapping labels.
    """

    def __init__(self, url: str, org: str, token: str, redis_client: RedisClient) -> None:
        """
        Initializes the InfluxInit class with connection details and a Redis client.

        Args:
            url (str): The URL of the InfluxDB instance.
            org (str): The organization name for InfluxDB.
            token (str): The authentication token for InfluxDB.
            redis_client (RedisClient): An instance of RedisClient to retrieve InfluxDB mapping labels.
        """
        # Create self parameters
        self._redis_client = redis_client
        self._influx_client = InfluxDBClient(url=url, token=token, org=org, timeout=30000)

        # Read labels
        self._labels_influx = redis_client.safe_read_from_redis("influxdb_mapping")

    def create_simulation_buckets_for_influx(self) -> None:
        """
        Creates the necessary InfluxDB buckets for weather and user simulation data.

        This method checks if the specified buckets (defined in `_labels_influx`)
        already exist. If not, it creates them with an expiration rule of 0 (no expiration).
        Logs information about bucket creation or if they already exist.
        """
        logger.info("Creating Influx buckets...")
        # Initiate the buckets api and define retention rules
        buckets_api = self._influx_client.buckets_api()
        retention_rules = BucketRetentionRules(type="expire", every_seconds=0)

        # Create bucket for the weather
        if buckets_api.find_bucket_by_name(self._labels_influx["bucket_weather"]) is None:
            buckets_api.create_bucket(
                bucket_name=self._labels_influx["bucket_weather"], retention_rules=retention_rules
            )
            logger.debug("Bucket %s created", self._labels_influx["bucket_weather"])
        else:
            logger.warning("Bucket with name %s already exists.", self._labels_influx["bucket_weather"])

        # Create bucket for the simulation
        if buckets_api.find_bucket_by_name(self._labels_influx["bucket_user_data"]) is None:
            buckets_api.create_bucket(
                bucket_name=self._labels_influx["bucket_user_data"], retention_rules=retention_rules
            )
            logger.debug("Bucket %s created", self._labels_influx["bucket_user_data"])
        else:
            logger.warning("Bucket with name %s already exists.", self._labels_influx["bucket_user_data"])
