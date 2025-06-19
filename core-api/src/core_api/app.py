import asyncio
import datetime
import os

from typing import Any, Dict, Optional, Tuple

import uvicorn

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.responses import FileResponse, Response
from fastapi_mcp import FastApiMCP
from faststream.redis import RedisBroker

from common.database.influxdb import InfluxManager
from common.database.redis import RedisClient
from common.util.logging import LoggingUtil
from core_api.api.building import BuildingAPI
from core_api.api.devices import DevicesAPI
from core_api.api.forecast_data import ForecastAPI
from core_api.api.historic_data import HistoricAPI
from core_api.api.preferences_data import PreferencesAPI
from core_api.api.weather_data import WeathertAPI
from core_api.device.realtime import RealtimeDataManager
from core_api.schedule.models import ControlType
from core_api.schedule.monitor import SchedulerMonitor


logger: LoggingUtil = LoggingUtil.get_logger(__name__)

# Constants
redis_password: Optional[str] = os.getenv("REDIS_PASSWORD")
redis_host: Optional[str] = os.getenv("REDIS_HOST")
redis_port: Optional[str] = os.getenv("REDIS_PORT")

# Create the redis client
redis_client: RedisClient = RedisClient(redis_host, redis_port, redis_password)

# Data for the local Influx
influxdb_url: Optional[str] = os.getenv("INFLUXDB_URL")
influxdb_org: Optional[str] = os.getenv("INFLUXDB_ORG")
influxdb_token: Optional[str] = os.getenv("INFLUXDB_TOKEN")
influx_manager: InfluxManager = InfluxManager(influxdb_url, influxdb_org, influxdb_token)

SCHEDULE_DEFAULT_TIME_STEP_DURATION_IN_SECONDS: int = 60  # seconds
schedule_time_step_duration_in_seconds: int = int(
    os.getenv("SCHEDULE_TIME_STEP_DURATION_IN_SECONDS", str(SCHEDULE_DEFAULT_TIME_STEP_DURATION_IN_SECONDS))
)

redis_url: str = f"redis://:{redis_password}@{redis_host}:{redis_port}"
realtime_data: RealtimeDataManager = RealtimeDataManager(influx_manager, redis_client)

# Create the FastAPI app
main_app: FastAPI = FastAPI(
    title="Peripheral API",
    description="This API exposes the endpoints to interact with the Peripheral core application.",
    version="0.0.1",
    contact={"name": "Hydro-Quebec", "email": "oviedocepeda.juancarlos@hydroquebec.com"},
    license_info={
        "name": "LiLiQ-P",
        "url": "https://forge.gouv.qc.ca/licence/en/liliq-p/",
    },
)

# Include routers
PREFIX_DATA: str = "/data"
main_app.include_router(BuildingAPI, prefix="/building")
main_app.include_router(DevicesAPI, prefix="/devices")
main_app.include_router(ForecastAPI, prefix=PREFIX_DATA)
main_app.include_router(HistoricAPI, prefix=PREFIX_DATA)
main_app.include_router(PreferencesAPI, prefix=PREFIX_DATA)
main_app.include_router(WeathertAPI, prefix=PREFIX_DATA)

# Define the root route
html_root_file: str = os.path.join(os.path.dirname(__file__), "html", "root.html")


@main_app.get("/", response_class=FileResponse, include_in_schema=False)
async def root() -> Response:
    """Root endpoint."""
    return FileResponse(html_root_file)


# Create and mount the MCP server
mcp_app: FastApiMCP = FastApiMCP(
    main_app,
    name="Peripheral API MCP",
    description="MCP server for Peripheral API, exposing endpoints as tools for AI agents.",
    base_url="http://localhost:8000",
    describe_all_responses=True,
    describe_full_response_schema=True,
)
mcp_app.mount()


def update_setpoints(system_just_started: bool = False) -> None:
    monitor: SchedulerMonitor = SchedulerMonitor(redis_client, influx_manager, schedule_time_step_duration_in_seconds)

    timestamp: datetime.datetime = datetime.datetime.now().replace(microsecond=0).astimezone()
    changed_count: int = 0

    # Initialize map of devices
    devices: Dict[str, Dict[str, Any]] = {
        device["entity_id"]: device for device in redis_client.safe_read_from_redis("user_devices") or []
    }
    for device in devices:
        data_and_changed: Tuple[Optional[Any], bool] = monitor.get_device_event_data_with_changed_flag(
            device, ControlType.CONTROL_SETPOINT, timestamp
        )
        data, changed = data_and_changed
        if data and (changed or system_just_started):
            changed_count += 1
            set_point: float = data.data
            try:
                asyncio.run(realtime_data.set_device_state(RedisBroker(redis_url), device, set_point))
                logger.info(
                    "Setpoint set to %s for device_id %s at %s. Event: %s", set_point, device, timestamp, data.event_id
                )
            except Exception as e:
                logger.error("Error setting setpoint for device %s: %s", device, e)
                continue
    if changed_count > 0:
        logger.info("Changed setpoints for %s devices at %s", changed_count, timestamp)
    else:
        logger.info("No setpoints changed at %s", timestamp)


def main() -> None:
    port: int = int(os.getenv("CORE_API_PORT", "8000"))
    scheduler: BackgroundScheduler = BackgroundScheduler()
    scheduler.start()

    # Ensure all programmed setpoints are applied following startup
    update_setpoints(system_just_started=True)

    # Set the schedule to trigger every XX seconds
    trigger: CronTrigger = CronTrigger(year="*", month="*", day="*", hour="*", minute="*", second="0")
    scheduler.add_job(
        update_setpoints,
        trigger=trigger,
        args=[],
        name="monitor_schedule",
    )

    # Run the FastAPI server with MCP mounted
    config: uvicorn.Config = uvicorn.Config("core_api.app:main_app", host="0.0.0.0", port=port, reload=True)
    server: uvicorn.Server = uvicorn.Server(config)
    logger.info("Starting FastAPI server with MCP on port %s", port)
    asyncio.run(server.serve())


if __name__ == "__main__":
    main()
