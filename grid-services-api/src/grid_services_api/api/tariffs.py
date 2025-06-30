"""
This module defines the API endpoints for Dynamic Tariffs Optimization within the Grid Services API.

It provides functionalities to send various tariff types (flat, Time-of-Use,
and consumption shifting) to the Model Predictive Control (MPC) system for
optimizing grid services based on pricing signals.
"""

from datetime import datetime
from typing import Any, Dict

import numpy as np

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from common.util.logging import LoggingUtil
from grid_services_api.api.models import FlatTariffParameters, ShiftConsumptionParameters, TouTariffParameters
from grid_services_api.api.publisher import publish


logger = LoggingUtil.get_logger(__name__)
logger.info("The Tariffs API is starting at %s:", str(datetime.now().astimezone()))

# Create the API
TariffsAPI = APIRouter()


HORIZON = 144


@TariffsAPI.post(
    "/flattariff",
    tags=["Dynamic Tariffs Optimization"],
)
async def send_flat_tariff(flat_params: FlatTariffParameters) -> JSONResponse:
    """
    Sends a flat tariff to initiate dynamic tariffs optimization.

    This endpoint takes `FlatTariffParameters` which include a `flat_price`.
    It constructs a price list for the defined `HORIZON` based on this flat price.
    An RPC payload is then created with the method `mpc_dynamic_tariff_optimizer`
    and the generated price list, along with the current date. This payload is
    published to a topic for grid functions.

    Args:
        flat_params (FlatTariffParameters): An object containing the flat price
                                            and the date for which the tariff applies.

    Returns:
        JSONResponse: The result of the publish operation, typically indicating
                      the success or failure of sending the RPC payload.
    """

    # Create a log
    logger.info("Executing flat tariff optimization.")

    constant_price = np.ones(HORIZON) * flat_params.flat_price

    price_list = constant_price.tolist()
    # Build the message
    now = datetime.now().astimezone()
    rpc_payload: Dict[str, Any] = {
        "method": "mpc_dynamic_tariff_optimizer",
        "params": {"prices": price_list, "date": now.isoformat()},
    }

    # Build topic including the prefix
    from grid_services_api.app import labels_channels

    topic = labels_channels["grid_functions_prefix"] + rpc_payload["method"]

    return await publish(rpc_payload, topic)


# Define the API to send broadcast a tou tariff
@TariffsAPI.post(
    "/toutariff",
    tags=["Dynamic Tariffs Optimization"],
)
async def send_tou_tariff(tou_params: TouTariffParameters) -> JSONResponse:
    """
    Sends a Time-of-Use (ToU) tariff to initiate dynamic tariffs optimization.

    This endpoint takes `TouTariffParameters` which define the on-peak and
    off-peak prices and their respective time windows. It constructs a price
    list for the defined `HORIZON` based on these parameters. An RPC payload
    is then created with the method `mpc_dynamic_tariff_optimizer` and the
    generated price list, along with the current date. This payload is
    published to a topic for grid functions.

    Args:
        tou_params (TouTariffParameters): An object containing the ToU tariff
                                          parameters, including peak and off-peak
                                          times and values.

    Returns:
        JSONResponse: The result of the publish operation, typically indicating
                      the success or failure of sending the RPC payload.
    """

    # Create a log
    logger.info("Executing Time of Use tariff optimization.")

    # Extract the values
    start_peak = tou_params.start_peak
    stop_peak = tou_params.stop_peak
    on_peak_value = tou_params.on_peak_value
    off_peak_value = tou_params.off_peak_value

    # Convert start and stop datetimes to integer values for indexing
    start_int = _convert_datetime_to_int(start_peak)
    stop_int = _convert_datetime_to_int(stop_peak)

    # Create arrays for off-peak and on-peak prices
    tou_tariff = np.ones(HORIZON) * off_peak_value

    # Calculate total tariff
    tou_tariff[start_int:stop_int] = on_peak_value

    price_list = tou_tariff.tolist()

    now = datetime.now().astimezone()
    rpc_payload: Dict[str, Any] = {
        "method": "mpc_dynamic_tariff_optimizer",
        "params": {"prices": price_list, "date": now.isoformat()},
    }

    # Build topic including the prefix
    from grid_services_api.app import labels_channels

    topic = labels_channels["grid_functions_prefix"] + rpc_payload["method"]

    return await publish(rpc_payload, topic)


# Define the API to send broadcast a shift_consumption tariff
@TariffsAPI.post(
    "/shift-consumption-tariff",
    tags=["Dynamic Tariffs Optimization"],
)
async def send_shift_consumption_tariff(
    shift_consumption_params: ShiftConsumptionParameters,
) -> JSONResponse:
    """
    Sends a consumption shifting tariff to initiate dynamic tariffs optimization.

    This endpoint takes `ShiftConsumptionParameters` which define a flat price,
    and multipliers for price increase and reduction during specified time windows.
    It constructs a price profile for the defined `HORIZON` based on these parameters.
    An RPC payload is then created with the method `mpc_dynamic_tariff_optimizer`
    and the generated price list, along with the current date. This payload is
    published to a topic for grid functions.

    Args:
        shift_consumption_params (ShiftConsumptionParameters): An object containing
                                                               the parameters for
                                                               the consumption shifting tariff.

    Returns:
        JSONResponse: The result of the publish operation, typically indicating
                      the success or failure of sending the RPC payload.
    """

    # Create a log
    logger.info("Executing shift consumption optimization.")

    # Convert start and stop datetimes to integer values for indexing
    start_increase_int = _convert_datetime_to_int(shift_consumption_params.start_increase)
    stop_increase_int = _convert_datetime_to_int(shift_consumption_params.stop_increase)
    start_reduction_int = _convert_datetime_to_int(shift_consumption_params.start_reduction)
    stop_reduction_int = _convert_datetime_to_int(shift_consumption_params.stop_reduction)

    # Create the tariff profile for shifting consumption
    shift_price_profile = np.ones(HORIZON) * shift_consumption_params.flat_price
    shift_price_profile[start_increase_int:stop_increase_int] = (
        shift_consumption_params.flat_price * shift_consumption_params.increase_multiplier
    )
    shift_price_profile[start_reduction_int:stop_reduction_int] = (
        shift_consumption_params.flat_price * shift_consumption_params.reduction_multiplier
    )

    price_list = shift_price_profile.tolist()

    now = datetime.now().astimezone()
    rpc_payload: Dict[str, Any] = {
        "method": "mpc_dynamic_tariff_optimizer",
        "params": {"prices": price_list, "date": now.isoformat()},
    }

    # Build topic including the prefix
    from grid_services_api.app import labels_channels

    topic = labels_channels["grid_functions_prefix"] + rpc_payload["method"]

    return await publish(rpc_payload, topic)


def _convert_datetime_to_int(date: datetime) -> int:
    """
    Converts a datetime object to an integer representation based on 10-minute intervals.

    This helper function calculates the total number of 10-minute steps from
    the beginning of the day up to the given datetime. This is used for
    indexing time-series data within a fixed horizon.

    Args:
        date (datetime): The datetime object to convert.

    Returns:
        int: The total number of 10-minute steps from the start of the day.
    """
    dac_timestemp = 10

    # Convert hours to steps
    steps_per_hour = np.floor(date.hour * 60 / dac_timestemp)

    # Convert minutes to steps
    steps_per_minute = np.floor(date.minute / dac_timestemp)

    # Compute total steps
    total_steps = int(steps_per_hour + steps_per_minute)

    return total_steps
