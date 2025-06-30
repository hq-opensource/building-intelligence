"""
This module defines the API endpoints for Direct Load Control within the Grid Services API.

It provides functionalities to directly control devices by sending setpoints
and power limits to subscribed users or devices.
"""

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
    """
    Sends a fixed setpoint to all subscribed devices of a specific type.

    This endpoint allows for direct load control by sending a setpoint
    (e.g., a temperature, power level) and a duration to devices.
    The request is encapsulated in an RPC payload and published to a topic
    that targets the dynamic writer for direct load control.

    Args:
        setpoint_request (SetpointRequest): An object containing the device type,
                                            the setpoint value, and the duration
                                            for which the setpoint should be applied.

    Returns:
        JSONResponse: The result of the publish operation, typically indicating
                      the success or failure of sending the RPC payload.
    """
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
    """
    Sends power limits to subscribed users or devices.

    This endpoint allows for setting a power limit. If a `power_limit` object
    is provided, its `limit` attribute is included in the RPC payload.
    The request is then published to a topic for power limit control.

    Args:
        power_limit (PowerLimit | None): An optional object containing the
                                         power limit value. If None, no specific
                                         limit is sent, but the control method
                                         is still invoked.

    Returns:
        JSONResponse: The result of the publish operation, typically indicating
                      the success or failure of sending the RPC payload.
    """

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
