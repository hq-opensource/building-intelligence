"""
This module provides functionality for detecting blackouts based on data interruptions
and managing the Grid Response and Protection (GRAP) state.
It interacts with InfluxDB for historical data, Redis for state management,
and uses a Redis broker for inter-service communication via RPC calls.
"""

import asyncio

from datetime import datetime, timedelta
from typing import Any, Dict, Tuple

import numpy as np

from faststream.redis import RedisBroker

from common.database.influxdb import InfluxManager
from common.database.redis import RedisClient
from common.util.logging import LoggingUtil


logger = LoggingUtil.get_logger(__name__)


class DetectBlackout:
    """
    A class responsible for detecting blackouts based on data interruptions
    and communicating this information via Redis and an RPC mechanism.
    """

    def __init__(
        self,
        influx_manager: InfluxManager,
        redis_client: RedisClient,
        broker: RedisBroker,
    ) -> None:
        """
        Initializes the DetectBlackout class with InfluxDB and Redis clients, and a Redis broker.

        Args:
            influx_manager (InfluxManager): An initialized InfluxDB manager instance.
            redis_client (RedisClient): An initialized Redis client instance.
            broker (RedisBroker): An initialized FastStream RedisBroker instance for RPC calls.
        """
        self._influx_manager = influx_manager
        self._redis_client = redis_client

        # Read labels for databases
        self._labels_influx = redis_client.safe_read_from_redis("influxdb_mapping")
        self._labels_redis = redis_client.safe_read_from_redis("labels_redis")
        self._labels_channels = redis_client.safe_read_from_redis("labels_channels")
        self._broker = broker

    def detect_blackout_info_locally(self) -> None:
        """
        Detects blackouts by checking for data interruptions in local InfluxDB.
        If a blackout is detected and the GRAP function
        has not been called previously, it saves blackout information to Redis
        and initiates an RPC call to activate the GRAP function.
        """
        # Verify if the system is executing a GRAP or not
        try:
            grap_info = self._redis_client.safe_read_from_redis(self._labels_redis["grap_info"])
        except Exception as e:
            logger.error("Grap info not found on redis. Error: %s", e)

        if grap_info is None:
            blackout_duration, blackout_stop = self._detect_last_data_interruption(min_gap_minutes=1)

            if blackout_duration is not None and blackout_duration > 30:
                # Save on Redis the information of the blackout
                blackout_info = {
                    "duration": blackout_duration,
                    "stop": blackout_stop.isoformat(),
                }
                self._redis_client.save_in_redis_with_expiration(
                    self._labels_redis["blackout_info"], blackout_info, blackout_duration * 60
                )

                # Read on redis if the GRAP function was called before or not
                try:
                    call_state = self._redis_client.safe_read_from_redis(self._labels_redis["grap_cold_pickup_call"])
                    print("e")
                except Exception:
                    logger.error("Grap was not called before")

                if call_state is None:
                    # Make an RPC to the power limit function to activate the GRAP
                    logger.info("Executing the RPC for the cold load pickup.")
                    # Update power limit
                    try:
                        grap_redis = self._redis_client.safe_read_from_redis("grid_service_grap")
                        grap_power_limit = grap_redis["grap_limit"]
                    except Exception:
                        logger.error("There is not a power limit stablished for the grap on RedisDB.")
                    # Build the message to request the GRAP
                    grap_request = blackout_info
                    grap_request["limit"] = grap_power_limit
                    asyncio.create_task(self._make_rpc_call(blackout_info))
                    logger.info("The blackout information was sent to the power limit grid service.")
                else:
                    logger.info("The cold load pickup was called previously, so, it will not be called again.")
            else:
                logger.info("No blackouts were detected.")
        else:
            logger.info(
                "The GRAP is already active. The system will not check actively for new blackouts until %s",
                grap_info["stop"],
            )

    def update_blackout_info_cloud(self) -> None:
        """
        Placeholder for future logic to communicate with a cloud service
        to verify and update blackout status and power limits.
        """
        pass

    def _detect_last_data_interruption(self, min_gap_minutes: int = 30) -> Tuple[datetime | None, datetime | None]:
        """
        Detects the last significant data interruption (blackout) in the 'net_power' measurement
        from InfluxDB. A gap is considered significant if it exceeds `min_gap_minutes`.

        Args:
            min_gap_minutes (int): The minimum duration in minutes for a data gap to be considered a blackout.
                                   Defaults to 30 minutes.

        Returns:
            Tuple[datetime | None, datetime | None]: A tuple containing the duration of the blackout in minutes
                                                     and the stop time of the blackout. Returns (None, None)
                                                     if no blackout is detected.
        """
        # Retrieve energy consumption
        bucket = self._labels_influx["net_power"]["bucket"]
        measurement = self._labels_influx["net_power"]["measurement"]
        tags = self._labels_influx["net_power"]["tags"]
        field = self._labels_influx["net_power"]["field"]
        fields = [field]

        # Extend tags to include measure
        tags["_type"] = "measure"

        # Fetch the data
        stop = datetime.now().astimezone()
        start = stop - timedelta(days=1)  # Adjust based on the desired period
        df = self._influx_manager.read(
            start=start.astimezone(),
            stop=stop.astimezone(),
            msname=measurement,
            fields=fields,
            bucket=bucket,
            tags=tags,
        )

        if df.empty:
            blackout_duration = None
            blackout_stop = None

        # Calculate time difference between consecutive timestamps
        time_diff = df.index.to_series().diff().dt.total_seconds() / 60  # Convert to minutes

        # Identify gap start and end points
        gaps = time_diff[time_diff > min_gap_minutes]
        if gaps.empty:
            blackout_duration = None
            blackout_stop = None
        else:
            # Get the start and end times of the last gap
            blackout_duration = np.around(gaps.iloc[-1], 2)
            blackout_stop = gaps.index[-1].to_pydatetime()
            logger.info("Blackout detected at %s with a duration of %s minutes", str(blackout_stop), blackout_duration)

        return blackout_duration, blackout_stop

    async def _make_rpc_call(self, blackout_info: Dict[str, Any]) -> None:
        """
        Makes an RPC (Remote Procedure Call) to the power limit function via the Redis broker.
        This function sends blackout information and expects a response, which it then logs
        and uses to update Redis with GRAP-related information.

        Args:
            blackout_info (Dict[str, Any]): A dictionary containing information about the detected blackout,
                                            which will be sent as parameters in the RPC request.
        """
        # Send an RPC request to the Redis event broker and wait for the response
        await self._broker.connect()  # We need to connect each time or else we get an event loop error
        # Define request

        request_body = {
            "method": self._labels_channels["grid_functions"]["cold_load_pickup"],
            "params": blackout_info,
        }
        topic = (
            self._labels_channels["grid_functions_prefix"] + self._labels_channels["grid_functions"]["cold_load_pickup"]
        )
        try:
            rpc_response_message = await self._broker.request(message=request_body, channel=topic)

            logger.info("Published grid function RPC to the redis broker.")

            # Decode the response message
            decoded_response = await rpc_response_message.decode()

            # Log response
            logger.info("The request for the GRAP received response: %s", decoded_response)

            # Save the RPC call
            self._redis_client.save_in_redis_with_expiration(
                self._labels_redis["grap_cold_pickup_call"],
                self._labels_redis["grap_called"],
                int(decoded_response["duration"]) * 60,
            )

            # Save on redis the grap information
            self._redis_client.save_in_redis_with_expiration(
                self._labels_redis["grap_info"],
                decoded_response,
                int(decoded_response["duration"]) * 60,
            )

        except Exception as e:
            logger.error("Error executing grid function broker publisher: %s", e)
            raise
        finally:
            await self._broker.close()  # We need to close each time or else we get an event loop error
