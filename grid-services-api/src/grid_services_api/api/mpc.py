"""
This module defines the API endpoints for Model Predictive Control (MPC) within the Grid Services API.

It provides functionalities to send MPC requests with various parameters
to optimize grid services.
"""

from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from common.util.logging import LoggingUtil
from grid_services_api.api.models import MpcParameters
from grid_services_api.api.publisher import publish


logger = LoggingUtil.get_logger(__name__)
logger.info("The MPC API is starting at %s:", str(datetime.now().astimezone()))

# Create the API
MpcAPI = APIRouter()


@MpcAPI.post(
    "/calculate_mpc",
    tags=["MPC"],
)
async def send_mpc_request(parameters: MpcParameters | None = None) -> JSONResponse:
    """
    Sends an MPC (Model Predictive Control) request with optional parameters.

    This endpoint constructs an RPC payload for the MPC system. If `parameters`
    are provided, they are included in the payload, enabling specific
    configurations for the MPC run, such as enabled device types, price and
    power limit profiles, and the optimization horizon. The request is then
    published to a predefined topic for MPC grid functions.

    Args:
        parameters (MpcParameters | None): An optional object containing the
                                           MPC configuration parameters. If None,
                                           default MPC behavior is assumed.

    Returns:
        JSONResponse: The result of the publish operation, typically indicating
                      the success or failure of sending the RPC payload.
    """
    logger.info("Sending an MPC request with parameters: %s", parameters)
    from grid_services_api.app import labels_channels

    rpc_payload: Dict[str, Any] = {
        "method": labels_channels["grid_functions"]["mpc"],
    }

    if parameters is not None:
        rpc_payload["params"] = {
            "space_heating": parameters.space_heating,
            "electric_storage": parameters.electric_storage,
            "electric_vehicle": parameters.electric_vehicle,
            "water_heater": parameters.water_heater,
            "start": parameters.start.isoformat(),
            "stop": parameters.stop.isoformat(),
            "interval": parameters.interval,
            "prices": {k.isoformat(): v for k, v in parameters.prices.items()},
            "power_limit": {k.isoformat(): v for k, v in parameters.power_limit.items()},
        }

    topic = labels_channels["grid_functions_prefix"] + rpc_payload["method"]

    return await publish(rpc_payload, topic)
