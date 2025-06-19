"""
Schedule Models Module

This module contains the model classes used for scheduling operations
in the building intelligence system. It defines the core structures
for representing and manipulating time-based events.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from enum import StrEnum
from typing import Any, Dict, Generic, List, Optional, TypeVar


# Format used for serializing/deserializing time in schedules
SCHEDULE_DEFAULT_TIME_FORMAT = "%H:%M"
SCHEDULE_DEFAULT_DATE_FORMAT = "%Y-%m-%d"

# Type variables for generic typing
D = TypeVar("D")  # Data type for schedule events
E = TypeVar("E")  # Type for event objects


class Weekday(StrEnum):
    """
    Enum representing days of the week.

    Used for defining which days a weekly schedule applies to.
    The string values match standard abbreviations for days.
    """

    SUNDAY = "SUNDAY"
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"


class ScheduleError(Exception):
    """
    Base exception class for schedule-related errors.

    All schedule-specific exceptions should inherit from this class
    to allow for specific error handling of scheduling issues.
    """

    def __init__(self, message: str):
        """
        Initialize with custom error message.

        Args:
            message: Description of the scheduling error
        """
        self.message = message
        super().__init__(self.message)


class InvalidScheduleError(ScheduleError):
    """
    Exception raised when a schedule definition is invalid.

    This error occurs when schedule data is malformed or contains
    logical errors that prevent proper scheduling (like end before start).
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize with error message and optional details.

        Args:
            message: Description of the validation failure
            details: Additional structured information about the error
        """
        self.details = details or {}
        super().__init__(message)


@dataclass
class ScheduleEvent(Generic[D]):
    """
    Represents a single scheduled event with start and end times.

    This class defines one-time events with specific start and end
    timestamps, along with associated data and priority information.

    Type Parameters:
        D: Data type associated with the schedule event

    Attributes:
        id: Unique identifier for the event
        priority: Numeric priority (higher value = higher priority)
        data: Generic data payload associated with the event
        start: Start time of the event
        end: End time of the event
        duration: Time duration of the event (calculated)
    """

    id: str
    priority: int
    data: D
    start: datetime
    end: Optional[datetime] = None
    duration: Optional[int] = None

    def generate_name(self) -> str:
        """
        Generates a descriptive name for the event.

        Used for debugging and when no explicit ID is provided.

        Returns:
            A formatted string describing the event's time span
        """

        end_date_str = self.end.strftime(SCHEDULE_DEFAULT_DATE_FORMAT) if self.end else "None"
        return f"{self.id}-{self.start.strftime(SCHEDULE_DEFAULT_DATE_FORMAT)}-{end_date_str}"

    def __post_init__(self) -> None:
        """
        Validates and calculates derived properties after initialization.

        Performs several operations:
        - Validates time sequence (start before end)
        - Calculates duration
        - Generates ID if not provided
        - Normalizes time precision

        Raises:
            InvalidScheduleError: If end time is before or equal to start time
        """

        # Generate ID if not specified
        if self.id is None or not self.id.strip():
            self.id = self.generate_name()

        # Time precision handling
        self.start = self.start.replace(microsecond=0)
        if self.end:
            self.end = self.end.replace(microsecond=0)

        # Duration and end time logic
        if self.end is None and self.duration is not None:
            self.end = self.start + timedelta(minutes=self.duration)
        elif self.end is not None and self.duration is not None:
            raise ValueError("Cannot specify both 'end' and 'duration'")

        # Additional validations
        if self.priority < 0:
            raise ValueError("Priority must be non-negative")

        if self.end and self.end <= self.start:
            raise ValueError("End time must be after start time")


@dataclass
class WeeklyScheduleEvent(Generic[D]):
    """
    Represents a recurring weekly schedule entry.

    This class defines events that repeat on specific days of the week at a fixed time,
    commonly used for regular schedules like thermostat programming or similar patterns.

    Type Parameters:
        D: Data type associated with the schedule entry (e.g., float for temperature)

    Attributes:
        id (str): Unique identifier for the schedule entry
        time (time): Time of day when the schedule activates (HH:MM)
        data (D): Generic data payload associated with the schedule
        days (List[Weekday]): List of weekdays when this schedule applies
    """

    id: str
    time: time
    data: D
    days: List[Weekday] = field(default_factory=list)

    def generate_name(self) -> str:
        """
        Generates a descriptive name for the schedule entry.

        Used for debugging and when no explicit ID is provided.

        Returns:
            str: A formatted string describing the days this schedule applies to
        """
        days_str = "-".join(self.days) if self.days else "No Days"
        return f"WeeklyScheduleEvent-[{days_str}]}}"

    def __post_init__(self) -> None:
        """
        Validates and normalizes schedule properties after initialization.

        Performs several operations:
        - Normalizes time precision
        - Converts day strings to Weekday enum values
        - Generates ID if not provided
        """
        self.time = time(self.time.hour, self.time.minute)
        self.days = [Weekday(day) if isinstance(day, str) else day for day in self.days]
        if self.id is None:
            self.id = self.generate_name()

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the schedule entry to a dictionary format.

        Useful for serialization, storage, and API responses.

        Returns:
            Dict[str, Any]: Dictionary representation of the schedule entry
        """
        return {
            "id": self.id,
            "time": self.time.strftime(SCHEDULE_DEFAULT_TIME_FORMAT),
            "data": self.data,
            "days": [day.value for day in self.days],
        }


@dataclass
class Schedule(Generic[E]):
    """
    Container for a collection of scheduled events.

    Represents a complete schedule with multiple events, providing
    organization and metadata for a set of related schedule entries.

    Type Parameters:
        E: Event type contained in this schedule

    Attributes:
        id: Unique identifier for the schedule
        name: Human-readable name for the schedule
        description: Detailed description of the schedule's purpose
        events: List of schedule events
    """

    id: str
    name: str
    description: str
    events: List[E] = field(default_factory=list)


@dataclass
class ScheduleEventData(Generic[D]):
    """
    Data container for schedule event information.

    This class is used to transfer schedule event data between
    components, particularly for direct control scenarios where
    event data might come from different sources.

    Type Parameters:
        D: Data type associated with the event

    Attributes:
        event_id: ID of the associated schedule event
        data: Generic data payload
        from_direct_control: Flag indicating if this data comes from direct control
    """

    event_id: str
    data: D
    from_direct_control: bool = False


@dataclass
class AbstractScheduler(ABC, Generic[D]):
    """
    Abstract base class defining the interface for all scheduler implementations.

    Schedulers are responsible for managing collections of schedule events
    and retrieving the appropriate event data for any given point in time.

    Type Parameters:
        D: Data type handled by this scheduler
    """

    @abstractmethod
    def get_event_data(self, timestamp: datetime) -> Optional[ScheduleEventData[D]]:
        """
        Retrieves the active schedule data for a specific point in time.

        This method must be implemented by all concrete scheduler classes.

        Args:
            timestamp (datetime): The point in time to get schedule data for

        Returns:
            Optional[ScheduleEventData[D]]: The active schedule data if available,
                                           None if no schedule is active
        """
        pass


class PreferenceType(StrEnum):
    """
    Enumeration of preference types supported by the system.
    These types represent different categories of user preferences
    that can be scheduled in the building management system.
    """

    PREFERENCES_SETPOINT = "preferences_setpoint"
    PREFERENCES_OCCUPANCY = "preferences_occupancy"
    PREFERENCES_BRANCHED = "preferences_branched"
    PREFERENCES_SOC = "preferences_soc"
    PREFERENCES_WATER_HEATER_CONSUMPTION = "preferences_water_heater_consumption"


class ControlType(StrEnum):
    """
    Enumeration of control types supported by the system.
    These types represent different categories of controls
    that can be applied to building devices and systems.
    """

    CONTROL_SETPOINT = "setpoint"
    CONTROL_POWER = "power"
    CONTROL_BATTERY_POWER = "battery_power"
    CONTROL_OCCUPATION = "occupation"
    CONTROL_SOC = "state_of_charge"
    CONTROL_SOLAR_POWER = "sp_power"


# Mapping between control types and their corresponding preference types
CONTROL_TO_PREFERENCE_TYPE_MAPPING = {
    ControlType.CONTROL_SETPOINT: PreferenceType.PREFERENCES_SETPOINT,
    ControlType.CONTROL_OCCUPATION: PreferenceType.PREFERENCES_OCCUPANCY,
    ControlType.CONTROL_SOC: PreferenceType.PREFERENCES_SOC,
    ControlType.CONTROL_POWER: None,
    ControlType.CONTROL_BATTERY_POWER: None,
    ControlType.CONTROL_SOLAR_POWER: None,
}
