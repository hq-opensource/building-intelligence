"""
This module defines the API endpoints for Flexibility Requests within the Grid Services API.

It provides functionalities to request and estimate the flexibility of connected
devices, typically for direct load control purposes.
"""

from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from common.util.logging import LoggingUtil
from grid_services_api.api.publisher import publish


logger = LoggingUtil.get_logger(__name__)
logger.info("The Flexibility API is starting at %s:", str(datetime.now().astimezone()))

# Create the API
FlexibilityAPI = APIRouter()


@FlexibilityAPI.get(
    "/getflexibility",
    tags=["Flexibility Requests"],
)
async def get_flexibility(
    duration: int = Query(
        ...,
        title="Duration",
        description="Seconds to compute the consumption",
        ge=60,
        le=600,
    ),
) -> JSONResponse:
    """
    Requests the flexibility from all subscribed users or devices.

    This endpoint sends an RPC request to estimate the flexibility of connected
    devices over a specified duration. The duration parameter defines the
    time window in seconds for which the consumption should be computed.
    The request is then published to a topic for direct load control flexibility estimation.

    Args:
        duration (int): The duration in seconds to compute the consumption.
                        Must be between 60 and 600 seconds (inclusive).

    Returns:
        JSONResponse: The result of the publish operation, typically indicating
                      the success or failure of sending the RPC payload.
    """
    # Request flexibility
    # Build the message
    rpc_payload: Dict[str, Any] = {
        "method": "dlc_estimate_flexibility",
        "params": {"duration": duration},
    }

    # Build topic including the prefix
    from grid_services_api.app import labels_channels

    topic = labels_channels["grid_functions_prefix"] + rpc_payload["method"]

    return await publish(rpc_payload, topic)
