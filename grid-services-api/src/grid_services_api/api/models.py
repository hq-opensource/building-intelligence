"""
This module defines the Pydantic models used across the Grid Services API.

It includes data models for various API functionalities such as:
- Direct Control: `SetpointRequest`, `PowerLimit`
- Tariffs: `FlatTariffParameters`, `TouTariffParameters`, `ShiftConsumptionParameters`
- Paid Control: `DynamicInterval`
- MPC (Model Predictive Control): `MpcParameters`

These models ensure data validation and clear structure for API requests and responses.
"""

from datetime import datetime, timedelta
from typing import Dict

from pydantic import BaseModel, Field, ValidationInfo, field_validator


###########################################
####### Direct Control ####################
###########################################


class SetpointRequest(BaseModel):
    """
    Represents a request to set a specific setpoint for a device.

    This model defines the parameters required to send a direct control command
    to a device, including the target device type, the desired setpoint value,
    and the duration for which the setpoint should be applied.
    """

    device: str = Field("space_heating", description="The device to set the setpoint for.")
    setpoint: int = Field(20, description="The desired setpoint for the device.")
    duration: int = Field(5, description="The duration in minutes for which the setpoint is applied.")

    @field_validator("device")
    @classmethod
    def validate_device(cls, device: str) -> str:
        """
        Validates that the specified device type is among the allowed devices.

        Args:
            device (str): The device type to validate.

        Returns:
            str: The validated device type.

        Raises:
            ValueError: If the device type is not in the list of allowed devices.
        """
        allowed_devices = [
            "space_heating",
            "electric_storage",
            "on_off_ev_charger",
            "electric_vehicle_v1g",
            "electric_vehicle_v2g",
            "water_heater",
        ]
        if device not in allowed_devices:
            raise ValueError(f"Invalid device '{device}'. Must be one of {allowed_devices}.")
        return device

    @field_validator("setpoint")
    @classmethod
    def validate_setpoint(cls, value: int, info: ValidationInfo) -> int:
        """
        Performs additional validation on the setpoint based on the device type.

        This validator ensures that the setpoint value falls within the acceptable
        range for the specified device.

        Args:
            value (int): The setpoint value to validate.
            info (ValidationInfo): Pydantic's validation information, used to access
                                   other fields like 'device'.

        Returns:
            int: The validated setpoint value.

        Raises:
            ValueError: If the setpoint value is outside the allowed range for the device.
        """
        device_type = info.data.get("device")

        if device_type == "space_heating" and not (10 <= value <= 30):
            raise ValueError("Setpoint for space_heating must be between 10 and 30 degrees.")
        if device_type == "electric_storage" and not (-100 <= value <= 100):
            raise ValueError("Setpoint for electric_storage must be between 0 and 100 percent.")
        if device_type == "on_off_ev_charger" and not (0 <= value <= 1):
            raise ValueError("Setpoint for ON-OFF EV charger must be either 0 or 1.")
        if device_type == "electric_vehicle_v1g" and not (-100 <= value <= 100):
            raise ValueError("Setpoint for charge of V1G must be between 0 and 100 percent.")
        if device_type == "electric_vehicle_v2g" and not (-100 <= value <= 100):
            raise ValueError("Setpoint for charge of V2G must be between 0 and 100 percent.")
        if device_type == "water_heater" and not (30 <= value <= 70):
            raise ValueError("Setpoint for water heater must be between 30 and 70 degrees.")

        return value

    @field_validator("duration")
    @classmethod
    def validate_duration(cls, value: int) -> int:
        """
        Validates that the duration is an integer between 5 and 240 minutes.

        Args:
            value (int): The duration value to validate.

        Returns:
            int: The validated duration value.

        Raises:
            ValueError: If the duration is not within the specified range.
        """
        if not (5 <= value <= 240):
            raise ValueError("Duration must be between 5 and 240 minutes.")
        return value


class PowerLimit(BaseModel):
    """
    Represents a power limit to be applied to a building or system.

    This model defines a single field for the power limit value, which is
    subject to validation to ensure it falls within an acceptable range.
    """

    limit: float = Field(description="The power limit for each building.")

    @field_validator("limit")
    @classmethod
    def validate_limit(cls, value: float) -> float:
        """
        Validates that the power limit is a float greater than 0 and less than or equal to 30 kW.

        Args:
            value (float): The power limit value to validate.

        Returns:
            float: The validated power limit value.

        Raises:
            ValueError: If the power limit is not within the specified range.
        """
        if not (0 < value <= 30):
            raise ValueError("The power limit must be greater than 0 and lower than 30 kW.")
        return value


###########################################
############## Tafiffs ####################
###########################################


class FlatTariffParameters(BaseModel):
    """
    Represents parameters for a flat tariff scheme.

    This model is used to define a constant energy price (`flat_price`)
    and the `date` for which this tariff applies. It includes validators
    to ensure the price is non-negative and the date is in the future.
    """

    flat_price: float = Field(0.08, description="The price.")
    date: datetime = Field(
        datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).astimezone() + timedelta(days=1),
        description="The date of the flat tarrif.",
    )

    @field_validator("flat_price")
    @classmethod
    def validate_flatprice(cls, value: float) -> float:
        """
        Validates that the flat price is non-negative.

        Args:
            value (float): The flat price value to validate.

        Returns:
            float: The validated flat price value.

        Raises:
            ValueError: If the price is negative.
        """
        if value < 0:
            raise ValueError("Price must be greater or equal than 0.")
        return value

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: datetime) -> datetime:
        """
        Validates that the specified date is in the future.

        Args:
            value (datetime): The date to validate.

        Returns:
            datetime: The validated date.

        Raises:
            ValueError: If the date is not in the future.
        """
        if value <= datetime.now().replace(second=0, microsecond=0).astimezone():
            raise ValueError("Date must be in the future.")

        return value


class TouTariffParameters(BaseModel):
    """
    Represents parameters for a Time-of-Use (ToU) tariff scheme.

    This model defines the date for the tariff, the start and stop times
    for the on-peak period, and the corresponding off-peak and on-peak prices.
    """

    _tomorrow = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).astimezone() + timedelta(days=1)

    date: datetime = Field(
        _tomorrow,
        description="The date of the tarrif.",
    )
    start_peak: datetime = Field(
        _tomorrow + timedelta(hours=16),
        description="The date of the start of the peak.",
    )
    stop_peak: datetime = Field(
        _tomorrow + timedelta(hours=21),
        description="The date of the end of the peak.",
    )
    off_peak_value: float = Field(0.05, description="The off peak price.")
    on_peak_value: float = Field(0.25, description="The peak price.")


class ShiftConsumptionParameters(BaseModel):
    """
    Represents parameters for a consumption shifting tariff scheme.

    This model defines a flat price, multipliers for price reduction and
    increase, and the start/stop dates for periods of price increase and reduction.
    It is used to incentivize or disincentivize consumption during specific times.
    """

    _tomorrow = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).astimezone() + timedelta(days=1)
    date: datetime = Field(
        _tomorrow,
        description="The date of the tarrif.",
    )
    flat_price: float = Field(0.08, description="The flat price.")
    reduction_multiplier: float = Field(0.5, description="The price reduction multiplier.")
    increase_multiplier: float = Field(2, description="The price increase multiplier.")
    start_increase: datetime = Field(
        _tomorrow + timedelta(hours=10),
        description="The start date of the increase.",
    )
    stop_increase: datetime = Field(
        _tomorrow + timedelta(hours=15),
        description="The end date of the increase.",
    )
    start_reduction: datetime = Field(
        _tomorrow + timedelta(hours=16),
        description="The start date of the reduction.",
    )
    stop_reduction: datetime = Field(
        _tomorrow + timedelta(hours=21),
        description="The start date of the reduction.",
    )


###########################################
######### Paid Control ####################
###########################################


class DynamicInterval(BaseModel):
    """
    Represents parameters for dynamic interval control, typically for device setpoints.

    This model defines the target device, the desired setpoint value, and the
    duration for which the setpoint should be applied. It includes validators
    to ensure that duration and setpoint are integers.
    """

    device: str = Field("space_heating", description="The device to set the setpoint for.")
    setpoint: int = Field(20, ge=0, le=30, description="The desired setpoint for the device.")
    duration: int = Field(5, ge=0, le=100, description="The duration in minutes for which the setpoint is applied.")

    @field_validator("duration", mode="before")
    @classmethod
    def duration_must_be_integer(cls, v: int) -> int:
        """
        Validates that the duration value is an integer.

        Args:
            v (int): The duration value to validate.

        Returns:
            int: The validated duration value.

        Raises:
            ValueError: If the duration is not an integer.
        """
        if not isinstance(v, int):
            raise ValueError("Duration must be an integer.")
        return v

    @field_validator("setpoint", mode="before")
    @classmethod
    def setpoint_must_be_integer(cls, v: int) -> int:
        """
        Validates that the setpoint value is an integer.

        Args:
            v (int): The setpoint value to validate.

        Returns:
            int: The validated setpoint value.

        Raises:
            ValueError: If the setpoint is not an integer.
        """
        if not isinstance(v, int):
            raise ValueError("Setpoint must be an integer.")
        return v


###########################################
######### MPC #############################
###########################################


def _price_example() -> Dict[datetime, float]:
    """
    Generates an example price profile for MPC optimization.

    This function creates a dictionary of datetime objects mapped to dummy
    price values, simulating a time-based price structure. The prices
    are generated for a 2-hour horizon with 10-minute intervals, starting
    from the next 10-minute mark.

    Returns:
        Dict[datetime, float]: A dictionary where keys are timestamps and
                               values are corresponding price examples.
    """
    now = datetime.now().replace(second=0, microsecond=0).astimezone()
    minutes_to_add = 10 - now.minute % 10
    start_optimization = now + timedelta(minutes=minutes_to_add)

    interval = 10  # in minutes

    # Generate timestamps
    timestamps = [start_optimization + timedelta(minutes=i) for i in range(0, 120 + 1, interval)]

    # Example: Generate dummy values
    price_profile = {ts: 0.07 if ts.minute < 40 else 0.15 for ts in timestamps}

    return price_profile


def _power_limit_example() -> Dict[datetime, float]:
    """
    Generates an example power limit profile for MPC optimization.

    This function creates a dictionary of datetime objects mapped to dummy
    power limit values, simulating a time-based power limit structure.
    The limits are generated for a 2-hour horizon with 10-minute intervals,
    starting from the next 10-minute mark.

    Returns:
        Dict[datetime, float]: A dictionary where keys are timestamps and
                               values are corresponding power limit examples.
    """
    now = datetime.now().replace(second=0, microsecond=0).astimezone()
    minutes_to_add = 10 - now.minute % 10
    start_optimization = now + timedelta(minutes=minutes_to_add)

    interval = 10  # in minutes

    # Generate timestamps
    timestamps = [start_optimization + timedelta(minutes=i) for i in range(0, 120 + 1, interval)]

    # Example: Generate dummy values
    power_limit = {ts: 7.0 if ts.minute < 40 else 15.0 for ts in timestamps}

    return power_limit


def _start_example() -> datetime:
    """
    Generates an example start datetime for MPC optimization.

    The start time is calculated to be the next 10-minute mark from the current time.

    Returns:
        datetime: The calculated start datetime.
    """
    now = datetime.now().replace(second=0, microsecond=0).astimezone()
    minutes_to_add = 10 - now.minute % 10
    start_optimization = now + timedelta(minutes=minutes_to_add)

    return start_optimization


def _stop_example() -> datetime:
    """
    Generates an example stop datetime for MPC optimization.

    The stop time is calculated to be 2 hours after the `_start_example` time.

    Returns:
        datetime: The calculated stop datetime.
    """
    now = datetime.now().replace(second=0, microsecond=0).astimezone()
    minutes_to_add = 10 - now.minute % 10
    start_optimization = now + timedelta(minutes=minutes_to_add)

    stop_optimization = start_optimization + timedelta(hours=2)

    return stop_optimization


class MpcParameters(BaseModel):
    """
    Represents the parameters for Model Predictive Control (MPC) optimization.

    This model defines various settings for the MPC, including flags to enable
    different device types (space heating, electric storage, electric vehicle,
    water heater), price and power limit profiles over time, the optimization
    interval, and the start and stop dates for the MPC run.
    """

    space_heating: bool = Field(True, description="Flag to enable in the MPC devices of type space heating.")
    electric_storage: bool = Field(True, description="Flag to enable in the MPC devices of type electric storage.")
    electric_vehicle: bool = Field(True, description="Flag to enable in the MPC devices of type electric vehicle.")
    water_heater: bool = Field(True, description="Flag to enable in the MPC devices of type water heater.")
    prices: Dict[datetime, float] = Field(_price_example(), description="The prices for the MPC.")
    power_limit: Dict[datetime, float] = Field(_power_limit_example(), description="The power limit for the MPC.")
    interval: int = Field(10, ge=0, le=100, description="The interval in minutes.")
    start: datetime = Field(
        _start_example(),
        description="The start date of the MPC.",
    )
    stop: datetime = Field(
        _stop_example(),
        description="The stop date of the MPC.",
    )

    # TODO add validators
