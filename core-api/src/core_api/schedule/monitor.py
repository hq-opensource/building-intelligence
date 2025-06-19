"""
Scheduler Monitoring Module

This module provides capabilities for monitoring and managing schedulers for various devices
and preference types in a building energy management system. It handles scheduler registration,
data extraction, and event tracking across different control and preference types.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

from common.database.influxdb import InfluxManager
from common.database.redis import RedisClient
from common.util.logging import LoggingUtil
from core_api.schedule.device_scheduler import DeviceScheduler
from core_api.schedule.models import (
    CONTROL_TO_PREFERENCE_TYPE_MAPPING,
    AbstractScheduler,
    ControlType,
    PreferenceType,
    ScheduleEventData,
)
from core_api.schedule.weekly_scheduler import WeeklyRecurringScheduler


logger = LoggingUtil.get_logger(__name__)


class SchedulerMonitor:
    """
    Monitors and manages schedulers for multiple devices and preference types.

    This class serves as a central registry and controller for all schedulers in the system.
    It is responsible for:
    - Loading device configurations and creating appropriate scheduler instances
    - Maintaining a registry of schedulers organized by control and preference types
    - Providing interfaces to access scheduler data and current schedule states
    - Tracking changes in scheduled events to notify the system of updates
    - Supporting both recurring weekly schedules and device-specific schedules
    """

    def __init__(
        self,
        redis_client: RedisClient,
        influx_manager: InfluxManager,
        time_step_duration_in_seconds: int = 60,
    ):
        """
        Initialize the scheduler monitor with device configurations.

        Args:
            redis_client: Redis client for caching and retrieving event data
            influx_manager: Manager for time series data operations
            time_step_duration_in_seconds: Duration of each time step in seconds (default: 60)
        """

        self._redis_client = redis_client
        self._influx_manager = influx_manager
        self._time_step_duration_in_seconds: int = time_step_duration_in_seconds

        # Initialize map of devices
        self._devices: Dict[str, Dict[str, Any]] = {
            device["entity_id"]: device for device in redis_client.safe_read_from_redis("user_devices") or []
        }

        # Initialize scheduler dictionary
        self.schedulers = self._initialize_scheduler_dictionary()

        # Initialize schedulers for all control types and preference types
        self._register_all_schedulers()

    def _initialize_scheduler_dictionary(
        self,
    ) -> Dict[ControlType | PreferenceType, Dict[str, AbstractScheduler]]:
        """
        Initialize the nested dictionary structure for schedulers.

        This method creates the initial structure to store all schedulers
        organized by control and preference types.

        Returns:
            Empty dictionary with keys for all control and preference types
        """

        schedulers: Dict[ControlType | PreferenceType, Dict[str, AbstractScheduler]] = {}

        # Initialize dictionaries for each control and preference type
        for control_type in ControlType:
            schedulers[control_type] = {}

        for preference_type in PreferenceType:
            schedulers[preference_type] = {}

        return schedulers

    def _register_all_schedulers(self) -> None:
        """
        Register all schedulers for both control types and preference types.

        This method initiates the registration process for all supported
        scheduler types in the system.
        """

        # Process control types first
        for control_type in ControlType:
            self._register_control_type_schedulers(control_type)

        # Process preference types separately
        for preference_type in PreferenceType:
            self._register_preference_type_schedulers(preference_type)

    def _register_control_type_schedulers(self, control_type: ControlType) -> None:
        """
        Register schedulers for a specific control type.

        Creates and registers device schedulers for the specified control type
        for all devices in the system.

        Args:
            control_type: The control type to register schedulers for
        """

        # Register device-specific schedulers for this control type
        device_schedulers = self._extract_device_schedulers(control_type)
        self._add_schedulers_to_registry(control_type, device_schedulers)

    def _register_preference_type_schedulers(self, preference_type: PreferenceType) -> None:
        """
        Register schedulers for a specific preference type.

        Creates and registers weekly recurring schedulers for devices
        that have configurations for the specified preference type.

        Args:
            preference_type: The preference type to register schedulers for
        """

        weekly_schedulers = self._extract_weekly_schedulers(preference_type)
        self._add_schedulers_to_registry(preference_type, weekly_schedulers)

    def _add_schedulers_to_registry(
        self, type_key: PreferenceType | ControlType, schedulers_dict: Dict[str, AbstractScheduler]
    ) -> None:
        """
        Add schedulers to the registry under the specified type key.

        This method handles the actual insertion of scheduler instances
        into the registry dictionary.

        Args:
            type_key: The type key (control or preference type)
            schedulers_dict: Dictionary mapping device IDs to schedulers
        """

        for device_id, scheduler in schedulers_dict.items():
            if device_id not in self.schedulers[type_key]:
                self.schedulers[type_key][device_id] = scheduler

    def _extract_weekly_schedulers(self, preference_type: PreferenceType) -> Dict[str, AbstractScheduler]:
        """
        Extract and create weekly schedulers for devices with the specified preference type.

        This method creates WeeklyRecurringScheduler instances for devices that
        have configuration data for the specified preference type.

        Args:
            preference_type: The type of preference to extract schedulers for
        Returns:
            Dict mapping device IDs to their weekly schedulers
        """

        schedulers: Dict[str, AbstractScheduler] = {}
        for device_id, device_data in self._devices.items():
            if preference_type in device_data and device_data[preference_type]:
                schedulers[device_id] = WeeklyRecurringScheduler(
                    device_data[preference_type], self._time_step_duration_in_seconds
                )
        return schedulers

    def _extract_device_schedulers(self, control_type: ControlType) -> Dict[str, AbstractScheduler]:
        """
        Extract and create device schedulers for the specified control type.

        This method creates DeviceScheduler instances for all devices in the system
        for the specified control type, allowing for direct control overrides.

        Args:
            control_type: The control type to extract schedulers for
        Returns:
            Dict mapping device IDs to their device schedulers
        """

        labels_influx: Dict[str, Any] = self._redis_client.safe_read_from_redis("influxdb_mapping")
        devices: Dict = self._redis_client.safe_read_from_redis("user_devices")

        schedulers: Dict[str, AbstractScheduler] = {}
        for device_id in self._devices.keys():
            schedulers[device_id] = DeviceScheduler(
                device_id,
                control_type,
                self._redis_client,
                self._influx_manager,
                labels_influx,
                devices,
                self._time_step_duration_in_seconds,
            )
        return schedulers

    def show_events_data(self, type_key: PreferenceType | ControlType, timestamp: datetime) -> None:
        """
        Display current event data for all devices of a specific type.

        This method logs the current scheduled events for all devices
        of the specified control or preference type.

        Args:
            type_key: The type of control or preference being displayed
            timestamp: The timestamp for which to retrieve event data
        """

        if type_key not in self.schedulers:
            logger.warning(f"No schedulers found for control type: {type_key}")
            return

        device_ids = self._devices.keys()

        for device_id in device_ids:
            self.show_device_event_data(device_id, type_key, timestamp)

    def show_device_event_data(
        self, device_id: str, type_key: PreferenceType | ControlType, timestamp: datetime
    ) -> None:
        """
        Display event data for a specific device and type.

        Logs the current scheduled event data for a specific device
        and indicates whether the event has changed from the previous time step.

        Args:
            device_id: The unique identifier of the device
            type_key: The preference or control type to check
            timestamp: The timestamp for which to retrieve event data
        """

        current_time = timestamp.astimezone()
        event_data, changed = self.get_device_event_data_with_changed_flag(device_id, type_key, current_time)
        if event_data:
            logger.info(f"{type_key} - device_id: {device_id}, event_data: {event_data}, event_changed: {changed}")

    def get_device_scheduler(
        self, device_id: str, type_key: PreferenceType | ControlType
    ) -> Optional[DeviceScheduler | WeeklyRecurringScheduler]:
        """
        Get scheduler for a specific device and type.

        This method retrieves the scheduler instance for a device.
        If no scheduler is found for a control type, it will attempt to fallback
        to the corresponding preference type.

        Args:
            device_id: The unique identifier of the device
            type_key: The preference or control type to check

        Returns:
            DeviceScheduler or WeeklyRecurringScheduler if found, None otherwise
        """
        # Try to get scheduler for the device and type
        return self.schedulers.get(type_key, {}).get(device_id)

    def get_device_event_data(
        self, device_id: str, type_key: PreferenceType | ControlType, timestamp: datetime
    ) -> Optional[ScheduleEventData]:
        """
        Get scheduled event data for a specific device at a given timestamp.

        This method retrieves the currently active scheduled event for a device.
        If no event is found for a control type, it will attempt to fallback
        to the corresponding preference type.

        Args:
            device_id: The unique identifier of the device
            type_key: The preference or control type to check
            timestamp: The datetime to get event data for

        Returns:
            ScheduleEventData if found, None otherwise
        """

        # Try to get scheduler for the device and type
        scheduler = self.get_device_scheduler(device_id, type_key)

        # Get data from scheduler if available
        data = scheduler.get_event_data(timestamp) if scheduler else None

        # If no data and type_key is a ControlType, try with corresponding PreferenceType
        if data is None and isinstance(type_key, ControlType):
            preference_type = CONTROL_TO_PREFERENCE_TYPE_MAPPING.get(type_key)
            if preference_type:
                data = self.get_device_event_data(device_id, preference_type, timestamp)

        return data

    def get_device_event_data_with_changed_flag(
        self, device_id: str, type_key: PreferenceType | ControlType, timestamp: datetime
    ) -> Tuple[Optional[ScheduleEventData], bool]:
        """
        Get device event data with a flag indicating if the event has changed.

        This method retrieves the current event data and determines if it has
        changed from the previous time step. It also caches the current event
        value in Redis for future comparisons.

        Args:
            device_id: The unique identifier of the device
            type_key: The preference or control type to check
            timestamp: The datetime to get event data for

        Returns:
            Tuple containing the event data (or None) and a boolean indicating
            whether the event has changed from the previous time step
        """

        timestamp = timestamp.replace(microsecond=0).astimezone()
        redis_event_value_key = f"event_value_{type_key}_{device_id}"

        previous_event_data = self._redis_client.safe_read_from_redis(redis_event_value_key)

        if previous_event_data:
            logger.debug(f"previous_event_data ({redis_event_value_key}) read from redis cache")
        else:
            logger.debug(f"previous_event_data ({redis_event_value_key}) not in redis cache")
            previous_timestamp = timestamp - timedelta(seconds=self._time_step_duration_in_seconds)
            previous_event = self.get_device_event_data(device_id, type_key, previous_timestamp)
            previous_event_data = previous_event.data if previous_event is not None else None

        current_data = self.get_device_event_data(device_id, type_key, timestamp)
        current_event_data = current_data.data if current_data is not None else None
        current_from_direct_control = current_data.from_direct_control if current_data is not None else False

        changed_flag = (previous_event_data != current_event_data) and current_from_direct_control is False

        # on enregistre la dernière valeur du device de facon ephemere soit deux fois le time_step de la schédule
        self._redis_client.save_in_redis_with_expiration(
            redis_event_value_key, current_event_data, self._time_step_duration_in_seconds * 2
        )

        return current_data, changed_flag
