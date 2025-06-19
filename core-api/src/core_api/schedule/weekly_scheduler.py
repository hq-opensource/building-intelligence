"""
Weekly Scheduler Module

This module implements a scheduler for managing weekly recurring events with specific time slots.
It handles schedule creation, validation and retrieval of events based on configured time intervals.

The scheduler supports:
- Multiple schedules (e.g. weekday/weekend schedules)
- Multiple events per schedule with specific times and data
- Automatic timezone handling
- Conflict detection between events

Example schedule configuration:
    weekday:
      days: ["MONDAY"]
      events:
        - time: "06:00", data: 21.0
        - time: "22:00", data: 17.0
    weekend:
      days: ["SATURDAY", "SUNDAY"]
      events:
        - time: "07:00", data: 21.0
        - time: "23:00", data: 17.0
"""

from datetime import datetime
from itertools import chain
from typing import List, Optional

from core_api.schedule.models import (
    AbstractScheduler,
    Schedule,
    ScheduleEventData,
    Weekday,
    WeeklyScheduleEvent,
)


class WeeklyRecurringSchedulerError(Exception):
    """
    Custom exception class for weekly recurring scheduler errors.

    Used to indicate schedule-specific error conditions such as:
    - Invalid configuration format
    - Missing required schedule parameters
    - Schedule processing failures
    """

    pass


class WeeklyRecurringScheduler(AbstractScheduler):
    """
    Manages weekly recurring schedules and their events.

    This class handles:
    - Creation and validation of scheduled events
    - Retrieval of active events for any given timestamp
    - Detection of schedule changes within time intervals
    - Conflict prevention between overlapping events
    """

    # Dictionary key constants for schedule data structure
    DAYS_KEY = "days"
    EVENTS_KEY = "events"
    TIME_KEY = "time"
    DATA_KEY = "data"

    def __init__(self, schedule_data: dict, time_step_duration_in_seconds: int = 60) -> None:
        """
        Initialize the weekly recurring scheduler.

        Sets up the scheduler with initial configuration, time zone settings,
        and processes the provided schedules data.

        Args:
            schedule_data (dict): Initial schedule configuration containing schedules
                                with their days and events configuration
        """
        self._time_step_duration_in_seconds: int = time_step_duration_in_seconds
        local_now = datetime.now().astimezone()
        self._timezone = local_now.astimezone().tzinfo
        self._schedules: List[Schedule[WeeklyScheduleEvent]] = []
        self._add_schedules(schedule_data)

    def _add_schedules(self, schedule_dict: dict) -> None:
        """
        Create and add schedules from configuration dictionary.

        For each schedule in the configuration:
        1. Creates events with specified times and data
        2. Validates events for conflicts
        3. Creates a Schedule object with the events
        4. Adds the schedule to the scheduler

        Args:
            schedule_dict (dict): Dictionary containing schedule configurations with
                                days and events for each schedule
        """
        for schedule_name, schedule_data in schedule_dict.items():
            # Validate schedule configuration structure
            self._validate_schedule(schedule_name, schedule_data)

            events = []
            # Process each event in the schedule
            for event_data in schedule_data["events"]:
                event_time = datetime.strptime(event_data["time"], "%H:%M").time()
                event = WeeklyScheduleEvent(
                    id=f"{schedule_name}_{event_data['time']}",
                    time=event_time,
                    data=event_data["data"],
                    days=[Weekday(day) for day in schedule_data["days"]],
                )
                self._validate_event(event)
                events.append(event)

            schedule: Schedule = Schedule(
                id=schedule_name, name=schedule_name, description=f"Schedule for {schedule_name}", events=events
            )
            self._schedules.append(schedule)

    def _get_events_with_changes_in_interval(
        self, start_interval: datetime, end_interval: datetime
    ) -> List[WeeklyScheduleEvent]:
        """
        Retrieve events that have changes within the specified time interval.

        Identifies schedule events that would activate (trigger) within the given
        time window, based on their configured time of day.

        Args:
            start_interval (datetime): Start time of the interval to check
            end_interval (datetime): End time of the interval to check

        Returns:
            List[WeeklyScheduleEvent]: List of events that change within the interval
        """
        start_local = start_interval.astimezone(self._timezone)
        end_local = end_interval.astimezone(self._timezone)
        return [
            event
            for event in self.get_events()
            if start_local
            < datetime.combine(start_local.date(), event.time).replace(tzinfo=self._timezone)
            <= end_local
        ]

    def get_events(self) -> List[WeeklyScheduleEvent]:
        """
        Retrieve all events from all configured schedules.

        Flattens the nested structure of schedules and events into a single list
        for easier processing and iteration.

        Returns:
            List[WeeklyScheduleEvent]: Flattened list of all schedule events
        """
        return list(chain.from_iterable(schedule.events for schedule in self._schedules))

    def get_event(self, timestamp: datetime) -> Optional[WeeklyScheduleEvent]:
        """
        Get the active schedule event at the specified timestamp.

        The active event is determined by:
        1. Finding events scheduled for the current day of week
        2. Selecting the most recent event before the given time
        3. If no previous events, selecting the last event of the day

        Args:
            timestamp (datetime): Point in time to check for active events

        Returns:
            Optional[WeeklyScheduleEvent]: Active schedule event if found, None otherwise
        """
        local_time = timestamp.astimezone(self._timezone).replace(microsecond=0)
        current_day = Weekday(local_time.strftime("%A").upper())
        current_time = local_time.time()
        valid_events = [event for event in self.get_events() if (current_day in event.days)]

        if not valid_events:
            return None

        # Find the most recent event before current time
        active_event = None
        for event in reversed(valid_events):
            if event.time <= current_time:
                active_event = event
                break

        # If no previous event found, use the last event of the day
        if not active_event and valid_events:
            active_event = max(valid_events, key=lambda x: x.time)
        return active_event

    def get_event_data(self, timestamp: datetime) -> Optional[ScheduleEventData]:
        """
        Get complete event data for the specified timestamp.

        This includes:
        - The active event at the timestamp
        - The event's associated data
        - Whether the schedule changed in the last interval

        Implements the abstract method from AbstractScheduler interface.

        Args:
            timestamp (datetime): Point in time to get event data for

        Returns:
            Optional[ScheduleEventData]: Complete event data including
                                           change status, or None if no active event
        """
        active_event = self.get_event(timestamp)

        if active_event and active_event.data is not None:
            return ScheduleEventData(event_id=active_event.id, data=active_event.data)
        else:
            return None

    def _validate_event(self, event: WeeklyScheduleEvent) -> None:
        """
        Validates a new schedule event for conflicts with existing events.

        Checks for:
        - Time conflicts on the same days of week
        - Overlapping schedules

        This ensures that no two events can be scheduled at exactly the same time
        on the same day, preventing ambiguity in schedule application.

        Args:
            event (WeeklyScheduleEvent): Event to validate

        Raises:
            WeeklyRecurringSchedulerError: If a conflicting event exists at the same time
                                on any of the same days
        """
        for existing in self.get_events():
            # Check for time and day conflicts
            if set(existing.days) & set(event.days) and existing.time == event.time:
                raise WeeklyRecurringSchedulerError(
                    f"Schedule conflict: Entry already exists for {event.time} "
                    f"on days {set(existing.days) & set(event.days)}"
                )

    def _validate_schedule(self, schedule_name: str, schedule_data: dict) -> None:
        """
        Validates that a schedule configuration dictionary contains the required properties.

        Checks if the dictionary has 'events' and 'days' keys with appropriate types.

        Args:
            schedule_name (str): Name of the schedule being validated
            schedule_data (dict): Schedule configuration data to validate

        Raises:
            WeeklyRecurringSchedulerError: If the configuration is invalid or incomplete
        """
        if not isinstance(schedule_data, dict):
            raise WeeklyRecurringSchedulerError(
                f"Invalid configuration for schedule '{schedule_name}': must be a dictionary"
            )

        # Validate presence and type of 'events' key
        if self.EVENTS_KEY not in schedule_data:
            raise WeeklyRecurringSchedulerError(
                f"Invalid configuration for schedule '{schedule_name}': '{self.EVENTS_KEY}' key missing"
            )
        if not isinstance(schedule_data[self.EVENTS_KEY], list):
            raise WeeklyRecurringSchedulerError(
                f"Invalid configuration for schedule '{schedule_name}': '{self.EVENTS_KEY}' must be a list"
            )

        # Validate presence and type of 'days' key
        if self.DAYS_KEY not in schedule_data:
            raise WeeklyRecurringSchedulerError(
                f"Invalid configuration for schedule '{schedule_name}': '{self.DAYS_KEY}' key missing"
            )
        if not isinstance(schedule_data[self.DAYS_KEY], list):
            raise WeeklyRecurringSchedulerError(
                f"Invalid configuration for schedule '{schedule_name}': '{self.DAYS_KEY}' must be a list"
            )

        # Validate each event has required properties
        for i, event in enumerate(schedule_data[self.EVENTS_KEY]):
            if not isinstance(event, dict):
                raise WeeklyRecurringSchedulerError(
                    f"Invalid configuration for schedule '{schedule_name}': event {i} must be a dictionary"
                )

            # Check for presence of required keys
            if self.TIME_KEY not in event:
                raise WeeklyRecurringSchedulerError(
                    f"Invalid configuration for schedule '{schedule_name}': '{self.TIME_KEY}' key missing in event {i}"
                )
            if self.DATA_KEY not in event:
                raise WeeklyRecurringSchedulerError(
                    f"Invalid configuration for schedule '{schedule_name}': '{self.DATA_KEY}' key missing in event {i}"
                )
