from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from common.util.logging import LoggingUtil
from grid_services_api.api.models import PowerLimit, SetpointRequest
from grid_services_api.api.publisher import publish


logger = LoggingUtil.get_logger(__name__)
logger.info("The Direct Control API is starting at %s:", str(datetime.now().astimezone()))

DirectControlAPI = APIRouter()


@DirectControlAPI.post(
    "/write_device_type_setpoint",
    tags=["Direct Load Control"],
)
async def set_device_setpoint(
    setpoint_request: SetpointRequest,
) -> JSONResponse:
    """Sends a fix setpoint to all subscribed users."""
    logger.info(
        "Sending %s setpoint for %s minutes to the device(s) of type %s.",
        setpoint_request.setpoint,
        setpoint_request.duration,
        setpoint_request.device,
    )

    from grid_services_api.app import labels_channels

    method = labels_channels["grid_functions"]["dlc_dynamic_writer"]

    # Build the message
    rpc_payload: Dict[str, Any] = {
        "method": method,
        "params": {
            "device": setpoint_request.device,
            "setpoint": setpoint_request.setpoint,
            "duration": setpoint_request.duration,
        },
    }

    topic = labels_channels["grid_functions_prefix"] + method

    return await publish(rpc_payload, topic)


@DirectControlAPI.post(
    "/power_limit",
    tags=["Direct Load Control"],
)
async def power_limit(
    power_limit: PowerLimit | None = None,
) -> JSONResponse:
    """Sends power limits to the users."""

    from grid_services_api.app import labels_channels

    method = labels_channels["grid_functions"]["power_limit_control"]

    # Build the message
    rpc_payload: Dict[str, Any] = {
        "method": method,
        "params": {},
    }

    if power_limit is not None:
        rpc_payload["params"]["limit"] = power_limit.limit

    topic = labels_channels["grid_functions_prefix"] + method

    logger.info(f"Sending power limit with the following parameters: {rpc_payload['params']}.")

    return await publish(rpc_payload, topic)
