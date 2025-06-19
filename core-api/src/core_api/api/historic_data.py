import os

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status
from fastapi.responses import JSONResponse

from common.database.influxdb import InfluxManager
from common.database.redis import RedisClient
from common.util.logging import LoggingUtil
from core_api.api.models import HistoricType
from core_api.database.historic_queries import HistoricQueries


logger = LoggingUtil.get_logger(__name__)


logger = LoggingUtil.get_logger(__name__)
logger.info("The devices API is starting at %s:", str(datetime.now().astimezone()))

# region to create the API
HistoricAPI = APIRouter()

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

# Create the dynamic writer
historic_queries = HistoricQueries(influx_manager, redis_client)


@HistoricAPI.get(
    "/historic/{historic_type}",
    tags=["Data management"],
    operation_id="controllable_loads_historic",
    summary="Get historical data of controllable loads.",
)
async def request_historical_data(
    historic_type: HistoricType = Path(description="The type of data to retrieve."),  # noqa: B008
    start: datetime = Query(  # noqa: B008
        description="The ISO 8601 formatted start timestamp.",
        example=datetime.now().replace(second=0, microsecond=0).astimezone(),  # noqa: B008
    ),
    stop: datetime = Query(  # noqa: B008
        description="The ISO 8601 formatted stop timestamp.",
        example=datetime.now().replace(second=0, microsecond=0).astimezone(),  # noqa: B008
    ),
    device_id: Annotated[str | None, Query(description="Device ID, if applicable.")] = None,  # noqa: B008
) -> JSONResponse:
    if historic_type == HistoricType.TZ_TEMPERATURE:
        if device_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="device_id parameter is required for temperature data.",
            )
        retrieved_data = historic_queries.load_tz_temperature_historic(start, stop, device_id)
    elif historic_type == HistoricType.TZ_HISTORIC_SETPOINT:
        retrieved_data = historic_queries.load_tz_setpoint_historic(start, stop, str(device_id))
    elif historic_type == HistoricType.TZ_ELECTRIC_CONSUMPTION:
        retrieved_data = historic_queries.load_tz_electric_consumption(start, stop, str(device_id))
    elif historic_type == HistoricType.NON_CONTROLLABLE_LOADS:
        retrieved_data = historic_queries.load_ec_non_controllable_loads_historic(start, stop)
    elif historic_type == HistoricType.VEHICLE_CONSUMPTION:
        retrieved_data = historic_queries.load_vehicle_consumption_historic(start, stop)
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Data type {historic_type} not found.",
        )

    return JSONResponse(content=retrieved_data)
