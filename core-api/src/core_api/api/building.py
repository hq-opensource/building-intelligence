import os

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from numpy import around

from common.database.influxdb import InfluxManager
from common.database.redis import RedisClient
from common.util.logging import LoggingUtil


logger = LoggingUtil.get_logger(__name__)
logger.info("The building API is starting at %s:", str(datetime.now().astimezone()))

# region to create the API
BuildingAPI = APIRouter()

# Data for the local Influx
influxdb_url = os.getenv("INFLUXDB_URL")
influxdb_org = os.getenv("INFLUXDB_ORG")
influxdb_token = os.getenv("INFLUXDB_TOKEN")
influx_manager = InfluxManager(influxdb_url, influxdb_org, influxdb_token)

redis_password = os.getenv("REDIS_PASSWORD")
redis_host = os.getenv("REDIS_HOST")
redis_port = os.getenv("REDIS_PORT")

# Create the redis client
redis_client = RedisClient(redis_host, redis_port, redis_password)

# Define required variables
labels_influx = redis_client.safe_read_from_redis("influxdb_mapping")
labels_redis = redis_client.safe_read_from_redis("labels_redis")


# Get all installed devices
@BuildingAPI.get(
    "/consumption",
    tags=["Building management"],
    operation_id="total_building_consumption",
    summary="Get the total consumption of the building.",
)
async def get_building_consumption(
    duration: int = Query(
        60,
        description="Duration in seconds to compute the average consumption",
        ge=10,  # Ensure duration is at least 10 seconds
    ),
) -> JSONResponse:
    # Check if duration is an integer
    if not isinstance(duration, int):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duration must be an integer representing seconds.",
        )

    try:
        # Read total building consumption from InfluxDB
        bucket = labels_influx["net_power"]["bucket"]
        measurement = labels_influx["net_power"]["measurement"]
        tags = labels_influx["net_power"]["tags"]
        field = labels_influx["net_power"]["field"]
        fields = [field]

        # Extend tags to include measure
        tags["_type"] = "measure"

        # Retrieve state
        retrieved_state = influx_manager.read_average_value_in_seconds(bucket, measurement, fields, duration, tags)

        # Send response
        if retrieved_state.empty:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve the total consumption of the building",
            )

        return JSONResponse(
            content={"total_consumption": float(around(retrieved_state.values, 2))},
            status_code=status.HTTP_200_OK,
        )

    except Exception as e:
        logger.error("Error trying to answer the api call: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error") from e


@BuildingAPI.get(
    "/grap",
    tags=["Building management"],
    operation_id="grap_values",
    summary="Get the GRAP values (state and limit)",
)
async def get_grap_values() -> JSONResponse:
    """
    Retrieves the 'grap_state' and 'grap_limit' values from Redis and returns them in a dictionary.
    """
    try:
        # Read 'grap_state' and 'grap_limit' from Redis
        grap = redis_client.safe_read_from_redis(labels_redis["grap_name"])
        grap_state = grap["grap_state"]
        grap_limit = grap["grap_limit"]

        # Prepare the response
        response = {"grap_state": grap_state, "grap_limit": grap_limit}

        return JSONResponse(content=response, status_code=status.HTTP_200_OK)

    except Exception as e:
        logger.error("Error retrieving grap values from Redis: %s", e)
        raise HTTPException(status_code=500, detail="Internal Server Error") from e
