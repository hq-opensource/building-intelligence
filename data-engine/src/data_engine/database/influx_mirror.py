"""
This module provides the InfluxMirror class for synchronizing data from InfluxDB Cloud
to a local InfluxDB instance. It handles fetching measurements, fields, and historical data,
and then writing this data to the local database.
"""

import os
import time

from datetime import datetime, timedelta

import schedule

from common.database.influxdb import InfluxManager
from common.util.logging import LoggingUtil


logger = LoggingUtil.get_logger(__name__)


class InfluxMirror:
    """Class to mirror measurements from InfluxDB Cloud to a local InfluxDB instance."""

    def __init__(
        self,
        cloud_url: str = os.getenv("INFLUXDB_CLOUD_URL"),
        cloud_token: str = os.getenv("INFLUXDB_CLOUD_TOKEN"),
        cloud_org: str = os.getenv("INFLUXDB_CLOUD_ORG"),
        cloud_bucket: str = os.getenv("CLOUD_WEATHER_BUCKET"),
        local_url: str = os.getenv("INFLUXDB_URL"),
        local_token: str = os.getenv("INFLUXDB_TOKEN"),
        local_org: str = os.getenv("INFLUXDB_ORG"),
        local_bucket: str = os.getenv("LOCAL_INFLUX_BUCKET"),
    ) -> None:
        """
        Initializes the InfluxMirror with cloud and local InfluxDB connection details.

        Args:
            cloud_url (str): URL for the InfluxDB Cloud instance.
            cloud_token (str): Authentication token for InfluxDB Cloud.
            cloud_org (str): Organization name for InfluxDB Cloud.
            cloud_bucket (str): Default bucket name for InfluxDB Cloud.
            local_url (str): URL for the local InfluxDB instance.
            local_token (str): Authentication token for local InfluxDB.
            local_org (str): Organization name for local InfluxDB.
            local_bucket (str): Default bucket name for local InfluxDB.
        """
        self.cloud_manager = InfluxManager(cloud_url, cloud_org, cloud_token)
        self.local_manager = InfluxManager(local_url, local_org, local_token)
        self.default_cloud_bucket = cloud_bucket
        self.default_local_bucket = local_bucket

    def sync_all_measurements(self, cloud_bucket: str, local_bucket: str) -> None:
        """
        Fetches the last specified hours of data for all measurements from InfluxDB Cloud
        and writes them to a local InfluxDB instance.

        Args:
            cloud_bucket (str): The bucket name in InfluxDB Cloud to read from.
            local_bucket (str): The bucket name in local InfluxDB to write to.
        """
        now = datetime.now().astimezone()
        stop_time = now + timedelta(hours=130)
        start_time = now - timedelta(hours=5)
        logger.info("Starting sync process for bucket %s at %s", cloud_bucket, stop_time)

        measurements = self.cloud_manager.get_measurements_on_bucket(cloud_bucket)
        if not measurements:
            logger.warning("No measurements found in bucket %s", cloud_bucket)
            return

        total = len(measurements)
        for i, measurement in enumerate(measurements, 1):
            logger.info("Processing measurement %d/%d: %s", i, total, measurement)
            fields = self.cloud_manager.get_fields(cloud_bucket, measurement)
            if not fields:
                logger.warning("No fields found for measurement %s in bucket %s", measurement, cloud_bucket)
                continue

            # Get 20 days of historic data
            if measurement == "historic":
                start_time = now - timedelta(days=20)

            try:
                df = self.cloud_manager.read(
                    start=start_time,
                    stop=stop_time,
                    msname=measurement,
                    fields=fields,
                    bucket=cloud_bucket,
                    interval="10m",
                    agg_func="mean",
                )
                if df.empty:
                    logger.debug("No data for measurement %s", measurement)
                    continue

                self.local_manager.synchronous_write(
                    bucket=local_bucket, data=df, data_frame_measurement_name=measurement
                )
                logger.info("Synced measurement %s", measurement)
            except Exception as e:
                logger.error("Failed to sync measurement %s: %s", measurement, str(e))
                if "429" in str(e) or "too many requests" in str(e).lower():
                    logger.warning("Rate limit detected, pausing for 60 seconds")
                    time.sleep(60)  # Back off on rate limit
            finally:
                time.sleep(1)  # Throttle requests to avoid hitting limits

        logger.info("Completed sync for bucket %s at %s", cloud_bucket, datetime.now().astimezone())

    def run(self) -> None:
        """
        Schedules the sync task to run periodically.
        Performs an initial sync immediately and then schedules hourly syncs.
        """
        # Execute the first sync immediately
        logger.info("Running initial sync task")
        self.sync_all_measurements(cloud_bucket=self.default_cloud_bucket, local_bucket=self.default_local_bucket)

        logger.info("Scheduled sync task to run every hour")
        schedule.every().hour.at(":00").do(
            self.sync_all_measurements,
            cloud_bucket=self.default_cloud_bucket,
            local_bucket=self.default_local_bucket,
        )

        while True:
            schedule.run_pending()
            time.sleep(60)

    def __del__(self) -> None:
        """
        Closes the InfluxDB client connections when the InfluxMirror object is destroyed.
        Ensures proper resource cleanup.
        """
        self.cloud_manager._influx_client.close()
        self.local_manager._influx_client.close()


if __name__ == "__main__":
    mirror = InfluxMirror()
    mirror.run(test_mode=True)  # Set to False in production
