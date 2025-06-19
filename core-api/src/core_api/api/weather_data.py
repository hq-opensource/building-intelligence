import os

from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Path, Query, status
from fastapi.responses import JSONResponse

from common.database.influxdb import InfluxManager
from common.database.redis import RedisClient
from common.util.logging import LoggingUtil
from core_api.api.models import WeatherForecastType, WeatherHistoricType
from core_api.database.weather_queries import WeatherQueries


logger = LoggingUtil.get_logger(__name__)
logger.info("The devices API is starting at %s:", str(datetime.now().astimezone()))

# region to create the API
WeathertAPI = APIRouter()

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


# Create the dynamic writer
weather_queries = WeatherQueries(influx_manager, redis_client)


@WeathertAPI.get(
    "/weather/forecast/{variable}",
    tags=["Data management"],
    operation_id="weather_forecast",
    summary="Get the weather forecast data.",
)
async def request_temperature_forecast(
    variable: WeatherForecastType = Path(description="The type of data to retrieve."),  # noqa: B008
    start: datetime = Query(  # noqa: B008
        description="The ISO 8601 formatted start timestamp.",
        example=datetime.now().replace(second=0, microsecond=0).astimezone(),  # noqa: B008
    ),  # noqa: B008
    stop: datetime = Query(  # noqa: B008
        description="The ISO 8601 formatted stop timestamp.",
        example=datetime.now().replace(second=0, microsecond=0).astimezone(),  # noqa: B008
    ),
) -> JSONResponse:
    """Retrieves weather forecast from a cloud InfluxDB database that is mirrored in the local InfluxDB database."""

    now = datetime.now().astimezone().replace(second=0, microsecond=0)

    # Validate start and stop times
    if start < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Start time {start} must be in the future (now: {now})",
        )
    if stop < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stop time {stop} must be in the future (now: {now})",
        )
    if start >= stop:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Start time {start} must be before stop time {stop}",
        )
    max_future = now + timedelta(hours=120)
    if stop > max_future:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stop time {stop} cannot be more than 120 hours into the future (max: {max_future})",
        )

    try:
        weather_data = weather_queries.retrieve_weather_forecast(start, stop, variable)
        logger.debug("Weather data retrieved: %s", weather_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving weather data: {e}",
        ) from e

    return JSONResponse(content=weather_data)


@WeathertAPI.get(
    "/weather/historic/{variable}",
    tags=["Data management"],
    operation_id="weather_historic",
    summary="Get the weather historic data.",
)
async def request_weather_historic(
    variable: WeatherHistoricType = Path(description="The type of data to retrieve."),  # noqa: B008
    start: datetime = Query(  # noqa: B008
        description="The ISO 8601 formatted start timestamp.",
        example=datetime.now().replace(second=0, microsecond=0).astimezone(),  # noqa: B008
    ),  # noqa: B008
    stop: datetime = Query(  # noqa: B008
        description="The ISO 8601 formatted stop timestamp.",
        example=datetime.now().replace(second=0, microsecond=0).astimezone(),  # noqa: B008
    ),
) -> JSONResponse:
    """Retrieves weather historic data from the local InfluxDB database."""

    now = datetime.now().astimezone().replace(second=0, microsecond=0)

    # Validate start and stop times
    if start > now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Start time {start} must be in the past (now: {now})",
        )
    if stop > now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stop time {stop} must be in the past (now: {now})",
        )
    if start >= stop:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Start time {start} must be before stop time {stop}",
        )

    try:
        weather_data = weather_queries.retrieve_weather_historic(start, stop, variable)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving weather data: {e}",
        ) from e

    return JSONResponse(content=weather_data)
