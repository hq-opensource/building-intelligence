from influxdb_client import BucketRetentionRules, InfluxDBClient

from common.database.redis import RedisClient
from common.util.logging import LoggingUtil


logger = LoggingUtil.get_logger(__name__)


class InfluxInit:
    """
    Initialize the profiles required to execute the optimization logic for a real user.
    """

    def __init__(self, url: str, org: str, token: str, redis_client: RedisClient) -> None:
        # Create self parameters
        self._redis_client = redis_client
        self._influx_client = InfluxDBClient(url=url, token=token, org=org, timeout=30000)

        # Read labels
        self._labels_influx = redis_client.safe_read_from_redis("influxdb_mapping")

    def create_simulation_buckets_for_influx(self) -> None:
        """
        Creates the buckets in influx to store future information."""
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
