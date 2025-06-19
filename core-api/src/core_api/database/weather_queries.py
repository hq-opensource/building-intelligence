import os

from datetime import datetime, timedelta
from typing import Any, Dict, List

import pandas as pd

from numpy import around
from pandas import DataFrame

from common.database.influxdb import InfluxManager
from common.database.redis import RedisClient
from common.util.logging import LoggingUtil
from core_api.api.models import WeatherForecastType, WeatherHistoricType


logger = LoggingUtil.get_logger(__name__)


class WeatherQueries:
    def __init__(
        self,
        influx_manager: InfluxManager,
        redis_client: RedisClient,
    ) -> None:
        self._influx_manager = influx_manager
        self._redis_client = redis_client
        # Read labels for databases
        self._labels_influx = redis_client.safe_read_from_redis("influxdb_mapping")

    def retrieve_weather_forecast(
        self, start: datetime, stop: datetime, variable: WeatherForecastType, interval: int = 10
    ) -> Dict[str, Any]:
        """Retrieves the forecast of the external temperature between start and stop times."""

        # Ensure timezone-aware current time
        now = datetime.now().astimezone().replace(second=0, microsecond=0)

        # Validate start and stop times
        if start < now:
            message = f"Start time {start} must be in the future (now: {now})"
            logger.error(message)
            raise ValueError(message)
        if stop < now:
            message = f"Stop time {stop} must be in the future (now: {now})"
            logger.error(message)
            raise ValueError(message)
        if start >= stop:
            message = f"Start time {start} must be before stop time {stop}"
            logger.error(message)
            raise ValueError(message)
        max_future = now + timedelta(hours=120)
        if stop > max_future:
            message = f"Stop time {stop} cannot be more than 120 hours into the future (max: {max_future})"
            logger.error(message)
            raise ValueError(message)

        # Bucket and field setup
        bucket = self._labels_influx["temperature"]["bucket"]

        # Retrieve all possible weather types
        fields = [variable.value]

        # Define hour offsets
        start_offset = 0  # Previous hour before start
        stop_offset = 100  # Few hours after stop

        # Build list of measurements (e.g., forecast_000 to forecast_119)
        measurements = []
        for forecast_measurement in range(start_offset, stop_offset):
            measurements.append(f"forecast_{str(forecast_measurement).zfill(3)}")
        logger.debug("Querying measurements: %s", measurements)

        # Query InfluxDB for each measurement
        weather_dfs: List[DataFrame] = []
        for measurement in measurements:
            try:
                df = self._influx_manager.read(
                    start=start - timedelta(hours=120),  # Be sure forecast 000 exists.
                    stop=stop + timedelta(hours=120),
                    msname=measurement,
                    fields=fields,
                    bucket=bucket,
                )
                if not df.empty:
                    # Take only the last row on the dataframe
                    df_last = df.tail(1)
                    # Convert timezone
                    df_last.index = df_last.index.tz_convert(os.getenv("TZ"))
                    # Append to the list
                    weather_dfs.append(df_last)
                    logger.debug("Retrieved data for measurement %s", measurement)
                else:
                    logger.warning("No data found for measurement %s", measurement)
            except Exception as e:
                logger.error("Failed to query measurement %s: %s", measurement, e)

        # Combine results into a single DataFrame
        if not weather_dfs:
            logger.warning("No data retrieved from InfluxDB for the specified range")
            return pd.DataFrame()

        weather_query = pd.concat(weather_dfs).sort_index()
        logger.debug("Combined %d DataFrames into a single query result", len(weather_dfs))

        # Perform sampling and interpolation
        if not weather_query.empty:
            # Resample data
            weather = (
                weather_query.resample(f"{interval}min").mean().interpolate(method="linear", limit_direction="forward")
            )
            logger.debug("Resampled data to %d-minute intervals", interval)
            # Limit reponse to the requested timeframe
            start_filter = self._round_up_to_10_minutes(start)
            stop_filter = self._round_up_to_10_minutes(stop)

            # Ensure datetime index and convert filters if necessary
            logger.debug("Ensuring weather DataFrame has a datetime index...")
            try:
                if not isinstance(weather.index, pd.DatetimeIndex):
                    weather.index = pd.to_datetime(weather.index)
                    logger.debug("Weather df looks like this: %s", weather.head(3))
                    logger.debug("Converted weather index to DatetimeIndex.")

                # Align timezones
                if start_filter.tzinfo is not None and weather.index.tzinfo is None:
                    logger.debug("Localizing weather index to match filter timezone.")
                    weather.index = weather.index.tz_localize(start_filter.tzinfo)
                elif start_filter.tzinfo is not None and weather.index.tzinfo != start_filter.tzinfo:
                    logger.debug("Converting weather index to match filter timezone.")
                    weather.index = weather.index.tz_convert(start_filter.tzinfo)

                logger.debug("Start filter (rounded): %s", str(start_filter))
                logger.debug("Stop filter (rounded): %s", str(stop_filter))

                logger.debug("Filtering rows after or equal to start_filter...")
                weather_after_start = weather[weather.index >= start_filter]
                logger.debug("Remaining rows after start_filter: %d", len(weather_after_start))

                logger.debug("Filtering rows before or equal to stop_filter...")
                filtered_weather = weather_after_start[weather_after_start.index <= stop_filter]
                logger.debug("Remaining rows after stop_filter: %d", len(filtered_weather))

                logger.debug("Final filtered_weather dataframe head:\n%s", filtered_weather.head())

            except Exception as e:
                logger.error("Error during filtering weather data: %s", str(e))
                raise

            # Build the weather dictionary
            weather_dict = filtered_weather.rename_axis("timestamp").reset_index()
            weather_dict["timestamp"] = weather_dict["timestamp"].astype(str)
            weather_dict = dict(
                zip(
                    weather_dict["timestamp"],
                    around(weather_dict[fields[0]], 1),
                    strict=False,
                )
            )
            logger.debug("Response converted to dictionary.")
        else:
            logger.error("Failed to build weather dataframe.")
            weather_dict = {}

        return weather_dict

    # Function to round up to the nearest 10-minute interval
    def _round_up_to_10_minutes(self, dt: datetime) -> datetime:
        # Extract minutes and round up to the next 10-minute mark
        minutes = dt.minute
        remainder = minutes % 10
        if remainder == 0:
            return dt  # Already on a 10-minute mark
        minutes_to_add = 10 - remainder
        return (dt + timedelta(minutes=minutes_to_add)).replace(second=0, microsecond=0)

    def retrieve_weather_historic(
        self,
        start: datetime,
        stop: datetime,
        variable: WeatherHistoricType,
        measurement: str = "historic",
        interval: int = 10,
    ) -> Dict[str, Any]:
        """Retrieves the weather historic."""
        # Ensure timezone-aware current time
        now = datetime.now().astimezone().replace(second=0, microsecond=0)

        # Validate start and stop times
        if start > now:
            message = f"Start time {start} must be in the past (now: {now})"
            logger.error(message)
            raise ValueError(message)
        if stop > now:
            message = f"Stop time {stop} must be in the past (now: {now})"
            logger.error(message)
            raise ValueError(message)
        if start >= stop:
            message = f"Start time {start} must be before stop time {stop}"
            logger.error(message)
            raise ValueError(message)

        # Bucket and field setup
        bucket = self._labels_influx["temperature"]["bucket"]

        # Retrieve all possible weather types
        fields = [variable.value]

        # Try to retrieve data from Influx
        try:
            df = self._influx_manager.read(
                start=start - timedelta(hours=120),  # Be sure forecast 000 exists.
                stop=stop + timedelta(hours=120),
                msname=measurement,
                fields=fields,
                bucket=bucket,
            )
            if not df.empty:
                # Convert timezone
                df.index = df.index.tz_convert(os.getenv("TZ"))

                # Resample data
                weather = df.resample(f"{interval}min").mean().interpolate(method="linear", limit_direction="forward")
                logger.debug("Resampled data to %d-minute intervals", interval)
                # Limit reponse to the requested timeframe
                start_filter = self._round_up_to_10_minutes(start)
                stop_filter = self._round_up_to_10_minutes(stop)

                # Ensure datetime index and convert filters if necessary
                logger.debug("Ensuring weather DataFrame has a datetime index...")
                try:
                    if not isinstance(weather.index, pd.DatetimeIndex):
                        weather.index = pd.to_datetime(weather.index)
                        logger.debug("Weather df looks like this: %s", weather.head(3))
                        logger.debug("Converted weather index to DatetimeIndex.")

                    # Align timezones
                    if start_filter.tzinfo is not None and weather.index.tzinfo is None:
                        logger.debug("Localizing weather index to match filter timezone.")
                        weather.index = weather.index.tz_localize(start_filter.tzinfo)
                    elif start_filter.tzinfo is not None and weather.index.tzinfo != start_filter.tzinfo:
                        logger.debug("Converting weather index to match filter timezone.")
                        weather.index = weather.index.tz_convert(start_filter.tzinfo)

                    logger.debug("Start filter (rounded): %s", str(start_filter))
                    logger.debug("Stop filter (rounded): %s", str(stop_filter))

                    logger.debug("Filtering rows after or equal to start_filter...")
                    weather_after_start = weather[weather.index >= start_filter]
                    logger.debug("Remaining rows after start_filter: %d", len(weather_after_start))

                    logger.debug("Filtering rows before or equal to stop_filter...")
                    filtered_weather = weather_after_start[weather_after_start.index <= stop_filter]
                    logger.debug("Remaining rows after stop_filter: %d", len(filtered_weather))

                    logger.debug("Final filtered_weather dataframe head:\n%s", filtered_weather.head())

                except Exception as e:
                    logger.error("Error during filtering weather data: %s", str(e))
                    raise

                logger.info("Weather historic filtered")

                # Build the weather dictionary
                weather_dict = filtered_weather.rename_axis("timestamp").reset_index()
                weather_dict["timestamp"] = weather_dict["timestamp"].astype(str)
                weather_dict = dict(
                    zip(
                        weather_dict["timestamp"],
                        around(weather_dict[fields[0]], 1),
                        strict=False,
                    )
                )
                logger.debug("Response converted to dictionary.")

            else:
                logger.warning("No data found for measurement %s", measurement)
                weather_dict = {}

        except Exception as e:
            logger.error("Failed to query measurement %s: %s", measurement, e)
            weather_dict = {}

        return weather_dict
