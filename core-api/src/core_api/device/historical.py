from datetime import datetime
from typing import Dict, List

from common.database.influxdb import InfluxManager
from common.database.redis import RedisClient
from common.device.helper import DeviceHelper
from common.util.logging import LoggingUtil


logger = LoggingUtil.get_logger(__name__)


# class def
class HistoricalDataReader:
    """Class created to read and overwrite values from InfluxDB."""

    def __init__(self, influx_manager: InfluxManager, redis_client: RedisClient) -> None:
        """
        Initializes the HistoricalDataReader class.

        Args:
            influx_manager (InfluxManager): An instance of the InfluxManager.
            redis_client (RedisClient): An instance of the RedisClient.
        """
        # Define database clients
        self._influx_manager = influx_manager
        self._redis_client = redis_client

        # Read labels for databases
        self._labels_influx = redis_client.safe_read_from_redis("influxdb_mapping")

        # Read devices
        self._devices = redis_client.safe_read_from_redis("user_devices")

    def get_historical_data(
        self,
        start: datetime,
        stop: datetime,
        devices: List[str],
    ) -> dict[str, list]:
        """
        Retrieves historical data for a list of devices.

        Args:
            start (datetime): The start time of the query.
            stop (datetime): The end time of the query.
            devices (List[str]): A list of device IDs.

        Returns:
            dict[str, list]: A dictionary containing the historical data for each device.
        """
        to_return = {}
        # Define a dictionary to map device types to their corresponding methods
        device_type_to_method = {
            DeviceHelper.SPACE_HEATING.value: self._get_space_heating_data,
            DeviceHelper.ON_OFF_EV_CHARGER.value: self._get_ev_charger_data,
            DeviceHelper.ELECTRIC_VEHICLE_V1G.value: self._get_v1g_data,
            DeviceHelper.ELECTRIC_VEHICLE_V2G.value: self._get_v2g_data,
            DeviceHelper.ELECTRIC_STORAGE.value: self._get_electric_storage_data,
            DeviceHelper.WATER_HEATER.value: self._get_water_heater_data,
            DeviceHelper.THERMAL_STORAGE.value: self._get_thermal_storage_data,
        }

        for entity_id in devices:
            # Get device type
            device_type = self._get_device_type(entity_id)

            # Retrieve the corresponding method from the dictionary
            retrieve_method = device_type_to_method.get(device_type)

            if retrieve_method:
                result = retrieve_method(start, stop, entity_id)
                to_return[entity_id] = result
            else:
                logger.error(f"Device of type {device_type} is not supported")
                to_return[entity_id] = []

        return to_return

    def _get_device_type(self, entity_id: str) -> str:
        """
        Gets the type of a device.

        Args:
            entity_id (str): The ID of the device.

        Returns:
            str: The type of the device.
        """
        device_type = DeviceHelper.get_all_values_by_filtering_devices(
            device_list=self._devices, filter_key="entity_id", filter_value=entity_id, target_key="type"
        )
        return device_type[0]

    def _get_space_heating_data(self, start: datetime, stop: datetime, entity_id: str) -> list:
        """
        Gets historical data for a space heating device.

        Args:
            start (datetime): The start time of the query.
            stop (datetime): The end time of the query.
            entity_id (str): The ID of the device.

        Returns:
            list: A list containing the historical data.
        """
        # Get all entity ids of the thermal zones
        bucket = self._labels_influx["sh_temperature"]["bucket"]
        measurement = self._labels_influx["sh_temperature"]["measurement"]
        tags = self._labels_influx["sh_temperature"]["tags"]
        tz_prefix = self._labels_influx["sh_temperature"]["field"]
        fields = [tz_prefix + entity_id]

        # Extend tags to include measure
        tags["_type"] = "measure"

        # Retrieve state
        return self._get_data(start, stop, bucket, measurement, fields, tags)

    def _get_ev_charger_data(self, start: datetime, stop: datetime, entity_id: str) -> list:
        """
        Gets historical data for an EV charger device.

        Args:
            start (datetime): The start time of the query.
            stop (datetime): The end time of the query.
            entity_id (str): The ID of the device.

        Returns:
            list: A list containing the historical data.
        """
        # Build the desired state
        bucket = self._labels_influx["ev_charger_net_power"]["bucket"]
        measurement = self._labels_influx["ev_charger_net_power"]["measurement"]
        tags = self._labels_influx["ev_charger_net_power"]["tags"]
        field = self._labels_influx["ev_charger_net_power"]["field"]
        fields = [field]

        # Extend tags to include measure
        tags["_type"] = "measure"

        # Retrieve state
        return self._get_data(start, stop, bucket, measurement, fields, tags)

    def _get_v1g_data(self, start: datetime, stop: datetime, entity_id: str) -> list:
        """
        Gets historical data for a V1G device.

        Args:
            start (datetime): The start time of the query.
            stop (datetime): The end time of the query.
            entity_id (str): The ID of the device.

        Returns:
            list: A list containing the historical data.
        """
        # Build the desired state
        bucket = self._labels_influx["v1g_time_series_of_charge"]["bucket"]
        measurement = self._labels_influx["v1g_time_series_of_charge"]["measurement"]
        tags = self._labels_influx["v1g_time_series_of_charge"]["tags"]
        field = self._labels_influx["v1g_time_series_of_charge"]["field"]
        fields = [field]

        # Extend tags to include measure
        tags["_type"] = "measure"

        # Retrieve state
        return self._get_data(start, stop, bucket, measurement, fields, tags)

    def _get_v2g_data(self, start: datetime, stop: datetime, entity_id: str) -> list:
        """
        Gets historical data for a V2G device.

        Args:
            start (datetime): The start time of the query.
            stop (datetime): The end time of the query.
            entity_id (str): The ID of the device.

        Returns:
            list: A list containing the historical data.
        """
        bucket = self._labels_influx["v2g_time_series_of_charge"]["bucket"]
        measurement = self._labels_influx["v2g_time_series_of_charge"]["measurement"]
        tags = self._labels_influx["v2g_time_series_of_charge"]["tags"]
        field = self._labels_influx["v2g_time_series_of_charge"]["field"]
        fields = [field]

        # Extend tags to include measure
        tags["_type"] = "measure"

        # Retrieve state
        return self._get_data(start, stop, bucket, measurement, fields, tags)

    def _get_electric_storage_data(self, start: datetime, stop: datetime, entity_id: str) -> list:
        """
        Gets historical data for an electric storage device.

        Args:
            start (datetime): The start time of the query.
            stop (datetime): The end time of the query.
            entity_id (str): The ID of the device.

        Returns:
            list: A list containing the historical data.
        """
        bucket = self._labels_influx["eb_time_series_of_charge"]["bucket"]
        measurement = self._labels_influx["eb_time_series_of_charge"]["measurement"]
        tags = self._labels_influx["eb_time_series_of_charge"]["tags"]
        field = self._labels_influx["eb_time_series_of_charge"]["field"]
        fields = [field]

        # Extend tags to include measure
        tags["_type"] = "measure"

        # Retrieve state
        return self._get_data(start, stop, bucket, measurement, fields, tags)

    def _get_water_heater_data(self, start: datetime, stop: datetime, entity_id: str) -> list:
        """
        Gets historical data for a water heater device.

        Args:
            start (datetime): The start time of the query.
            stop (datetime): The end time of the query.
            entity_id (str): The ID of the device.

        Returns:
            list: A list containing the historical data.
        """
        bucket = self._labels_influx["wh_temperature"]["bucket"]
        measurement = self._labels_influx["wh_temperature"]["measurement"]
        tags = self._labels_influx["wh_temperature"]["tags"]
        field = self._labels_influx["wh_temperature"]["field"]
        fields = [field]

        # Extend tags to include measure
        tags["_type"] = "measure"

        # Retrieve state
        return self._get_data(start, stop, bucket, measurement, fields, tags)

    def _get_thermal_storage_data(self, start: datetime, stop: datetime, entity_id: str) -> list:
        """
        Gets historical data for a thermal storage device.

        Args:
            start (datetime): The start time of the query.
            stop (datetime): The end time of the query.
            entity_id (str): The ID of the device.

        Returns:
            list: A list containing the historical data.
        """
        bucket = self._labels_influx["ts_time_series_of_charge"]["bucket"]
        measurement = self._labels_influx["ts_time_series_of_charge"]["measurement"]
        tags = self._labels_influx["ts_time_series_of_charge"]["tags"]
        fields = [entity_id]

        # Extend tags to include measure
        tags["_type"] = "measure"

        # Retrieve state
        return self._get_data(start, stop, bucket, measurement, fields, tags)

    def _get_data(
        self, start: datetime, stop: datetime, bucket: str, measurement: str, fields: List[str], tags: Dict[str, str]
    ) -> list:
        """
        Retrieve data from InfluxDB.

        Args:
            start (datetime): The start time of the query.
            stop (datetime): The end time of the query.
            bucket (str): The bucket to query.
            measurement (str): The measurement to query.
            fields (List[str]): The fields to query.
            tags (Dict[str, str]): The tags to query.

        Returns:
            list: A list containing the data.
        """
        query_result = self._influx_manager.read(start, stop, measurement, fields, bucket, tags)
        if len(query_result) == 0:
            logger.error(f"An error occured retrieving historical data of a device. Fields: {fields}")
            return []

        numpy_result = query_result.to_numpy()[0]
        return numpy_result.tolist()
