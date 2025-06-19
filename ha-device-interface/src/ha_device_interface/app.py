import asyncio
import os

from faststream import FastStream
from faststream.redis import RedisBroker

from common.util.logging import LoggingUtil
from ha_device_interface.control.subscriber import device_interface_router


logger = LoggingUtil.get_logger(__name__)


def main() -> None:
    """Launched with `poetry run service` at root level"""

    # Redis event broker setup
    redis_password = os.getenv("REDIS_PASSWORD")
    redis_host = os.getenv("REDIS_HOST")
    redis_port = os.getenv("REDIS_PORT")
    redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}"
    broker = RedisBroker(redis_url)

    # Include routers on the broker
    broker.include_router(device_interface_router)

    # Create the app
    broker_events_app = FastStream(broker)

    # Start the subscription to the forecasters
    asyncio.run(broker_events_app.run())


if __name__ == "__main__":
    main()
