"""
This module provides the InfluxManager class for interacting with InfluxDB.

It includes functionalities for reading, writing, and querying time-series data,
as well as managing buckets and retrieving metadata like measurements and fields.
"""

import os

from datetime import datetime, timedelta
from typing import Any, Dict, List

import pandas as pd

from influxdb_client import BucketsApi, InfluxDBClient, QueryApi, WriteApi
from influxdb_client.client.write_api import SYNCHRONOUS, PointSettings

from common.util.logging import LoggingUtil


logger = LoggingUtil.get_logger(__name__)


class InfluxManager:
    """
    Manages interactions with InfluxDB, providing methods for reading, writing, and querying data.

    This class encapsulates the InfluxDB client and offers a simplified interface for common database operations,
    including handling dataframes, managing buckets, and retrieving measurement and field keys.
    """

    _influx_client: InfluxDBClient

    def __init__(
        self,
        url: str = os.getenv("INFLUXDB_URL"),
        org: str = os.getenv("INFLUXDB_ORG"),
        token: str = os.getenv("INFLUXDB_TOKEN"),
    ) -> None:
        """
        Initializes the InfluxManager with connection details for InfluxDB.

        Args:
            url (str): The URL of the InfluxDB instance. Defaults to INFLUXDB_URL environment variable.
            org (str): The organization name in InfluxDB. Defaults to INFLUXDB_ORG environment variable.
            token (str): The authentication token for InfluxDB. Defaults to INFLUXDB_TOKEN environment variable.
        """
        self._influx_client = InfluxDBClient(url=url, token=token, org=org, timeout=30000)

    def read(
        self,
        start: datetime,
        stop: datetime,
        msname: str,
        fields: List[str],
        bucket: str,
        tags: Dict[str, str] | None = None,
        interval: str = "10m",  # New parameter for downsampling interval
        agg_func: str = "mean",  # New parameter for aggregation function
    ) -> pd.DataFrame:
        """
        Reads data from InfluxDB for a specified time range, measurement, and fields, with optional downsampling.

        Args:
            start (datetime): The start timestamp for the query.
            stop (datetime): The stop timestamp for the query.
            msname (str): The measurement name to query.
            fields (List[str]): A list of field names to retrieve.
            bucket (str): The InfluxDB bucket name.
            tags (Dict[str, str] | None): Optional tags to filter the query. Defaults to None.
            interval (str): The downsampling interval (e.g., "10m", "1h"). Defaults to "10m".
            agg_func (str): The aggregation function to apply (e.g., "mean", "last"). Defaults to "mean".

        Returns:
            pd.DataFrame: A DataFrame containing the queried data, indexed by time.
        """

        if tags is None:
            tags = {}

        fields_list = " or ".join(['r["_field"] == "{}"'.format(field) for field in fields])

        if tags:
            tags_list = " and " + " and ".join(
                ['r.{} == "{}"'.format(tag_key, tag_value) for (tag_key, tag_value) in tags.items()]
            )
        else:
            tags_list = ""

        start_str = start.isoformat()
        stop_str = stop.isoformat()

        query = f"""
            from(bucket: "{bucket}")
            |> range(start: {start_str}, stop: {stop_str})
            |> filter(fn: (r) => r["_measurement"] == "{msname}"{tags_list})
            |> filter(fn: (r) => {fields_list})
            |> aggregateWindow(every: {interval}, fn: {agg_func}, createEmpty: false)
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        """

        logger.debug("Querying InfluxDB: %s", query)

        api_queryfcast = self._influx_client.query_api()
        query_results = api_queryfcast.query_data_frame(query)
        if query_results.empty:
            results_to_return = pd.DataFrame()
        else:
            results_to_return = query_results[fields]
            results_to_return = results_to_return.set_index(query_results["_time"])
            results_to_return.index.name = None

        logger.debug(
            f"Query to bucket {bucket} and measurement {msname} with the fields {fields}, downsampled to {interval}"
        )

        return results_to_return

    def get_write_api(self, tags: Dict[str, str] | None = None) -> WriteApi:
        """
        Retrieves a configured InfluxDB WriteApi instance.

        Args:
            tags (Dict[str, str] | None): Optional default tags to apply to all points written using this API.
                                          Defaults to None.

        Returns:
            WriteApi: An InfluxDB WriteApi instance.
        """
        if tags is None:
            tags = {}

        point_settings = PointSettings()
        for tag_key, tag_value in tags.items():
            point_settings.add_default_tag(tag_key, tag_value)

        return self._influx_client.write_api(point_settings=point_settings)

    def get_buckets_api(self) -> BucketsApi:
        """
        Retrieves the InfluxDB BucketsApi instance.

        Returns:
            BucketsApi: An InfluxDB BucketsApi instance.
        """
        return self._influx_client.buckets_api()

    def get_query_api(self) -> QueryApi:
        """
        Retrieves the InfluxDB QueryApi instance.

        Returns:
            QueryApi: An InfluxDB QueryApi instance.
        """
        return self._influx_client.query_api()

    def synchronous_write(
        self, bucket: str, data: pd.DataFrame, data_frame_measurement_name: str, tags: Dict[str, str] | None = None
    ) -> None:
        """
        Writes a pandas DataFrame to InfluxDB synchronously.

        Args:
            bucket (str): The InfluxDB bucket to write to.
            data (pd.DataFrame): The DataFrame containing the data to write.
            data_frame_measurement_name (str): The measurement name to use for the DataFrame.
            tags (Dict[str, str] | None): Optional tags to apply to all points in the DataFrame. Defaults to None.
        """
        if tags is None:
            tags = {}

        point_settings = PointSettings()
        for tag_key, tag_value in tags.items():
            point_settings.add_default_tag(tag_key, tag_value)

        write_client = self._influx_client.write_api(write_options=SYNCHRONOUS, point_settings=point_settings)
        write_client.write(bucket=bucket, record=data, data_frame_measurement_name=data_frame_measurement_name)

    def read_all_fields(
        self,
        start: datetime,
        stop: datetime,
        msname: str,
        bucket: str,
        tags: Dict[str, str] | None = None,
    ) -> pd.DataFrame:
        """
        Reads all fields from a given measurement within a specified time range in InfluxDB.

        Args:
            start (datetime): The start timestamp for the query.
            stop (datetime): The stop timestamp for the query.
            msname (str): The measurement name to query.
            bucket (str): The InfluxDB bucket name.
            tags (Dict[str, str] | None): Optional tags to filter the query. Defaults to None.

        Returns:
            pd.DataFrame: A DataFrame containing all fields for the specified measurement, indexed by time.
        """
        if tags is None:
            tags = {}

        if tags:
            tags_list = " and " + " and ".join(
                ['r.{} == "{}"'.format(tag_key, tag_value) for (tag_key, tag_value) in tags.items()]
            )
        else:
            tags_list = ""

        start_str = start.isoformat()
        stop_str = stop.isoformat()

        query = """
            from(bucket: "{}")
            |> range(start: {}, stop: {})
            |> filter(fn: (r) => r["_measurement"] == "{}"{})
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        """.format(bucket, start_str, stop_str, msname, tags_list)

        logger.debug("Querying InfluxDB: %s", query)

        api_query = self._influx_client.query_api()
        query_results = api_query.query_data_frame(query)
        if query_results.empty:
            return pd.DataFrame()

        query_results = query_results.set_index(query_results["_time"])
        query_results.index.name = None
        query_results.drop(
            columns=["result", "table", "_start", "_stop", "_measurement", "_type", "_time"], inplace=True
        )

        return query_results

    def read_accumulated_value(
        self,
        start: datetime,
        stop: datetime,
        msname: str,
        fields: List[str],
        bucket: str,
        timestep: int,
        tags: Dict[str, str] | None = None,
    ) -> pd.DataFrame:
        """
        Reads accumulated values (differences between consecutive points) for specified fields from InfluxDB.

        This method calculates the difference between consecutive 'last' values within each `timestep` interval.
        Useful for meters that report total accumulated values, to get the consumption over an interval.

        Args:
            start (datetime): The start timestamp for the query.
            stop (datetime): The stop timestamp for the query.
            msname (str): The measurement name to query.
            fields (List[str]): A list of field names to retrieve.
            bucket (str): The InfluxDB bucket name.
            timestep (int): The time interval in minutes for aggregation and difference calculation.
            tags (Dict[str, str] | None): Optional tags to filter the query. Defaults to None.

        Returns:
            pd.DataFrame: A DataFrame containing the accumulated values, indexed by time.
        """
        if tags is None:
            tags = {}

        fields_list = " or ".join(['r["_field"] == "{}"'.format(field) for field in fields])
        if tags:
            tags_list = " and " + " and ".join(
                ['r.{} == "{}"'.format(tag_key, tag_value) for (tag_key, tag_value) in tags.items()]
            )
        else:
            tags_list = ""

        start_str = start.isoformat()
        stop_str = stop.isoformat()

        time_interval = timedelta(minutes=timestep)
        query = """
            from(bucket: "{}")
            |> range(start: {}, stop: {})
            |> filter(fn: (r) => r["_measurement"] == "{}"{})
            |> filter(fn: (r) => {})
            |> aggregateWindow(every: {}, fn: last)
            |> difference()
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            """.format(bucket, start_str, stop_str, msname, tags_list, fields_list, time_interval)

        logger.debug("Querying InfluxDB: %s", query)

        api_queryfcast = self._influx_client.query_api()
        query_results = api_queryfcast.query_data_frame(query)
        if query_results.empty:
            results_to_return = pd.DataFrame()
        else:
            results_to_return = query_results[fields]
            results_to_return = results_to_return.set_index(query_results["_time"])
            results_to_return.index.name = None
        logger.debug(f"Query to bucket {bucket} and measurement {msname} with the fields {fields}")

        return results_to_return

    def read_accumulated_value_in_seconds(
        self,
        start: datetime,
        stop: datetime,
        msname: str,
        fields: List[str],
        bucket: str,
        duration: int,
        tags: Dict[str, str] | None = None,
    ) -> pd.DataFrame:
        """
        Reads accumulated values (differences between consecutive points) for specified fields from InfluxDB,
        with a duration specified in seconds.

        Similar to `read_accumulated_value` but allows for second-level duration specification.

        Args:
            start (datetime): The start timestamp for the query.
            stop (datetime): The stop timestamp for the query.
            msname (str): The measurement name to query.
            fields (List[str]): A list of field names to retrieve.
            bucket (str): The InfluxDB bucket name.
            duration (int): The time interval in seconds for aggregation and difference calculation.
            tags (Dict[str, str] | None): Optional tags to filter the query. Defaults to None.

        Returns:
            pd.DataFrame: A DataFrame containing the accumulated values, indexed by time.
        """
        if tags is None:
            tags = {}

        fields_list = " or ".join(['r["_field"] == "{}"'.format(field) for field in fields])
        if tags:
            tags_list = " and " + " and ".join(
                ['r.{} == "{}"'.format(tag_key, tag_value) for (tag_key, tag_value) in tags.items()]
            )
        else:
            tags_list = ""

        start_str = start.isoformat()
        stop_str = stop.isoformat()

        time_interval_str = str(int(duration)) + "s"
        query = """
            from(bucket: "{}")
            |> range(start: {}, stop: {})
            |> filter(fn: (r) => r["_measurement"] == "{}"{})
            |> filter(fn: (r) => {})
            |> aggregateWindow(every: {}, fn: last, createEmpty: false)
            |> difference()
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            """.format(bucket, start_str, stop_str, msname, tags_list, fields_list, time_interval_str)

        logger.debug("Querying InfluxDB: %s", query)

        api_queryfcast = self._influx_client.query_api()
        query_results = api_queryfcast.query_data_frame(query)
        if query_results.empty:
            results_to_return = pd.DataFrame()
        else:
            results_to_return = query_results[fields]
            results_to_return = results_to_return.set_index(query_results["_time"])
            results_to_return.index.name = None
        logger.debug(f"Query to bucket {bucket} and measurement {msname} with the fields {fields}")

        return results_to_return

    def read_average_value_in_seconds(
        self,
        bucket: str,
        measurement: str,
        fields: List[str],
        duration: int,
        tags: Dict[str, str] | None = None,
    ) -> pd.DataFrame:
        """
        Read the average value of specified fields over a time range, going back 'duration' seconds from the current
        time.

        :param measurement: The name of the measurement.
        :param fields: A list of fields to retrieve.
        :param bucket: The InfluxDB bucket name.
        :param duration: Duration in seconds to look back from the current time.
        :param tags: Optional tags to filter the query.
        :return: A DataFrame with the average value of the specified fields.
        """
        if tags is None:
            tags = {}

        # Calculate current time and start time based on duration
        stop = datetime.now().astimezone()
        start = stop - timedelta(seconds=duration)

        # Format the start and stop times as required by InfluxDB
        start_str = start.isoformat()
        stop_str = stop.isoformat()

        # Create the filter for fields
        fields_list = " or ".join([f'r["_field"] == "{field}"' for field in fields])

        # Add optional tag filters
        if tags:
            tags_list = " and " + " and ".join(
                [f'r["{tag_key}"] == "{tag_value}"' for tag_key, tag_value in tags.items()]
            )
        else:
            tags_list = ""

        # Construct the query
        query = f"""
            from(bucket: "{bucket}")
            |> range(start: {start_str}, stop: {stop_str})
            |> filter(fn: (r) => r["_measurement"] == "{measurement}"{tags_list})
            |> filter(fn: (r) => {fields_list})
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        """

        logger.debug("Querying InfluxDB with the query: %s", query)

        # Execute the query using InfluxDB client
        api_queryfcast = self._influx_client.query_api()
        query_results = api_queryfcast.query_data_frame(query)

        if query_results.empty:
            return pd.DataFrame()  # Return an empty DataFrame if no results

        # Compute the average for the relevant fields
        df_construction = query_results[fields]
        df_construction = df_construction.set_index(query_results["_time"])  # Set the timestamp as the index

        # Calculate the average, assuming we're interested in the field "total_consumption_instantaneous"
        mean_values = df_construction.mean() / 1000  # Convert to kW if needed
        last_time_step = df_construction.index[-1]  # Get the last timestamp

        # Create a DataFrame with the mean values and the last timestamp as the index
        results_to_return = pd.DataFrame(mean_values).T
        results_to_return.index = [last_time_step]

        logger.debug("Computed averages for bucket %s, measurement %s, fields %s", bucket, measurement, fields)

        return results_to_return

    def read_last_data_point(
        self, bucket: str, measurement: str, fields: List[str], tags: Dict[str, str] | None = None
    ) -> Dict[str, Any]:
        """
        Reads the last data point for specified fields from a given measurement in InfluxDB.

        Args:
            bucket (str): The InfluxDB bucket name.
            measurement (str): The measurement name to query.
            fields (List[str]): A list of field names to retrieve the last value for.
            tags (Dict[str, str] | None): Optional tags to filter the query. Defaults to None.

        Returns:
            Dict[str, Any]: A dictionary where keys are field names and values are their last recorded data points.
                            Returns an empty dictionary or an error message if no data is found or an error occurs.
        """
        if tags is None:
            tags = {}

        fields_list = " or ".join(['r["_field"] == "{}"'.format(field) for field in fields])

        if tags:
            tags_list = " and " + " and ".join(
                ['r.{} == "{}"'.format(tag_key, tag_value) for (tag_key, tag_value) in tags.items()]
            )
        else:
            tags_list = ""

        query = f"""
        from(bucket: "{bucket}")
        |> range(start: -2h)
        |> filter(fn: (r) => r["_measurement"] == "{measurement}"{tags_list})
        |> filter(fn: (r) => {fields_list})
        |> last()
        |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        """

        logger.debug("Querying InfluxDB: %s", query)

        api_queryfcast = self._influx_client.query_api()
        # Try to execute the query
        try:
            query_results = api_queryfcast.query_data_frame(query)
        except Exception as e:
            logger.info("An error occurred while querying data: %s", e)
            result = {"error": "The InfluxDB query failed to execute."}

        if query_results.empty:
            result = {"error": "The requested query returned no values from InfluxDB."}
        else:
            # Check for NaN values and replace them with 0.0
            results_to_return = query_results[fields]
            results_to_return = results_to_return.set_index(query_results["_time"])
            results_to_return.index.name = None

            # Iterate over columns (devices)
            result = {}
            for column in results_to_return.columns:
                # Iterate over rows (timestamps) for each column
                for value in results_to_return[column]:
                    if pd.notna(value):  # Check if the value is not NaN
                        result[column] = value  # Store the first numeric value found
                        break  # Exit loop after finding the first numeric value
        logger.debug("Query to bucket %s and measurement %s with the fields %s", bucket, measurement, fields)

        return result

    def get_measurements_on_bucket(self, bucket: str) -> List[str]:
        """
        Retrieves all measurement names present in a specified InfluxDB bucket.

        Args:
            bucket (str): The name of the InfluxDB bucket.

        Returns:
            List[str]: A list of measurement names found in the bucket. Returns an empty list if no measurements
                       are found or an error occurs.
        """
        query = f'''
            import "influxdata/influxdb/schema"
            schema.measurements(bucket: "{bucket}")
        '''
        try:
            result = self._influx_client.query_api().query(query=query)
            measurements = [record["_value"] for table in result for record in table.records]
            logger.debug("Found measurements in bucket %s: %s", bucket, measurements)
            return measurements
        except Exception as e:
            logger.error("Error retrieving measurements for bucket %s: %s", bucket, str(e))
            return []

    def get_fields(self, bucket: str, measurement: str) -> List[str]:
        """
        Retrieves all field names for a specific measurement within a given InfluxDB bucket.

        Args:
            bucket (str): The name of the InfluxDB bucket.
            measurement (str): The name of the measurement.

        Returns:
            List[str]: A list of field names for the specified measurement. Returns an empty list if no fields
                       are found or an error occurs.
        """
        query = f'''
            import "influxdata/influxdb/schema"
            schema.fieldKeys(bucket: "{bucket}", predicate: (r) => r._measurement == "{measurement}", start: -3h)
        '''
        try:
            result = self._influx_client.query_api().query(query=query)
            fields = [record["_value"] for table in result for record in table.records]
            logger.debug("Found fields for measurement %s in bucket %s: %s", measurement, bucket, fields)
            return fields
        except Exception as e:
            logger.error("Error retrieving fields for measurement %s in bucket %s: %s", measurement, bucket, str(e))
            return []
