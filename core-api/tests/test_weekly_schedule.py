"""
Weekly Schedule Tests Module

This module contains unit tests for the WeeklyRecurringScheduler class.
It validates the scheduler's ability to:
- Parse and process schedule configurations from YAML
- Properly initialize schedule events and days
- Retrieve the correct schedule data for specific timestamps
- Handle time zone information correctly
- Validate and prevent conflicting events
- Properly format and sanitize event times

The tests ensure that schedules correctly handle weekday/weekend configurations
and maintain proper event data throughout the week.
"""

import unittest

from datetime import datetime, time
from typing import Any

import yaml

from core_api.schedule.models import Weekday, WeeklyScheduleEvent
from core_api.schedule.weekly_scheduler import WeeklyRecurringScheduler, WeeklyRecurringSchedulerError


class TestWeeklySchedule(unittest.TestCase):
    """
    Test suite for WeeklyRecurringScheduler functionality.

    Tests the scheduler's ability to handle different schedule configurations,
    time-based event retrieval, and validation of schedule integrity.
    """

    @classmethod
    def setUpClass(cls) -> None:
        """
        Initialize shared test resources before any tests run.

        Currently commented out but prepared for Redis mocking if needed.
        """
        pass

    def setUp(self) -> None:
        """
        Set up test fixtures before each test method.

        Creates a sample schedule configuration with:
        - Weekday schedule (Mon-Fri) with three time slots
        - Weekend schedule (Sat-Sun) with three time slots
        - Multiple devices assigned to each schedule

        Initializes a scheduler with this test data and captures timezone information.
        """
        self.test_yaml_data: str = """
            weekday_office:
                devices: ["device1", "device2", "device3"]
                days: ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]
                events:
                    - time: "07:00"
                      data: 19.5,
                    - time: "08:30"
                      data: 21.0
                    - time: "17:30"
                      data: 18.0
            weekend_office:
                devices: ["device1", "device2"]
                days: ["SATURDAY", "SUNDAY"]
                events:
                    - time: "00:00"
                      data: 17.0
                    - time: "10:00"
                      data: 19.0
                    - time: "18:00"
                      data: 17.0
                """
        self.test_data: dict[str, Any] = yaml.safe_load(self.test_yaml_data)
        self.scheduler = WeeklyRecurringScheduler(schedule_data=self.test_data)
        local_now = datetime.now()
        self.timezone = local_now.astimezone().tzinfo

    def test_init_scheduler(self) -> None:
        """
        Test that scheduler initializes correctly with proper event counts.

        Verifies:
        - All events are loaded from the configuration
        - Weekday schedule has the expected number of events
        - Weekday schedule has all 5 weekdays configured
        """
        expected_events = sum(len(schedule["events"]) for schedule in self.test_data.values())
        obtained_events = self.scheduler.get_events()

        self.assertEqual(len(obtained_events), expected_events)

        # Verify specific schedule details
        office_events = [event for event in obtained_events if event.id.startswith("weekday_office")]
        self.assertEqual(len(office_events), 3)

        self.assertEqual(len(office_events[0].days), 5)  # All week

    def test_get_data_multiple_devices(self) -> None:
        """
        Test retrieving data for specific dates across weekday and weekend schedules.

        Verifies that the scheduler returns the correct temperature setpoints for:
        - A Monday morning (weekday schedule)
        - A Saturday late morning (weekend schedule)
        """
        test_cases = [
            # (datetime, expected_setpoint)
            (datetime(2024, 1, 1, 9, 0), 21.0),  # Monday morning, weekday_office
            (datetime(2024, 1, 6, 11, 0), 19.0),  # Saturday, weekend_office
        ]

        for test_time, expected in test_cases:
            test_time = test_time.replace(tzinfo=self.timezone)
            data = self.scheduler.get_event(test_time)
            self.assertEqual(data.data, expected, f"Failed at {test_time}")

    def test_get_data(self) -> None:
        """
        Test retrieving data for specific timestamps throughout the day.

        Verifies the scheduler returns the correct temperature setpoints for:
        - Mid-morning on a Monday (active period)
        - Late night on a Monday (evening period)
        - Early morning on a Tuesday (carryover from previous day)

        Tests the scheduler's ability to find the most recent applicable event.
        """
        # Test during active period
        test_datetime = datetime(2024, 1, 1, 10, 0)  # Monday 10:00
        test_datetime = test_datetime.replace(tzinfo=self.timezone)
        data = self.scheduler.get_event(test_datetime)
        self.assertEqual(data.data, 21.0)

        # Test during night period
        test_datetime = datetime(2024, 1, 1, 23, 0)  # Monday 23:00
        test_datetime = test_datetime.replace(tzinfo=self.timezone)
        data = self.scheduler.get_event(test_datetime)
        self.assertEqual(data.data, 18.0)

        # Test during overnight period
        test_datetime = datetime(2024, 1, 2, 2, 0)  # Tuesday 2:00
        test_datetime = test_datetime.replace(tzinfo=self.timezone)
        data = self.scheduler.get_event(test_datetime)
        self.assertEqual(data.data, 18.0)

    def test_event_time_truncation(self) -> None:
        """
        Test that event times are properly truncated to minute precision.

        Verifies that when creating a WeeklyScheduleEvent with a time containing
        seconds and microseconds, they are truncated to maintain consistent time handling.
        """
        # Create time with seconds and microseconds
        test_time = time(14, 30, 45, 123456)

        event = WeeklyScheduleEvent(id="test_truncation", time=test_time, data=21.0, days=[Weekday.MONDAY])

        # Verify seconds and microseconds are truncated
        self.assertEqual(event.time.second, 0)
        self.assertEqual(event.time.microsecond, 0)

        # Verify hours and minutes are preserved
        self.assertEqual(event.time.hour, test_time.hour)
        self.assertEqual(event.time.minute, test_time.minute)

    def test_validate_event_conflict(self) -> None:
        """
        Test that conflicting schedule events are properly detected and rejected.

        Verifies that when attempting to add events with the same time on the same days
        as existing events, an InvalidScheduleError is raised, preventing schedule conflicts.
        """
        self.confict_schedule: str = """
            weekday_office2:
                devices: ["device1", "device2", "device3"]
                days: ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]
                events:
                    - time: "07:00"
                      data: 19.5,
                    - time: "08:30"
                      data: 21.0
                    - time: "17:30"
                      data: 18.0
            weekend_office2:
                devices: ["device1", "device2"]
                days: ["SATURDAY", "SUNDAY"]
                events:
                    - time: "00:00"
                      data: 17.0
                    - time: "10:00"
                      data: 19.0
                    - time: "18:00"
                      data: 17.0
                """
        with self.assertRaises(WeeklyRecurringSchedulerError):
            self.scheduler._add_schedules(yaml.safe_load(self.confict_schedule))


if __name__ == "__main__":
    unittest.main()
