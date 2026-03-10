"""
Device Scheduler Module

This module provides implementation for device-specific scheduling functionality.
It bridges device management with the scheduling system to control device behavior
based on time-based events.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import pandas as pd
import pytz

from common.database.influxdb import InfluxManager
from common.database.redis import RedisClient
from common.device.helper import DeviceHelper
from common.util.logging import LoggingUtil
from core_api.schedule.models import AbstractScheduler, ScheduleEventData


logger = LoggingUtil.get_logger(__name__)


class DeviceScheduler(AbstractScheduler):
    """
    Device-specific scheduler implementation.

    This class manages schedules for individual devices, handling the storage,
    retrieval, and application of schedule data for device control operations.
    It interfaces with InfluxDB for persistence and Redis for configuration.
    """

    def __init__(
        self,
        device_id: str,
        control_type: str,
        redis_client: RedisClient,
        influx_manager: InfluxManager,
        labels_influx: Dict[str, Any],
        devices: Dict[str, Any],
        time_step_duration_in_seconds: int = 60,
    ) -> None:
        """
        Initialize the device scheduler.

        Args:
            device_id: Unique identifier for the device
            control_type: Type of control strategy to apply
            redis_client: Redis client for retrieving configurations
            influx_manager: InfluxDB manager for data operations
            time_step_duration_in_seconds: Time step granularity in seconds (default: 60)
        """

        self._device_id = device_id
        self._control_type = control_type
        self._influx_manager = influx_manager
        self._redis_client = redis_client
        self._labels_influx = labels_influx
        self._devices = devices
        self._time_step_duration_in_seconds = time_step_duration_in_seconds

        # Configure InfluxDB bucket
        self._bucket = self._labels_influx["bucket_user_data"]

    def get_event_data(self, time_target: datetime) -> Optional[ScheduleEventData]:
        """
        Retrieve scheduled event data for a specified time.

        Args:
            time_target: Target timestamp for retrieving scheduled data

        Returns:
            ScheduleEventData object if an event is found, None otherwise
        """

        # Check timezone
        if time_target.tzinfo is None:
            time_target = pytz.UTC.localize(time_target)

        # 1. Step 1: Check for changes in the last 60 seconds
        logger.debug(f"Step 1: Checking for control changes at {time_target} for device {self._device_id}")
        time_limit_60s = time_target - timedelta(seconds=self._time_step_duration_in_seconds)
        event_data = self._query_event_data(time_target, time_limit_60s, time_target)

        if event_data:
            return event_data

        # 2. Step 2: Fallback to the most recent 10-minute interval (staircase interpolation)
        # Round down to the nearest 10-minute mark (00, 10, 20, 30, 40, 50)
        minutes = (time_target.minute // 10) * 10
        time_10m = time_target.replace(minute=minutes, second=0, microsecond=0)

        # Avoid redundant query if time_target was already a 10m mark and we just checked it
        if time_10m == time_target:
            return None

        logger.debug(f"Step 2: No recent changes. Falling back to 10m interval at {time_10m} for device {self._device_id}")
        return self._query_event_data(time_10m, time_10m, time_10m)

    def _query_event_data(
        self, time_target: datetime, time_limit: datetime, time_range_end: datetime
    ) -> Optional[ScheduleEventData]:
        """
        Query InfluxDB to retrieve schedule event data within the specified time window.

        Args:
            time_target: Target timestamp for priority selection
            time_limit: Lower boundary of time window
            time_range_end: Upper boundary of time window (inclusive)

        Returns:
            ScheduleEventData if an event is found, None otherwise
        """

        self._influx_manager.get_buckets_api()

        # We look around the target time to find the points
        # Influx range is exclusive on stop, so we add a tiny bit
        time_windows_start = time_limit - timedelta(seconds=10)
        time_windows_end = time_range_end + timedelta(seconds=1)

        # Build Flux query
        # We filter for r._time >= timeLimit and r._time <= time_range_end
        # This allows finding an exact point if timeLimit == time_range_end
        query = f'''
        import "strings"
        from(bucket:"{self._bucket}")
          |> range(start: {time_windows_start.isoformat()}, stop: {time_windows_end.isoformat()})
          |> filter(fn: (r) => r["_type"] == "control")
          |> filter(fn: (r) => strings.hasSuffix(v: r["_field"], suffix: "{self._device_id}"))
          |> map(fn: (r) => ({{ r with priority_int: int(v: r.priority) }}))
          |> filter(fn: (r) => r._time >= {time_limit.isoformat()} and r._time <= {time_range_end.isoformat()})
          |> group(columns: ["_field"])
          |> top(n: 1, columns: ["priority_int","_time"])
        '''

        # Execute query
        query_api = self._influx_manager.get_query_api()
        result = query_api.query(query)

        # Process result
        if not result or len(result) == 0:
            return None

        for table in result:
            for record in table.records:
                field = record.get_time().isoformat()
                value = record.get_value()

                # Check if from_direct_control exists in record and convert to boolean
                from_direct_control = False
                if record["from_direct_control"]:
                    # Convert string '0' or '1' to boolean
                    from_direct_control = record["from_direct_control"] == "1"

                return ScheduleEventData(event_id=field, data=value, from_direct_control=from_direct_control)

        return None

    @classmethod
    def save_schedule(
        cls,
        priority: int,
        dispatches: Dict[str, Dict[datetime, float]],
        redis_client: RedisClient,
        influx_manager: InfluxManager,
        from_direct_control: bool = False,
    ) -> None:
        """
        Save device schedules to InfluxDB.

        Args:
            priority: Priority level for the schedule (higher values take precedence)
            dispatches: Dictionary mapping device IDs to their schedule (timestamp → value)
            redis_client: Redis client for configuration access
            influx_manager: InfluxDB manager for database operations
            from_direct_control: Flag indicating if schedule came from direct control (default: False)
        """

        # Initialize configurations
        labels_influx = redis_client.safe_read_from_redis("influxdb_mapping")
        devices = redis_client.safe_read_from_redis("user_devices")

        # Process each device
        for device_id, dispatch in dispatches.items():
            try:
                # Check that device exists
                if not DeviceHelper.device_exists(devices, device_id):
                    logger.error(f"Device with entity_id {device_id} is not installed on the building.")
                    continue

                # Get device type
                device_type = DeviceHelper.get_all_values_by_filtering_devices(
                    device_list=devices, filter_key="entity_id", filter_value=device_id, target_key="type"
                )[0]

                # Convert data to DataFrame
                df = cls._prepare_dataframe(dispatch)

                # Write data according to device type
                cls._write_schedule_for_device_type(
                    device_type,
                    device_id,
                    priority,
                    df,
                    influx_manager,
                    labels_influx,
                    from_direct_control=from_direct_control,
                )

            except Exception as e:
                logger.error(f"Error when saving for device {device_id}: {str(e)}")

    @staticmethod
    def _prepare_dataframe(dispatch: Dict[datetime, float]) -> pd.DataFrame:
        """
        Convert a schedule dispatch dictionary to a properly formatted DataFrame.

        Args:
            dispatch: Dictionary mapping timestamps to control values

        Returns:
            Pandas DataFrame with timestamp index and value column
        """

        df = pd.DataFrame(list(dispatch.items()), columns=["timestamp", "value"])
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.set_index("timestamp", inplace=True)

        return df

    @staticmethod
    def _write_schedule_for_device_type(
        device_type: str,
        device_id: str,
        priority: int,
        data: pd.DataFrame,
        influx_manager: InfluxManager,
        labels_influx: Dict[str, Any],
        from_direct_control: bool = False,
    ) -> None:
        """
        Write schedule data to InfluxDB according to device type specifications.

        Args:
            device_type: Type of device (heating, storage, etc.)
            device_id: Device identifier
            priority: Priority level of the schedule
            data: DataFrame containing schedule data
            influx_manager: InfluxDB manager for database operations
            labels_influx: InfluxDB field and measurement mappings
            from_direct_control: Flag indicating if schedule came from direct control (default: False)
        """

        # Configuration for each device type
        if device_type == DeviceHelper.SPACE_HEATING.value:
            config = labels_influx["sh_setpoint"]
            field_name = config["field"] + device_id
        elif device_type == DeviceHelper.ON_OFF_EV_CHARGER.value:
            config = labels_influx["ev_charger_net_power"]
            field_name = config["field"] + "_" + device_id
        elif device_type == DeviceHelper.ELECTRIC_VEHICLE_V1G.value:
            config = labels_influx["v1g_net_power"]
            field_name = config["field"] + "_" + device_id
        elif device_type == DeviceHelper.ELECTRIC_VEHICLE_V2G.value:
            config = labels_influx["v2g_net_power"]
            field_name = config["field"] + "_" + device_id
        elif device_type == DeviceHelper.ELECTRIC_STORAGE.value:
            config = labels_influx["eb_net_power"]
            field_name = config["field"] + "_" + device_id
        elif device_type == DeviceHelper.WATER_HEATER.value:
            config = labels_influx["wh_power"]
            field_name = config["field"] + "_" + device_id
        elif device_type == DeviceHelper.THERMAL_STORAGE.value:
            config = labels_influx["ts_power"]
            field_name = config["field"] + "_" + device_id
        else:
            logger.warning(f"Unsupported device type: {device_type}")
            return

        # Rename value column according to InfluxDB field
        data.rename(columns={"value": field_name}, inplace=True)

        # Prepare tags
        tags = dict(config["tags"])
        tags["priority"] = str(priority)
        tags["_type"] = "control"
        tags["from_direct_control"] = str(int(from_direct_control))

        # Write to InfluxDB
        with influx_manager.get_write_api(tags) as write_api:
            write_api.write(
                bucket=config["bucket"],
                record=data,
                data_frame_measurement_name=config["measurement"],
            )
