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
