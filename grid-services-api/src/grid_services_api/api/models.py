from datetime import datetime, timedelta
from typing import Dict

from pydantic import BaseModel, Field, ValidationInfo, field_validator


###########################################
####### Direct Control ####################
###########################################


class SetpointRequest(BaseModel):
    device: str = Field("space_heating", description="The device to set the setpoint for.")
    setpoint: int = Field(20, description="The desired setpoint for the device.")
    duration: int = Field(5, description="The duration in minutes for which the setpoint is applied.")

    @field_validator("device")
    @classmethod
    def validate_device(cls, device: str) -> str:
        """Validate that the device is one of the allowed devices."""
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
        """Perform additional validation on setpoint depending on the device."""
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
        """Validate that duration is an integer between 5 and 240 minutes."""
        if not (5 <= value <= 240):
            raise ValueError("Duration must be between 5 and 240 minutes.")
        return value


class PowerLimit(BaseModel):
    limit: float = Field(description="The power limit for each building.")

    @field_validator("limit")
    @classmethod
    def validate_limit(cls, value: float) -> float:
        """Validate that the power limit is an integer between 0 and 20 kW."""
        if not (0 < value <= 30):
            raise ValueError("The power limit must be greater than 0 and lower than 30 kW.")
        return value


###########################################
############## Tafiffs ####################
###########################################


class FlatTariffParameters(BaseModel):
    """Object to store the optimization parameters."""

    flat_price: float = Field(0.08, description="The price.")
    date: datetime = Field(
        datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).astimezone() + timedelta(days=1),
        description="The date of the flat tarrif.",
    )

    @field_validator("flat_price")
    @classmethod
    def validate_flatprice(cls, value: float) -> float:
        """Validate that price is postive."""
        if value < 0:
            raise ValueError("Price must be greater or equal than 0.")
        return value

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: datetime) -> datetime:
        """Validate that date is in the future"""
        if value <= datetime.now().replace(second=0, microsecond=0).astimezone():
            raise ValueError("Date must be in the future.")

        return value


class TouTariffParameters(BaseModel):
    """Object to store the optimization parameters."""

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
    """Object to store the optimization parameters."""

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
    """Parameters for the overwrite inputs."""

    device: str = Field("space_heating", description="The device to set the setpoint for.")
    setpoint: int = Field(20, ge=0, le=30, description="The desired setpoint for the device.")
    duration: int = Field(5, ge=0, le=100, description="The duration in minutes for which the setpoint is applied.")

    @field_validator("duration", mode="before")
    @classmethod
    def duration_must_be_integer(cls, v: int) -> int:
        """Validator for the duration value."""
        if not isinstance(v, int):
            raise ValueError("Duration must be an integer.")
        return v

    @field_validator("setpoint", mode="before")
    @classmethod
    def setpoint_must_be_integer(cls, v: int) -> int:
        """Validator for the setpoint value."""
        if not isinstance(v, int):
            raise ValueError("Setpoint must be an integer.")
        return v


###########################################
######### MPC #############################
###########################################


def _price_example() -> Dict[datetime, float]:
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
    now = datetime.now().replace(second=0, microsecond=0).astimezone()
    minutes_to_add = 10 - now.minute % 10
    start_optimization = now + timedelta(minutes=minutes_to_add)

    return start_optimization


def _stop_example() -> datetime:
    now = datetime.now().replace(second=0, microsecond=0).astimezone()
    minutes_to_add = 10 - now.minute % 10
    start_optimization = now + timedelta(minutes=minutes_to_add)

    stop_optimization = start_optimization + timedelta(hours=2)

    return stop_optimization


class MpcParameters(BaseModel):
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
