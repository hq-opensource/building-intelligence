import os

from datetime import datetime

from fastapi import APIRouter, HTTPException, Path, Query, status
from fastapi.responses import JSONResponse

from common.database.influxdb import InfluxManager
from common.database.redis import RedisClient
from common.util.logging import LoggingUtil
from core_api.api.models import PreferencesType
from core_api.database.preferences_queries import PreferencesQueries, PreferencesQueriesNoDataFoundError


logger = LoggingUtil.get_logger(__name__)
logger.info("The devices API is starting at %s:", str(datetime.now().astimezone()))

PreferencesAPI = APIRouter()

# Data for the local Influx
influxdb_url = os.getenv("INFLUXDB_URL")
influxdb_org = os.getenv("INFLUXDB_ORG")
influxdb_token = os.getenv("INFLUXDB_TOKEN")
influx_manager = InfluxManager(influxdb_url, influxdb_org, influxdb_token)

# Create the redis client
redis_password = os.getenv("REDIS_PASSWORD")
redis_host = os.getenv("REDIS_HOST")
redis_port = os.getenv("REDIS_PORT")
redis_client = RedisClient(redis_host, redis_port, redis_password)

preferences_manager = PreferencesQueries(influx_manager, redis_client)


@PreferencesAPI.get(
    "/preferences/{preferences_type}",
    tags=["Data management"],
    operation_id="preferences",
    summary="Get preferences data.",
)
async def request_preferences_data(
    preferences_type: PreferencesType = Path(description="The type of data to retrieve."),  # noqa: B008
    device_id: str = Query(description="Device ID."),
    start: datetime = Query(  # noqa: B008
        description="Start timestamp.",
        example=datetime.now().replace(second=0, microsecond=0).astimezone(),  # noqa: B008
    ),
    stop: datetime = Query(  # noqa: B008
        description="Stop timestamp.",
        example=datetime.now().replace(second=0, microsecond=0).astimezone(),  # noqa: B008
    ),
    sampling_in_minutes: int = Query(
        default=10,
        description="Sampling interval in minutes.",
    ),
) -> JSONResponse:
    if not all([device_id, start, stop]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="device_id, start, and stop parameters are required.",
        )

    if (stop - start).days > 7:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Time range cannot exceed 7 days.",
        )

    if sampling_in_minutes < 1 or sampling_in_minutes > 60:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sampling interval must be between 1 and 60 minutes.",
        )

    try:
        if preferences_type == PreferencesType.TZ_SETPOINT_PREFERENCES:
            df = preferences_manager.load_comfort_setpoints(device_id, start, stop, sampling_in_minutes)
        elif preferences_type == PreferencesType.TZ_OCCUPANCY_PREFERENCES:
            df = preferences_manager.load_occupancy_preferences(device_id, start, stop, sampling_in_minutes)
        elif preferences_type == PreferencesType.VEHICLE_BRANCHED_PREFERENCES:
            df = preferences_manager.load_vehicle_branched_preferences(device_id, start, stop, sampling_in_minutes)
        elif preferences_type == PreferencesType.VEHICLE_SOC_PREFERENCES:
            df = preferences_manager.load_vehicle_soc_preferences(device_id, start, stop, sampling_in_minutes)
        elif preferences_type == PreferencesType.ELECTRIC_BATTERY_SOC_PREFERENCES:
            df = preferences_manager.load_electric_battery_soc_preferences(device_id, start, stop, sampling_in_minutes)
        elif preferences_type == PreferencesType.WATER_HEATER_CONSUMPTION_PREFERENCES:
            df = preferences_manager.load_water_heater_consumption_preferences(
                device_id, start, stop, sampling_in_minutes
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Data type {preferences_type} not implemented."
            )
    except PreferencesQueriesNoDataFoundError as ex:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail=str(ex)) from ex

    if df.empty:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No data found for {preferences_type}.")
    else:
        retrieved_data = dict(
            zip(
                df["timestamp"].apply(lambda ts: ts.isoformat()),
                df["data"],
                strict=False,
            )
        )

    return JSONResponse(content=retrieved_data)
