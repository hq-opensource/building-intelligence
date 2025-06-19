import os

from time import time
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from influxdb_client import InfluxDBClient


class RetrieveDataForCloud:
    def __init__(self, influx_client: InfluxDBClient) -> None:
        self._influx_client = influx_client

    def retrieve_all_data(self, start_range: int = -30) -> Dict[str, Any]:
        """Retrieve all data and organize it into a nested dictionary."""

        # Retrieve all the data
        all_dataframes = self._retrieve_all_dataframes(start_range)

        # Initialize the nested dictionary to store results
        values: Dict = {}

        # Process each DataFrame in the dictionary
        for key, df in all_dataframes.items():
            if not df.empty:
                values[key] = {}
                for column in df.columns:
                    # Get the last value in each column
                    value = float(df[column].iloc[-1])
                    values[key][column] = value

        # Add the latitude and longitude
        values["latitude"] = float(os.getenv("LATITUDE", "46.562261"))
        values["longitude"] = float(os.getenv("LONGITUDE", "-72.772112"))

        # Build telemetry
        telemetry = {"ts": int(round(time() * 1000)), "values": values}

        return telemetry

    def _retrieve_all_dataframes(self, start_range: int = -30) -> Dict[str, pd.DataFrame]:
        """Fetch last data points for all 'real' measurements in all buckets."""
        all_dataframes = {}
        buckets = self._get_all_buckets()

        for bucket in buckets:
            real_measurements = self._get_measurements_with_real(bucket)
            if len(real_measurements) > 0:
                for measurement in real_measurements:
                    fields = self._get_fields_for_measurement(bucket, measurement)
                    if fields:
                        last_data = self._read_last_data_point_seconds(
                            bucket, measurement, fields, start_range=start_range
                        )
                        all_dataframes[f"{measurement}"] = last_data

        return all_dataframes

    def _read_last_data_point_seconds(
        self, bucket: str, measurement: str, fields: list, tags: dict = {}, start_range: int = -30
    ) -> pd.DataFrame:
        """Reads the last data point from InfluxDB within the specified time range in seconds."""

        # Create the fields list for the query
        fields_list = " or ".join([f'r["_field"] == "{field}"' for field in fields])

        # Create the tags list for the query
        tags_list = (
            " and " + " and ".join([f'r.{tag_key} == "{tag_value}"' for (tag_key, tag_value) in tags.items()])
            if tags
            else ""
        )

        # InfluxDB query
        query = f"""
        from(bucket: "{bucket}")
        |> range(start: {start_range}s)
        |> filter(fn: (r) => r["_measurement"] == "{measurement}"{tags_list})
        |> filter(fn: (r) => {fields_list})
        |> last()
        |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        """

        api_query = self._influx_client.query_api()
        query_results = api_query.query_data_frame(query)

        if query_results.empty:
            return pd.DataFrame()
        else:
            # Process the resulting dataframe and extract only the fields that exist in the results
            query_results.replace(np.nan, 0.0, inplace=True)
            query_results = query_results.set_index(query_results["_time"])
            query_results.index.name = None

            # Validate and filter fields that exist in the results
            existing_fields = [field for field in fields if field in query_results.columns]
            if not existing_fields:
                return pd.DataFrame()  # Return an empty DataFrame if no fields match

            resulting_df = query_results[existing_fields]
            return resulting_df

    def _get_all_buckets(self) -> List[str]:
        """Retrieve all bucket names."""
        buckets_api = self._influx_client.buckets_api()
        buckets = buckets_api.find_buckets().buckets
        all_buckets = [bucket.name for bucket in buckets]
        return all_buckets

    def _get_measurements_with_real(self, bucket: str) -> List[str]:
        """Retrieve all measurements containing the word 'real' from a bucket."""
        query = f"""
        import "influxdata/influxdb/schema"
        schema.measurements(bucket: "{bucket}")
        """
        api_query = self._influx_client.query_api()
        result = api_query.query(query)
        measurements = [record.get_value() for table in result for record in table.records]
        measurements_with_real = [m for m in measurements if "real" in m]
        return measurements_with_real

    def _get_fields_for_measurement(self, bucket: str, measurement: str) -> List[str]:
        """Retrieve all fields for a specific measurement."""
        query = f"""
        import "influxdata/influxdb/schema"
        schema.measurementFieldKeys(
            bucket: "{bucket}",
            measurement: "{measurement}"
        )
        """
        api_query = self._influx_client.query_api()
        result = api_query.query(query)

        if not result:
            fields = []
        else:
            fields = [record["_value"] for table in result for record in table.records]

        return fields
