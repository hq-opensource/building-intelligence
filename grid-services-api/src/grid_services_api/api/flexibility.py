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
    """Requests the flexibility from all subscribed users."""
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
