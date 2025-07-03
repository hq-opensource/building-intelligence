"""
This module defines the API endpoints for Day Ahead Coordination within the Grid Services API.

It provides functionalities to initiate day-ahead coordination processes and
retrieve the optimization status from the Model Predictive Control (MPC) system.
"""

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
    """
    Initiates the Day Ahead Coordination grid function.

    This endpoint triggers the day-ahead coordination process, which involves
    calculating prices and preparing an RPC payload for the MPC (Model Predictive Control)
    system. The payload includes the current iteration, a list of prices, and the
    current timestamp. This message is then published to a predefined topic
    for the grid functions.

    Returns:
        JSONResponse: The result of the publish operation, typically indicating
                      the success or failure of sending the RPC payload.
    """
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
    """
    Retrieves the current optimization status from the MPC system.

    This endpoint constructs an RPC payload to request the optimization status
    and publishes it to a predefined topic for grid functions. The response
    from the MPC system will contain details about the ongoing or last completed
    optimization process.

    Returns:
        JSONResponse: The result of the publish operation, typically indicating
                      the success or failure of sending the RPC payload.
    """

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
