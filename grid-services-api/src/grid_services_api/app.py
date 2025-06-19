import os

import uvicorn

from fastapi import FastAPI
from fastapi.responses import FileResponse, Response
from faststream.redis import RedisBroker

from common.database.redis import RedisClient
from grid_services_api.api.direct_control import DirectControlAPI
from grid_services_api.api.mpc import MpcAPI


redis_password = os.getenv("REDIS_PASSWORD")
redis_host = os.getenv("REDIS_HOST")
redis_port = os.getenv("REDIS_PORT")
redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}"
redis_broker = RedisBroker(redis_url)

# Redis event broker setup
redis_password = os.getenv("REDIS_PASSWORD")
redis_host = os.getenv("REDIS_HOST")
redis_port = os.getenv("REDIS_PORT")
redis_client = RedisClient(redis_host, redis_port, redis_password)
# Read labels for Redis channels
labels_channels = redis_client.safe_read_from_redis("labels_channels")


# Create the API
main_app = FastAPI(
    title="Peripheral Grid Services API",
    description="This API exposes the endpoints to interact with the Peripheral Grid Services.",
    version="0.0.1",
    contact={"name": "Hydro-Quebec", "email": "hydroquebec@hydroquebec.com"},
    license_info={
        "name": "LiLiQ-P",
        "url": "https://forge.gouv.qc.ca/licence/en/liliq-p/",
    },
)

main_app.include_router(DirectControlAPI, prefix="/direct_control")
main_app.include_router(MpcAPI, prefix="/mpc")

# For now, these APIs are not fully working so we're not including them in the main app
# main_app.include_router(DayAheadAPI, prefix="/dac")
# main_app.include_router(TariffsAPI, prefix="/tariffs")
# main_app.include_router(PaidControlAPI, prefix="/paid_control")
# main_app.include_router(FlexibilityAPI, prefix="/flexibility")


@main_app.get("/", response_class=FileResponse)
async def root() -> Response:
    """Root endpoint."""
    html_root_file = os.path.join(os.path.dirname(__file__), "html", "root.html")
    return FileResponse(html_root_file)


def main() -> None:
    port = int(os.getenv("GRID_SERVICES_API_PORT", 8001))
    uvicorn.run("grid_services_api.app:main_app", host="0.0.0.0", port=port, reload=True)


if __name__ == "__main__":
    main()
