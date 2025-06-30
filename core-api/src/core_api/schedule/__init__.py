"""
The `schedule` package provides a framework for managing device schedules.

It includes:
- `device_scheduler`: Implements device-specific scheduling functionality.
- `models`: Defines core data models and enumerations for scheduling.
- `monitor`: Provides capabilities for monitoring and managing schedulers.
- `weekly_scheduler`: Implements a scheduler for managing weekly recurring events.
"""

"""
The `core_api.schedule` package provides a robust framework for managing and
monitoring device schedules within the building intelligence system. It includes
modules for handling both device-specific and weekly recurring schedules, as well
as data models and monitoring tools to ensure reliable and efficient scheduling
operations.

Modules:
- `device_scheduler.py`: Implements the `DeviceScheduler` class, which manages
  schedules for individual devices. It handles the storage, retrieval, and
  application of schedule data for device control, interfacing with both InfluxDB
  and Redis.

- `models.py`: Defines the core data models and enumerations used for scheduling,
  such as `ScheduleEvent`, `WeeklyScheduleEvent`, and `PreferenceType`. These models
  provide a structured and consistent way to represent and manipulate time-based
  events.

- `monitor.py`: Contains the `SchedulerMonitor` class, which serves as a central
  registry and controller for all schedulers in the system. It is responsible for
  loading device configurations, creating scheduler instances, and tracking
  changes in scheduled events.

- `weekly_scheduler.py`: Implements the `WeeklyRecurringScheduler` class for
  managing weekly recurring events. It supports multiple schedules with specific
  time slots and handles conflict detection to ensure schedule integrity.
"""
