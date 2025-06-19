from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from common.util.logging import LoggingUtil
from grid_services_api.api.publisher import publish


logger = LoggingUtil.get_logger(__name__)
logger.info("The Day Ahead Coordination API is starting at %s:", str(datetime.now().astimezone()))

# Create the API
DayAheadAPI = APIRouter()


HORIZON = 144


@DayAheadAPI.post(
    "/coordinatedac",
    tags=["Day Ahead Coordination"],
)
async def execute_day_ahead_coodination() -> JSONResponse:
    """Starts the coordination grid function."""
    # Create a log
    logger.info("Executing the Day Ahead Coordination.")
    price_list = [0.07] * HORIZON
    iteration = 0
    now = datetime.now().astimezone()
    rpc_payload: Dict[str, Any] = {
        "method": "mpc_day_ahead_coordination",
        "params": {"iteration": iteration, "prices": price_list, "date": now.isoformat()},
    }

    # Build topic including the prefix
    from grid_services_api.app import labels_channels

    topic = labels_channels["grid_functions_prefix"] + rpc_payload["method"]

    return await publish(rpc_payload, topic)


@DayAheadAPI.post(
    "/request_optimization_status",
    tags=["Day Ahead Coordination"],
)
async def request_optimization_status() -> JSONResponse:
    """Retrieves the optimization status."""

    # Create a log
    logger.info("Retrieving optimization status.")
    # Build the message
    rpc_payload: Dict[str, Any] = {
        "method": "mpc_retrieve_optimization_status",
        "params": {},
    }

    # Build topic including the prefix
    from grid_services_api.app import labels_channels

    topic = labels_channels["grid_functions_prefix"] + rpc_payload["method"]

    return await publish(rpc_payload, topic)
