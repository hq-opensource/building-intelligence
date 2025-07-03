import os

from datetime import datetime
from typing import Dict

from fastapi import APIRouter, Body, HTTPException, Path, Query, status
from fastapi.responses import JSONResponse
from faststream.redis import RedisBroker

from common.database.influxdb import InfluxManager
from common.database.redis import RedisClient
from common.util.logging import LoggingUtil
from core_api.device.historical import HistoricalDataReader
from core_api.device.realtime import RealtimeDataManager
from core_api.schedule.device_scheduler import DeviceScheduler


logger = LoggingUtil.get_logger(__name__)
logger.info("The devices API is starting at %s:", str(datetime.now().astimezone()))

# region to create the API
DevicesAPI = APIRouter()

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
historical_data = HistoricalDataReader(influx_manager, redis_client)
redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}"
realtime_data = RealtimeDataManager(influx_manager, redis_client)

# ================================================================================================
# POST APIs
# ================================================================================================


# Define the API to send the dynamic setpoint
@DevicesAPI.post(
    "/setpoint/{device_id}",
    tags=["Device management"],
    operation_id="adjust_setpoints",
    summary="Adjust the setpoint of a device using its ID.",
)
async def set_device_id_setpoint(
    device_id: str = Path(description="ID of the device."),
    setpoint: float = Query(description="The desired setpoint."),
) -> JSONResponse:
    """
    Adjust the setpoint of a device using its ID.

    Args:
        device_id (str): ID of the device.
        setpoint (float): The desired setpoint.

    Returns:
        JSONResponse: A response indicating that the setpoint was successfully applied.
    """
    logger.info(f"Received set device setpoint API request. Device ID: {device_id} Setpoint: {setpoint}")
    if not realtime_data.has_device(device_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Device {device_id} not found.")

    dispatches: Dict[str, Dict[datetime, float]] = {
        device_id: {datetime.now().replace(microsecond=0).astimezone(): setpoint}
    }

    # save setpoint as a new dispatche in schedule
    DeviceScheduler.save_schedule(100, dispatches, redis_client, influx_manager, from_direct_control=True)

    await realtime_data.set_device_state(RedisBroker(redis_url), device_id, setpoint)
    return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "Setpoint successfully applied."})


@DevicesAPI.post(
    "/schedule/{priority}",
    tags=["Device management"],
    operation_id="schedule_setpoints",
    summary="Schedule the dispatch of a lists of devices as timeseries.",
)
async def set_device_dispatches_schedule(
    priority: int = Path(
        description="Priority level applied to all dispatches in this request. Must be an integer between 0 and 100 inclusive. Higher values indicate higher priority."
    ),
    dispatches: Dict[str, Dict[datetime, float]] = Body(  # noqa: B008
        description="Devices...",
        examples=[
            {
                "device_id_1": {
                    "2025-04-01T07:59:00-04:00": 21.0,
                    "2025-04-01T08:00:00-04:00": 17.5,
                    "2025-04-01T08:01:00-04:00": 17.0,
                },
                "device_id_2": {
                    "2025-04-02T07:59:00-04:00": 21.0,
                    "2025-04-02T08:00:00-04:00": 17.5,
                    "2025-04-02T08:01:00-04:00": 17.0,
                },
                "device_id_3": {
                    "2025-04-03T07:59:00-04:00": 21.0,
                    "2025-04-03T08:00:00-04:00": 17.5,
                    "2025-04-03T08:01:00-04:00": 17.0,
                },
            }
        ],
    ),
) -> JSONResponse:
    """
    Schedule the dispatch of a lists of devices as timeseries.

    Args:
        priority (int): Priority level applied to all dispatches in this request.
        dispatches (Dict[str, Dict[datetime, float]]): A dictionary where keys are device IDs and values are
                                                      dictionaries of datetime and setpoint pairs.

    Returns:
        JSONResponse: A response indicating that the schedule was saved successfully.
    """
    # Validate priority
    if not (0 <= priority <= 100):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid priority value: {priority}. Priority must be between 0 and 100 inclusive.",
        )

    logger.debug("Received dispatches schedule API request with priority %s for devices: %s", priority, dispatches)

    DeviceScheduler.save_schedule(priority, dispatches, redis_client, influx_manager)

    return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "Schedule saved successfully"})


# Get all installed devices
@DevicesAPI.get(
    "/",
    tags=["Device management"],
    operation_id="get_controllable_devices",
    summary="Get the list of devices.",
)
async def get_devices() -> JSONResponse:
    """
    Get the list of devices.

    Returns:
        JSONResponse: A response containing the list of devices.
    """
    try:
        # Read from redis the devices
        logger.debug("Retrieving list of devices from RedisDB.")
        devices = redis_client.safe_read_from_redis("user_devices")
        logger.debug("Answering the API call using the information from redis.")
        # Create the response for the API call if publishing is successful
        response = JSONResponse(
            content={"content": devices},  # Automatically serializes list of dictionaries
            status_code=status.HTTP_200_OK,
        )
        return response

    except Exception as e:
        logger.error(f"Error trying to answer the api call: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error") from e


# Get device state
@DevicesAPI.get(
    "/state/{device_id}",
    tags=["Device management"],
    operation_id="get_device_state",
    summary="Get the state of a device.",
)
async def get_device_state(
    device_id: str = Path(description="ID of the device."),
    field: str | None = Query(default=None, description="Optional field of the state to read."),
) -> float:
    """
    Get the state of a device.

    Args:
        device_id (str): ID of the device.
        field (str | None): Optional field of the state to read.

    Returns:
        float: The state of the device.
    """
    if not realtime_data.has_device(device_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Device {device_id} not found.")

    return await realtime_data.get_device_state(RedisBroker(redis_url), device_id, field)
