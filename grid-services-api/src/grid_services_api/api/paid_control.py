from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from common.util.logging import LoggingUtil
from grid_services_api.api.models import DynamicInterval, SetpointRequest
from grid_services_api.api.publisher import publish


logger = LoggingUtil.get_logger(__name__)
logger.info("The Paid Control API is starting at %s:", str(datetime.now().astimezone()))

# Create the API
PaidControlAPI = APIRouter()

# Define the FastAPI default values
# _setpoint_request_default_value = Body(..., description="Device, setpoint and duration of the request.")


@PaidControlAPI.post(
    "/paidcontrolrequest",
    tags=["Paid Control"],
)
async def send_paid_setpoint_message(dynamic_interval: DynamicInterval) -> JSONResponse:
    """Sends a request for a paid setpoint to all subscribed users."""
    logger.info(
        "Sending paid request to set a setpoint of %s for %s minutes:",
        dynamic_interval.setpoint,
        dynamic_interval.duration,
    )

    rpc_payload: Dict[str, Any] = {
        "method": "paid_setpoint_control",
        "params": {"setpoint": dynamic_interval.setpoint, "duration": dynamic_interval.duration},
    }

    # Build topic including the prefix
    from grid_services_api.app import labels_channels

    topic = labels_channels["grid_functions_prefix"] + rpc_payload["method"]

    return await publish(rpc_payload, topic)


# Define the API to send the dynamic setpoint
@PaidControlAPI.post(
    "/request_paid_device_control",
    tags=["Paid Control"],
)
async def request_paid_device_control(
    setpoint_request: SetpointRequest,
) -> JSONResponse:
    logger.info(
        "Sending setpoint of %s for device %s with a duration of %s minutes:",
        setpoint_request.setpoint,
        setpoint_request.device,
        setpoint_request.duration,
    )

    rpc_payload: Dict[str, Any] = {
        "method": "paid_setpoint_control",
        "params": {
            "device": setpoint_request.device,
            "setpoint": setpoint_request.setpoint,
            "duration": setpoint_request.duration,
        },
    }

    # Build topic including the prefix
    from grid_services_api.app import labels_channels

    topic = labels_channels["grid_functions_prefix"] + rpc_payload["method"]

    return await publish(rpc_payload, topic)
