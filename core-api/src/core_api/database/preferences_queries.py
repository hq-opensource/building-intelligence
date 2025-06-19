from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Optional

import pandas as pd

from common.database.influxdb import InfluxManager
from common.database.redis import RedisClient
from common.util.logging import LoggingUtil
from core_api.schedule.models import PreferenceType, ScheduleEventData
from core_api.schedule.monitor import SchedulerMonitor


logger = LoggingUtil.get_logger(__name__)


class PreferencesError(Exception):
    """Base class for preference errors."""

    pass


class PreferencesQueriesNoDataFoundError(PreferencesError):
    """Raised when no data is found."""

    pass


class PreferencesInvalidSamplingError(PreferencesError):
    """Raised when the sampling interval is invalid."""

    pass


@dataclass
class WaterHeaterEvent:
    """Data structure for water heater events."""

    time: time
    volume: float
    rate: float


def _adjust_to_next_datetime_of_sampling_in_minutes(date: datetime, sampling_in_minutes: int) -> datetime:
    """Adjusts a date to the next sampling interval.

    Args:
        date: Date to adjust
        sampling_in_minutes: Sampling interval in minutes

    Returns:
        datetime: Adjusted date
    """
    adjustment = (
        ((date.minute + (sampling_in_minutes - 1)) // sampling_in_minutes) * sampling_in_minutes
    ) - date.minute

    return date + timedelta(minutes=adjustment)


class PreferencesQueries:
    """Class to manage preference queries for different devices.

    This class provides methods to load different types of preferences
    from an InfluxDB database and Redis.
    """

    MIN_SAMPLING_MINUTES = 1
    MAX_SAMPLING_MINUTES = 60

    def __init__(self, influx_manager: InfluxManager, redis_client: RedisClient) -> None:
        """
        Args:
            influx_manager: InfluxDB database manager
            redis_client: Redis client
        """
        self._influx_manager = influx_manager
        self._redis_client = redis_client
        self._labels_redis = redis_client.safe_read_from_redis("labels_redis")

    def load_preferences(
        self, device_id: str, start: datetime, stop: datetime, preference_type: PreferenceType, sampling_in_minutes: int
    ) -> pd.DataFrame:
        """Loads preferences for a specific device.

        Args:
            device_id: Unique identifier of the device
            start: Start date
            stop: End date
            preference_type: Type of preference to load
            sampling_in_minutes: Sampling interval in minutes

        Returns:
            DataFrame containing the preference data

        Raises:
            PreferencesInvalidSamplingError: If the sampling interval is invalid
            PreferencesQueriesNoDataFoundError: If no data is found
        """

        if sampling_in_minutes < 1 or sampling_in_minutes > 60:
            raise ValueError("Sampling interval must be between 1 and 60 minutes.")

        logger.debug("Starting to load preferences for device %s, type %s", device_id, preference_type)

        monitor = SchedulerMonitor(
            redis_client=self._redis_client,
            influx_manager=self._influx_manager,
        )

        start_date = _adjust_to_next_datetime_of_sampling_in_minutes(start, sampling_in_minutes).replace(
            second=0,
            microsecond=0,
        )
        end_date = _adjust_to_next_datetime_of_sampling_in_minutes(stop, sampling_in_minutes).replace(
            second=0,
            microsecond=0,
        )

        date_range = pd.date_range(
            start=start_date,
            end=end_date,
            freq=f"{sampling_in_minutes}min",
        )

        data: list[float] = []
        for timestep in date_range:
            event_data: Optional[ScheduleEventData] = monitor.get_device_event_data(
                device_id, preference_type, timestep
            )
            if event_data:
                data.append(event_data.data)

        if not data:
            error_msg = f"No {preference_type} data found for {device_id} between {start} and {stop}."
            logger.error(error_msg)
            raise PreferencesQueriesNoDataFoundError(error_msg)

        logger.debug(
            "Preferences successfully loaded for device %s, type %s: %d data points",
            device_id,
            preference_type,
            len(data),
        )
        return pd.DataFrame({"timestamp": date_range, "data": data})

    def load_comfort_setpoints(
        self, device_id: str, start: datetime, stop: datetime, sampling_in_minutes: int
    ) -> pd.DataFrame:
        """Loads comfort setpoints preferences."""
        return self.load_preferences(device_id, start, stop, PreferenceType.PREFERENCES_SETPOINT, sampling_in_minutes)

    def load_electric_battery_soc_preferences(
        self, device_id: str, start: datetime, stop: datetime, sampling_in_minutes: int
    ) -> pd.DataFrame:
        """Loads electric battery state of charge preferences."""
        return self.load_preferences(device_id, start, stop, PreferenceType.PREFERENCES_SOC, sampling_in_minutes)

    def load_occupancy_preferences(
        self, device_id: str, start: datetime, stop: datetime, sampling_in_minutes: int
    ) -> pd.DataFrame:
        """Loads occupancy preferences."""
        return self.load_preferences(device_id, start, stop, PreferenceType.PREFERENCES_OCCUPANCY, sampling_in_minutes)

    def load_vehicle_branched_preferences(
        self, device_id: str, start: datetime, stop: datetime, sampling_in_minutes: int
    ) -> pd.DataFrame:
        """Loads vehicle branched preferences."""
        return self.load_preferences(device_id, start, stop, PreferenceType.PREFERENCES_BRANCHED, sampling_in_minutes)

    def load_vehicle_soc_preferences(
        self, device_id: str, start: datetime, stop: datetime, sampling_in_minutes: int
    ) -> pd.DataFrame:
        """Loads vehicle state of charge preferences."""
        return self.load_preferences(device_id, start, stop, PreferenceType.PREFERENCES_SOC, sampling_in_minutes)

    def _get_last_occurrence_of_time(self, reference_datetime: datetime, hour: int, minute: int) -> datetime:
        """Calculates the last occurrence of a specific time relative to a reference datetime.

        Args:
            reference_datetime: Reference datetime to calculate from
            hour: Hour (0-23) to find last occurrence of
            minute: Minute (0-59) to find last occurrence of

        Returns:
            datetime: Most recent occurrence of the specified time that is <= reference_datetime
        """
        target_time = reference_datetime.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return target_time if reference_datetime >= target_time else target_time - timedelta(days=1)

    def load_water_heater_consumption_preferences(
        self, device_id: str, start: datetime, stop: datetime, sampling_in_minutes: int
    ) -> pd.DataFrame:
        """Loads water heater consumption preferences.

        Args:
            device_id: Water heater identifier
            start: Start date
            stop: End date
            sampling_in_minutes: Sampling interval

        Returns:
            DataFrame with consumption data

        Raises:
            PreferencesInvalidSamplingError: If the sampling interval is invalid
            PreferencesQueriesNoDataFoundError: If no data is found or scheduler is not found
            PreferencesError: For other unexpected errors
        """
        logger.debug("Starting to load water heater consumption preferences for device %s", device_id)

        if sampling_in_minutes < 1 or sampling_in_minutes > 60:
            raise ValueError("Sampling interval must be between 1 and 60 minutes.")

        try:
            start_date = _adjust_to_next_datetime_of_sampling_in_minutes(start, sampling_in_minutes).replace(
                second=0,
                microsecond=0,
            )
            end_date = _adjust_to_next_datetime_of_sampling_in_minutes(stop, sampling_in_minutes).replace(
                second=0,
                microsecond=0,
            )

            date_range = pd.date_range(
                start=start_date,
                end=end_date,
                freq="1min",
            )

            monitor = SchedulerMonitor(
                redis_client=self._redis_client,
                influx_manager=self._influx_manager,
            )

            scheduler = monitor.get_device_scheduler(device_id, PreferenceType.PREFERENCES_WATER_HEATER_CONSUMPTION)

            if not scheduler:
                error_msg = f"No {PreferenceType.PREFERENCES_WATER_HEATER_CONSUMPTION} scheduler found for {device_id}."
                logger.error(error_msg)
                raise PreferencesQueriesNoDataFoundError(error_msg)

            data: list[float] = []
            for timestep in date_range:
                event = scheduler.get_event(timestep)
                if event:
                    event_datetime = self._get_last_occurrence_of_time(timestep, event.time.hour, event.time.minute)
                    volume: float = event.data["volume"]
                    rate: float = event.data["rate"]
                    consumed_volume: float = max(0, rate * (timestep - event_datetime).total_seconds() / 60)
                    consumption_during_timestep: float = rate
                    residual_volume: float = max(0.0, volume - consumed_volume)
                    data.append(min(consumption_during_timestep, residual_volume))

            if not data:
                error_msg = f"""No {PreferenceType.PREFERENCES_WATER_HEATER_CONSUMPTION} data found for {device_id} between {start}
                and {stop}."""
                logger.error(error_msg)
                raise PreferencesQueriesNoDataFoundError(error_msg)

            data_adapted_to_sampling_interval: pd.DataFrame = (
                pd.DataFrame({"timestamp": date_range, "data": data})
                .set_index("timestamp")
                .resample(f"{sampling_in_minutes}min")
                .sum()
                .reset_index()
            )

            logger.debug(
                "Water heater preferences successfully loaded for device %s: %d data points", device_id, len(data)
            )
            return data_adapted_to_sampling_interval

        except PreferencesError as e:
            logger.error("Unexpected error loading water heater preferences: %s", str(e))
            raise
