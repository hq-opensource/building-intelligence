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
    Retrieves data from the database.
    """

    def __init__(
        self,
        influx_manager: InfluxManager,
        redis_client: RedisClient,
        broker: RedisBroker,
    ) -> None:
        self._influx_manager = influx_manager
        self._redis_client = redis_client

        # Read labels for databases
        self._labels_influx = redis_client.safe_read_from_redis("influxdb_mapping")
        self._labels_redis = redis_client.safe_read_from_redis("labels_redis")
        self._labels_channels = redis_client.safe_read_from_redis("labels_channels")
        self._broker = broker

    def detect_blackout_info_locally(self) -> None:
        """
        Makes the detection of a blackout.
        Saves on Redis a variable specifying the GRAP state.
        Takes as input the power limit measured on kWs.
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
        # TODO: Create logic to talk to the cloud and verify state and power limit
        pass

    def _detect_last_data_interruption(self, min_gap_minutes: int = 30) -> Tuple[datetime | None, datetime | None]:
        """
        Detects gaps in data timestamps where the gap is greater than `min_gap_minutes`.
        Returns the start and end times of the last gap found.
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
        """Make and RPC to the power limit function."""
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
