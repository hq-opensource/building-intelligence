"""
This module provides the ForecastRetriever class, which is responsible for
generating forecasts, specifically for non-controllable loads.
It leverages historical data from InfluxDB and configuration from Redis,
using the Prophet library for time series forecasting.
"""

import os

from datetime import datetime, timedelta

import pandas as pd

from numpy import around, ndarray
from prophet import Prophet

from common.database.influxdb import InfluxManager
from common.database.redis import RedisClient
from common.device.helper import DeviceHelper
from common.util.logging import LoggingUtil


logger = LoggingUtil.get_logger(__name__)


class ForecastRetriever:
    """
    A class responsible for retrieving and computing forecasts, particularly for non-controllable loads.
    It interacts with InfluxDB for historical data and Redis for configuration and device information.
    """

    def __init__(self) -> None:
        """
        Initializes the ForecastRetriever with InfluxDB and Redis client instances.
        It also loads necessary configuration and device information from Redis.
        """
        self._influx_manager = InfluxManager()
        redis_client = RedisClient()

        # Read labels for databases
        self._labels_influx = redis_client.safe_read_from_redis("influxdb_mapping")
        self._labels_market = redis_client.safe_read_from_redis("labels_market")
        self._weather_bucket_name = self._labels_influx["bucket_weather"]
        self._user_data_bucket_name = self._labels_influx["bucket_user_data"]

        # Retrieve information of the user from Redis
        self._devices = redis_client.safe_read_from_redis("user_devices")
        self._thermal_model = redis_client.safe_read_from_redis("thermal_model")

    def non_controllable_loads_forecast(
        self, start_forecast: str, stop_forecast: str, interval: int = 10
    ) -> pd.DataFrame:
        """
        Computes the forecast for non-controllable loads using historical data and Prophet.

        This method performs the following steps:
        1. Defines the start and end times for the forecast.
        2. Computes the historical non-controllable loads.
        3. Trains a Prophet model using the historical data.
        4. Generates a forecast using the trained Prophet model.
        5. Saves the generated forecast to InfluxDB.
        6. Returns the forecast as a dictionary.

        Args:
            start_forecast (str): The ISO formatted string representing the start time of the forecast.
            stop_forecast (str): The ISO formatted string representing the end time of the forecast.
            interval (int): The interval in minutes for the forecast data points. Defaults to 10.

        Returns:
            pd.DataFrame: A pandas DataFrame containing the non-controllable loads forecast,
                          indexed by timestamp.
        """
        # Compute start time and end time for the forecast
        start_time_forecast = datetime.fromisoformat(start_forecast).replace(second=0, microsecond=0)
        end_time_forecast = datetime.fromisoformat(stop_forecast).replace(second=0, microsecond=0)

        # Compute periods
        start_historic = start_time_forecast.replace(minute=0) - timedelta(days=30)
        stop_historic = start_time_forecast
        periods_to_predict = int((end_time_forecast - start_time_forecast).total_seconds() // (interval * 60)) + 1

        # Compute the non controllable loads
        non_controllable_loads_historic = self._compute_non_controllable_historic(start_historic, stop_historic)

        # Compute forecast using prophet
        prophet_model = self._execute_prophet_learning(non_controllable_loads_historic)
        non_controllable_loads_forecast = self._load_forecast_using_prophet(prophet_model, periods_to_predict, interval)

        # Create a dataframe to save results
        bucket = self._labels_influx["not_controllable_loads"]["bucket"]
        measurement = self._labels_influx["not_controllable_loads"]["measurement"]
        field = self._labels_influx["not_controllable_loads"]["field"]
        tags = self._labels_influx["not_controllable_loads"]["tags"]

        time_index = pd.date_range(start=start_time_forecast, end=end_time_forecast, freq=str(interval) + "min")
        non_controllable_loads_forecast_df = pd.DataFrame(
            data={field: non_controllable_loads_forecast},
            index=time_index,
        )

        # Filter data
        filtered_non_controllable_loads_forecast_df = non_controllable_loads_forecast_df[
            (non_controllable_loads_forecast_df.index >= start_time_forecast)
            & (non_controllable_loads_forecast_df.index <= end_time_forecast)
        ]

        # Save forecast on InfluxDB
        self._influx_manager.synchronous_write(
            bucket=bucket,
            data=filtered_non_controllable_loads_forecast_df,
            data_frame_measurement_name=measurement,
            tags=tags,
        )

        # process as dictionary
        non_controllable_loads_forecast_dict = filtered_non_controllable_loads_forecast_df.rename_axis(
            "timestamp"
        ).reset_index()
        non_controllable_loads_forecast_dict["timestamp"] = non_controllable_loads_forecast_dict["timestamp"].astype(
            str
        )
        non_controllable_loads_forecast_dict = dict(
            zip(
                non_controllable_loads_forecast_dict["timestamp"],
                around(non_controllable_loads_forecast_dict[self._labels_influx["not_controllable_loads"]["field"]], 2),
                strict=False,
            )
        )

        return non_controllable_loads_forecast_dict

    def _execute_prophet_learning(
        self,
        non_controllable_loads_historic: pd.DataFrame,
    ) -> Prophet:
        """
        Executes the training of the forecasting model using the Prophet library.

        Args:
            non_controllable_loads_historic (pd.DataFrame): Historical data of non-controllable loads
                                                            with a datetime index and a 'y' column.

        Returns:
            Prophet: A trained Prophet model instance.
        """
        # Create the dataframe for prophet
        prophet_df = pd.DataFrame(
            {
                "ds": non_controllable_loads_historic.index.tz_localize(None),  # datetime index for prophet
                "y": non_controllable_loads_historic[
                    self._labels_influx["not_controllable_loads"]["field"]
                ],  # independent variable for prophet
            }
        ).reset_index()

        prophet_model = Prophet(
            daily_seasonality=True,
            changepoint_prior_scale=0.01,
            growth="flat",
            # interval_width=0.95,
        )
        prophet_model.fit(prophet_df)

        return prophet_model

    def _load_forecast_using_prophet(
        self,
        prophet_model: Prophet,
        periods: int,
        interval: int = 10,
    ) -> ndarray:
        """
        Generates future forecasts using a trained Prophet model.

        Args:
            prophet_model (Prophet): An already trained Prophet model.
            periods (int): The number of future periods to forecast.
            interval (int): The frequency interval in minutes for the future dataframe. Defaults to 10.

        Returns:
            ndarray: A NumPy array containing the forecasted 'yhat' values for the specified periods.
        """
        # Execute forecast
        future = prophet_model.make_future_dataframe(
            periods=periods, freq=str(interval) + "min"
        )  # extended datetime index
        demand_forecast = prophet_model.predict(future)  # forecast variable

        forecast = demand_forecast["yhat"].tail(periods).values

        return forecast

    def _compute_non_controllable_historic(self, start: datetime, stop: datetime) -> pd.DataFrame:
        """
        Computes the historical non-controllable loads by subtracting controllable loads
        (thermostats, batteries, EVs, water heaters) from the total power consumption.

        Args:
            start (datetime): The start datetime for retrieving historical data.
            stop (datetime): The stop datetime for retrieving historical data.

        Returns:
            pd.DataFrame: A pandas DataFrame containing the historical non-controllable loads,
                          indexed by timestamp.
        """
        # region to load values
        # Retrieve total power consumption
        bucket = self._labels_influx["net_power"]["bucket"]
        measurement = self._labels_influx["net_power"]["measurement"]
        fields = [self._labels_influx["net_power"]["field"]]
        tags = self._labels_influx["net_power"]["tags"]
        tags["_type"] = "measure"
        total_consumption_df = self._influx_manager.read(
            start=start, stop=stop, msname=measurement, fields=fields, bucket=bucket, tags=tags
        )

        # Retrieve information for smart thermostats
        num_thermostats = DeviceHelper.count_devices_by_type(self._devices, DeviceHelper.SPACE_HEATING.value)
        if num_thermostats > 0:
            bucket = self._labels_influx["sh_power"]["bucket"]
            measurement = self._labels_influx["sh_power"]["measurement"]

            # Get all entity IDs
            entity_ids = DeviceHelper.get_all_values_by_filtering_devices(
                device_list=self._devices,
                filter_key="type",
                filter_value=DeviceHelper.SPACE_HEATING.value,
                target_key="entity_id",
            )
            fields = []
            for entity in entity_ids:
                fields.append("power_" + entity)
            tags = self._labels_influx["sh_power"]["tags"]
            tags["_type"] = "measure"
            tz_total_consumption_df = self._influx_manager.read(
                start=start, stop=stop, msname=measurement, fields=fields, bucket=bucket, tags=tags
            )
        else:
            tz_total_consumption_df = pd.DataFrame()

        # Retrieve information for electric battery
        num_batteries = DeviceHelper.count_devices_by_type(self._devices, DeviceHelper.ELECTRIC_STORAGE.value)
        if num_batteries > 0:
            bucket = self._labels_influx["eb_net_power"]["bucket"]
            measurement = self._labels_influx["eb_net_power"]["measurement"]
            fields = [self._labels_influx["eb_net_power"]["field"]]
            tags = self._labels_influx["eb_net_power"]["tags"]
            tags["_type"] = "measure"
            battery_total_consumption_df = self._influx_manager.read(
                start=start, stop=stop, msname=measurement, fields=fields, bucket=bucket, tags=tags
            )
        else:
            battery_total_consumption_df = pd.DataFrame()

        # Retrieve information for electric vehicle
        num_ev = DeviceHelper.count_devices_by_type(self._devices, DeviceHelper.ON_OFF_EV_CHARGER.value)
        if num_ev > 0:
            bucket = self._labels_influx["v1g_net_power"]["bucket"]
            measurement = self._labels_influx["v1g_net_power"]["measurement"]
            fields = [self._labels_influx["v1g_net_power"]["field"]]
            tags = self._labels_influx["v1g_net_power"]["tags"]
            tags["_type"] = "measure"
            ev_total_consumption_df = self._influx_manager.read(
                start=start, stop=stop, msname=measurement, fields=fields, bucket=bucket, tags=tags
            )
        else:
            ev_total_consumption_df = pd.DataFrame()

        # Retrieve information for electric vehicle
        num_water_heater = DeviceHelper.count_devices_by_type(self._devices, DeviceHelper.WATER_HEATER.value)
        if num_water_heater > 0:
            bucket = self._labels_influx["wh_power"]["bucket"]
            measurement = self._labels_influx["wh_power"]["measurement"]
            fields = [self._labels_influx["wh_power"]["field"]]
            tags = self._labels_influx["wh_power"]["tags"]
            tags["_type"] = "measure"
            water_heater_total_consumption_df = self._influx_manager.read(
                start=start, stop=stop, msname=measurement, fields=fields, bucket=bucket, tags=tags
            )
        else:
            water_heater_total_consumption_df = pd.DataFrame()
        # endregion to load values

        # region to compute the non controllable loads

        # Compute total consumption (Consumption = Negative, Production = Positive)
        total_consumption = total_consumption_df.sum(axis=1)

        # Compute controllable consumption
        tot_thermostats = tz_total_consumption_df.sum(axis=1) if not tz_total_consumption_df.empty else 0
        tot_battery = battery_total_consumption_df.sum(axis=1) if not battery_total_consumption_df.empty else 0
        tot_ev = ev_total_consumption_df.sum(axis=1) if not ev_total_consumption_df.empty else 0
        tot_water_heater = (
            water_heater_total_consumption_df.sum(axis=1) if not water_heater_total_consumption_df.empty else 0
        )

        # Compute the non controllable loads
        # TODO: Juan, verify this computation to validate if this is correct.
        # TODO: Maybe delete the generation? Leave only the consumption?
        # TODO: Delete the battery temporary!
        neg_consumption = (total_consumption * -1) + tot_thermostats + tot_water_heater + (tot_ev * -1)
        # neg_consumption = (total_consumption * -1) + tot_thermostats + tot_battery + tot_water_heater + (tot_ev * -1)
        # endregion to compute the non controllable loads

        # region to save the non controllable loads in Influx
        bucket_save = self._labels_influx["not_controllable_loads"]["bucket"]
        measurement_save = self._labels_influx["not_controllable_loads"]["measurement"]
        field_save = self._labels_influx["not_controllable_loads"]["field"]
        tags_save = self._labels_influx["not_controllable_loads"]["tags"]

        # Build the dataframe to save
        non_controllable_df = pd.DataFrame(index=total_consumption_df.index)
        non_controllable_df[field_save] = neg_consumption

        # save the non controllable loads in InfluxDB
        self._influx_manager.synchronous_write(
            bucket=bucket_save, data=non_controllable_df, data_frame_measurement_name=measurement_save, tags=tags_save
        )
        # endregion to save the non controllable loads in Influx

        non_controllable_df = non_controllable_df.tz_convert(tz=os.getenv("TZ"))

        return non_controllable_df
