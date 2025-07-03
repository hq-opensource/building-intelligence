"""Collection of Influx queries to retrieve historical data."""

from datetime import datetime
from typing import Tuple

import pandas as pd

from numpy import around

from common.database.influxdb import InfluxManager
from common.database.redis import RedisClient
from common.device.helper import DeviceHelper
from common.util.logging import LoggingUtil


logger = LoggingUtil.get_logger(__name__)


class HistoricQueries:
    """Class that groups the queries to retrieve historic data from InfluxDB."""

    def __init__(
        self,
        influx_manager: InfluxManager,
        redis_client: RedisClient,
    ) -> None:
        """
        Initializes the HistoricQueries class.

        Args:
            influx_manager (InfluxManager): An instance of the InfluxManager.
            redis_client (RedisClient): An instance of the RedisClient.
        """
        self._influx_manager = influx_manager

        # Read labels for databases
        self._labels_influx = redis_client.safe_read_from_redis("influxdb_mapping")
        self._labels_market = redis_client.safe_read_from_redis("labels_market")
        self._user_data_bucket_name = self._labels_influx["bucket_user_data"]

        # Retrieve information of the user from Redis
        self._devices = redis_client.safe_read_from_redis("user_devices")
        self._thermal_model = redis_client.safe_read_from_redis("thermal_model")

    def load_tz_temperature_historic(self, start: datetime, stop: datetime, entity_id: str) -> pd.DataFrame:
        """
        Retrieves the historic temperature for a given thermal zone.

        Args:
            start (datetime): The start time of the query.
            stop (datetime): The end time of the query.
            entity_id (str): The ID of the thermal zone.

        Returns:
            pd.DataFrame: A DataFrame containing the temperature data.
        """
        # Load info for the influx query
        bucket = self._labels_influx["sh_temperature"]["bucket"]
        measurement = self._labels_influx["sh_temperature"]["measurement"]
        tags = self._labels_influx["sh_temperature"]["tags"]
        tz_prefix = self._labels_influx["sh_temperature"]["field"]
        fields = [tz_prefix + entity_id]

        # Extend tags to include measure
        tags["_type"] = "measure"

        # Retrieve state
        tz_temperature_historic_query = self._influx_manager.read(start, stop, measurement, fields, bucket, tags)

        # Check if the query returned any data
        if tz_temperature_historic_query.empty:
            tz_temperature_historic = pd.DataFrame()
        else:
            # Perform sampling
            tz_temperature_historic = (
                tz_temperature_historic_query.resample(str(self._labels_market["dac_timestep"]) + "min")
                .mean()
                .interpolate(method="linear", limit_direction="forward")
            )

        tz_temperature_historic_dict = tz_temperature_historic.rename_axis("timestamp").reset_index()
        tz_temperature_historic_dict["timestamp"] = tz_temperature_historic_dict["timestamp"].astype(str)
        tz_temperature_historic_dict = dict(
            zip(
                tz_temperature_historic_dict["timestamp"],
                around(tz_temperature_historic_dict[fields[0]], 1),
                strict=False,
            )
        )

        return tz_temperature_historic_dict

    def load_tz_setpoint_historic(self, start: datetime, stop: datetime, entity_id: str) -> pd.DataFrame:
        """
        Retrieves the historic setpoint for a given thermal zone.

        Args:
            start (datetime): The start time of the query.
            stop (datetime): The end time of the query.
            entity_id (str): The ID of the thermal zone.

        Returns:
            pd.DataFrame: A DataFrame containing the setpoint data.
        """
        # Load info for the influx query
        bucket = self._labels_influx["sh_setpoint"]["bucket"]
        measurement = self._labels_influx["sh_setpoint"]["measurement"]
        tags = self._labels_influx["sh_setpoint"]["tags"]
        tz_prefix = self._labels_influx["sh_setpoint"]["field"]
        fields = [tz_prefix + entity_id]

        # Extend tags to include measure
        tags["_type"] = "measure"

        # Retrieve state
        tz_setpoint_historic_query = self._influx_manager.read(start, stop, measurement, fields, bucket, tags)

        # Check if the query returned any data
        if tz_setpoint_historic_query.empty:
            tz_setpoint_historic = pd.DataFrame()
        else:
            # Perform sampling
            tz_setpoint_historic = (
                tz_setpoint_historic_query.resample(str(self._labels_market["dac_timestep"]) + "min")
                .mean()
                .interpolate(method="linear", limit_direction="forward")
            )

        tz_setpoint_historic_dict = tz_setpoint_historic.rename_axis("timestamp").reset_index()
        tz_setpoint_historic_dict["timestamp"] = tz_setpoint_historic_dict["timestamp"].astype(str)
        tz_setpoint_historic_dict = dict(
            zip(
                tz_setpoint_historic_dict["timestamp"],
                around(tz_setpoint_historic_dict[fields[0]], 1),
                strict=False,
            )
        )

        return tz_setpoint_historic_dict

    def load_tz_electric_consumption(self, start: datetime, stop: datetime, entity_id: str) -> pd.DataFrame:
        """
        Retrieves the electric consumption of a specific thermal zone.

        Args:
            start (datetime): The start time of the query.
            stop (datetime): The end time of the query.
            entity_id (str): The ID of the thermal zone.

        Returns:
            pd.DataFrame: A DataFrame containing the electric consumption data.
        """
        # Load info for the influx query
        bucket = self._labels_influx["sh_power"]["bucket"]
        measurement = self._labels_influx["sh_power"]["measurement"]
        tags = self._labels_influx["sh_power"]["tags"]
        tz_prefix = self._labels_influx["sh_power"]["field"]
        fields = [tz_prefix + entity_id]

        # Extend tags to include measure
        tags["_type"] = "measure"

        # Retrieve state
        tz_electric_consumption_query = self._influx_manager.read(start, stop, measurement, fields, bucket, tags)

        # Check if the query returned any data
        if tz_electric_consumption_query.empty:
            tz_electric_consumption = tz_electric_consumption_query
        else:
            # Perform sampling
            tz_electric_consumption = (
                tz_electric_consumption_query.resample(str(self._labels_market["dac_timestep"]) + "min")
                .mean()
                .interpolate(method="linear", limit_direction="forward")
            )

        tz_electric_consumption_dict = tz_electric_consumption.rename_axis("timestamp").reset_index()
        tz_electric_consumption_dict["timestamp"] = tz_electric_consumption_dict["timestamp"].astype(str)
        tz_electric_consumption_dict = dict(
            zip(
                tz_electric_consumption_dict["timestamp"],
                around(tz_electric_consumption_dict[fields[0]], 2),
                strict=False,
            )
        )

        return tz_electric_consumption_dict

    def load_vehicle_consumption_historic(self, start: datetime, stop: datetime) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Retrieves consumption historic for the electric vehicle.

        Args:
            start (datetime): The start time of the query.
            stop (datetime): The end time of the query.

        Returns:
            Tuple[pd.DataFrame, pd.DataFrame]: A tuple containing the consumption data.
        """
        # Load info for the influx query
        bucket = self._labels_influx["v1g_net_power"]["bucket"]
        measurement = self._labels_influx["v1g_net_power"]["measurement"]
        tags = self._labels_influx["v1g_net_power"]["tags"]
        fields = [self._labels_influx["v1g_net_power"]["field"]]

        # Extend tags to include measure
        tags["_type"] = "measure"

        # Retrieve state
        ev_consumption_query = self._influx_manager.read(start, stop, measurement, fields, bucket, tags)

        # Check if the query returned any data
        if ev_consumption_query.empty:
            ev_consumption = ev_consumption_query
        else:
            # Perform sampling
            ev_consumption = (
                ev_consumption_query.resample(str(self._labels_market["dac_timestep"]) + "min")
                .mean()
                .interpolate(method="linear", limit_direction="forward")
            )

        ev_consumption_dict = ev_consumption.rename_axis("timestamp").reset_index()
        ev_consumption_dict["timestamp"] = ev_consumption_dict["timestamp"].astype(str)
        ev_consumption_dict = dict(
            zip(
                ev_consumption_dict["timestamp"],
                around(ev_consumption_dict[fields[0]], 2),
                strict=False,
            )
        )

        return ev_consumption_dict

    def load_ec_non_controllable_loads_historic(self, start: datetime, stop: datetime) -> pd.DataFrame:
        """
        Builds and retrieves the non-controllable consumption.

        Args:
            start (datetime): The start time of the query.
            stop (datetime): The end time of the query.

        Returns:
            pd.DataFrame: A DataFrame containing the non-controllable consumption data.
        """
        # Build the non controllable loads consumption and save it on influx
        non_controllable_loads = self._compute_non_controllable_consumption(start, stop)
        field_non_controllable_loads = self._labels_influx["not_controllable_loads"]["field"]

        non_controllable_loads_dict = non_controllable_loads.rename_axis("timestamp").reset_index()
        non_controllable_loads_dict["timestamp"] = non_controllable_loads_dict["timestamp"].astype(str)
        non_controllable_loads_dict = dict(
            zip(
                non_controllable_loads_dict["timestamp"],
                around(non_controllable_loads_dict[field_non_controllable_loads], 1),
                strict=False,
            )
        )

        return non_controllable_loads_dict

    # Required methods to build the non controllable loads historic
    # TODO: JUAN: This should be moved to the data engine! An RPC call should call the service for non controllable loads

    def _compute_non_controllable_consumption(self, start: datetime, stop: datetime) -> pd.DataFrame:
        """
        This method computes the non-controllable loads.

        Args:
            start (datetime): The start time of the query.
            stop (datetime): The end time of the query.

        Returns:
            pd.DataFrame: A DataFrame containing the non-controllable consumption data.
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
        neg_consumption = (total_consumption * -1) + tot_thermostats + tot_battery + tot_water_heater + (tot_ev * -1)
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

        return non_controllable_df

    def _resample_accumulated_consumption(
        self, start: datetime, stop: datetime
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Resamples the accumulated consumption data.

        Args:
            start (datetime): The start time of the query.
            stop (datetime): The end time of the query.

        Returns:
            Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]: A tuple containing the resampled total consumption,
                                                            non-controllable loads, and thermostat consumption.
        """
        # region to retrieve the total resampled energy consumption
        total_consumption_query = self._influx_manager.read_accumulated_value(
            start=start,
            stop=stop,
            msname=self._labels_influx["ms_electric_consumption_accumulated"],
            fields=[self._labels_influx["fd_total_electric_consumption_accumulated"]],
            bucket=self._labels_influx["bucket_user_data"],
            timestep=int(self._labels_market["dac_timestep"]),
        )

        # Check if the query returned any data
        if total_consumption_query.empty:
            resampled_total_consumption = pd.DataFrame()
        else:
            # Resample
            resampled_total_consumption = (
                total_consumption_query.resample(str(self._labels_market["dac_timestep"]) + "min")
                .mean()
                .interpolate(method="linear", limit_direction="forward")
            )
        # endregion to retrieve the total resampled energy consumption

        # region to retrieve the accumulated non controllable loads
        non_controllable_loads_query = self._influx_manager.read_accumulated_value(
            start=start,
            stop=stop,
            msname=self._labels_influx["ms_electric_consumption_accumulated"],
            fields=[self._labels_influx["fd_non_controllable_loads_accumulated"]],
            bucket=self._labels_influx["bucket_user_data"],
            timestep=int(self._labels_market["dac_timestep"]),
        )

        # Check if the query returned any data
        if non_controllable_loads_query.empty:
            resampled_non_controllable_loads = pd.DataFrame()
        else:
            # Resample
            resampled_non_controllable_loads = (
                non_controllable_loads_query.resample(str(self._labels_market["dac_timestep"]) + "min")
                .mean()
                .interpolate(method="linear", limit_direction="forward")
            )
        # endregion to retrieve the accumulated non controllable loads

        # region to retrieve the accumulated consumption of the thermostats
        if DeviceHelper.count_devices_by_type(self._devices, DeviceHelper.SPACE_HEATING.value) > 0:
            # Create fields for the query
            quantity_of_thermal_zones = self._thermal_model["thermal_zones"]
            fields_thermal_zones_to_ask = []
            for pos in range(quantity_of_thermal_zones):
                fields_thermal_zones_to_ask += [self._labels_influx["fd_thermal_zones_name"] + str(pos + 1)]

            # Make the influx query for the electric consumption of the thermostats
            consumption_thermostats_query = self._influx_manager.read_accumulated_value(
                start=start,
                stop=stop,
                msname=self._labels_influx["ms_st_consumption_real_accumulated"],
                fields=fields_thermal_zones_to_ask,
                bucket=self._user_data_bucket_name,
                timestep=int(self._labels_market["dac_timestep"]),
            )

            # Check if the query returned any data
            if consumption_thermostats_query.empty:
                resampled_consumption_thermostats = pd.DataFrame()
            else:
                # resample (This should not be required here. Verify if its good)
                resampled_consumption_thermostats = (
                    consumption_thermostats_query.resample(str(self._labels_market["dac_timestep"]) + "min")
                    .mean()
                    .interpolate(method="linear", limit_direction="forward")
                )

        else:
            resampled_consumption_thermostats = pd.DataFrame()
        # endregion to retrieve the accumulated consumption of the thermostats

        return resampled_total_consumption, resampled_non_controllable_loads, resampled_consumption_thermostats

    def _save_real_consumption_influx(
        self,
        resampled_total_consumption: pd.DataFrame,
        resampled_non_controllable_loads: pd.DataFrame,
        resampled_consumption_thermostats: pd.DataFrame,
    ) -> None:
        """
        Saves the real consumption data to InfluxDB.

        Args:
            resampled_total_consumption (pd.DataFrame): The resampled total consumption data.
            resampled_non_controllable_loads (pd.DataFrame): The resampled non-controllable loads data.
            resampled_consumption_thermostats (pd.DataFrame): The resampled thermostat consumption data.
        """
        # Save the resampled total consumption
        self._influx_manager.synchronous_write(
            bucket=self._labels_influx["bucket_user_data"],
            data=resampled_total_consumption,
            data_frame_measurement_name=self._labels_influx["ms_electric_consumption_real"],
        )
        self._influx_manager.synchronous_write(
            bucket=self._labels_influx["bucket_user_data"],
            data=resampled_non_controllable_loads,
            data_frame_measurement_name=self._labels_influx["ms_electric_consumption_real"],
        )
        # Save the resampled thermostat energy cnsumption
        self._influx_manager.synchronous_write(
            bucket=self._labels_influx["bucket_user_data"],
            data=resampled_consumption_thermostats,
            data_frame_measurement_name=self._labels_influx["ms_st_consumption_real"],
        )
