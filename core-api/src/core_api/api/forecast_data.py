import os

from datetime import datetime

from fastapi import APIRouter, HTTPException, Path, Query, status
from fastapi.responses import JSONResponse
from faststream.redis import RedisBroker

from common.database.redis import RedisClient
from common.util.logging import LoggingUtil
from core_api.api.models import ForecastType
from core_api.database.forecast_queries import ForecastQueries


logger = LoggingUtil.get_logger(__name__)
logger.info("The devices API is starting at %s:", str(datetime.now().astimezone()))

# region to create the API
ForecastAPI = APIRouter()

redis_password = os.getenv("REDIS_PASSWORD")
redis_host = os.getenv("REDIS_HOST")
redis_port = os.getenv("REDIS_PORT")
redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}"
redis_client = RedisClient(redis_host, redis_port, redis_password)

redis_broker = RedisBroker(redis_url)

# Create the forecasts queries to execute RPC to the data engine
forecast_queries = ForecastQueries(redis_client, redis_broker)


@ForecastAPI.get(
    "/forecast/{forecast_type}",
    tags=["Data management"],
    operation_id="non_controllable_loads_forecast",
    summary="Get forecasts of the non controllable loads.",
)
async def request_forecast_data(
    forecast_type: ForecastType = Path(description="The type of data to retrieve."),  # noqa: B008
    start: datetime = Query(  # noqa: B008
        description="The ISO 8601 formatted start timestamp.",
        example=datetime.now().replace(second=0, microsecond=0).astimezone(),  # noqa: B008
    ),
    stop: datetime = Query(  # noqa: B008
        description="The ISO 8601 formatted stop timestamp.",
        example=datetime.now().replace(second=0, microsecond=0).astimezone(),  # noqa: B008
    ),
) -> JSONResponse:
    """
    Get forecasts of the non controllable loads.

    Args:
        forecast_type (ForecastType): The type of data to retrieve.
        start (datetime): The start timestamp for the forecast data.
        stop (datetime): The stop timestamp for the forecast data.

    Returns:
        JSONResponse: A response containing the forecast data.
    """
    if forecast_type == ForecastType.NON_CONTROLLABLE_LOADS:
        retrieved_data = await forecast_queries.load_ec_non_controllable_loads_forecast(start, stop)
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Data type {forecast_type} not found.",
        )

    return JSONResponse(content=retrieved_data)
