import asyncio
import os

from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from faststream import FastStream, context
from faststream.redis import RedisBroker

from common.database.influxdb import InfluxManager
from common.database.redis import RedisClient
from common.util.logging import LoggingUtil
from data_engine.database.influx_mirror import InfluxMirror
from data_engine.events.forecaster_rpc_answer import forecast_router
from data_engine.grap.detect_blackout import DetectBlackout


logger = LoggingUtil.get_logger(__name__)


async def blackout_detection(influx_manager: InfluxManager, redis_client: RedisClient, broker: RedisBroker) -> None:
    """Background task to detect blackouts."""
    logger.info("The blackout detection mechanism is starting at %s:", str(datetime.now().astimezone()))

    # Create the blackout detection object
    detect_blackout = DetectBlackout(influx_manager, redis_client, broker)

    while True:
        detect_blackout.detect_blackout_info_locally()
        await asyncio.sleep(10)  # Wait for 10 seconds before printing again


def start_influx_mirror() -> None:
    """Starts the InfluxDB mirroring task."""
    mirror = InfluxMirror()
    mirror.run()


async def run_tasks(
    broker_events_app: FastStream, influx_manager: InfluxManager, redis_client: RedisClient, broker: RedisBroker
) -> None:
    """Run broker and alive task concurrently."""
    # Create a task for the broker and the alive task, and run them concurrently
    await asyncio.gather(broker_events_app.run())


def main() -> None:
    """Launched with `poetry run service` at root level"""
    scheduler = BackgroundScheduler()
    scheduler.start()

    # Add InfluxMirror task to scheduler
    scheduler.add_job(start_influx_mirror, "interval", hours=1, next_run_time=datetime.now())

    # Redis event broker setup
    redis_password = os.getenv("REDIS_PASSWORD")
    redis_host = os.getenv("REDIS_HOST")
    redis_port = os.getenv("REDIS_PORT")
    redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}"
    broker = RedisBroker(redis_url)

    # Set the scheduler in the context so that it can be accessed by the routers
    context.set_global("scheduler", scheduler)

    # Include routers on the broker
    broker.include_router(forecast_router)
    # broker.include_router(telemetry_router)

    # Create the app
    broker_events_app = FastStream(broker)

    # Create the influx manager
    influxdb_url = os.getenv("INFLUXDB_URL")
    influxdb_org = os.getenv("INFLUXDB_ORG")
    influxdb_token = os.getenv("INFLUXDB_TOKEN")
    influx_manager = InfluxManager(influxdb_url, influxdb_org, influxdb_token)

    # Create the redis client
    redis_client = RedisClient(redis_host, redis_port, redis_password)

    # Run the broker and the alive task concurrently
    asyncio.run(run_tasks(broker_events_app, influx_manager, redis_client, broker))


if __name__ == "__main__":
    main()
