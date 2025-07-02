---
sidebar_position: 4
---

# Schedule Module

The `schedule` package provides a robust framework for managing and monitoring device schedules within the building intelligence system. It includes modules for handling both device-specific and weekly recurring schedules, as well as data models and monitoring tools to ensure reliable and efficient scheduling operations.

## Device Scheduler

The `device_scheduler.py` module implements the `DeviceScheduler` class, which manages schedules for individual devices. It handles the storage, retrieval, and application of schedule data for device control, interfacing with both InfluxDB and Redis.

### Class: `DeviceScheduler`

- **`get_event_data(time_target)`**: Retrieves scheduled event data for a specified time.
- **`save_schedule(priority, dispatches, redis_client, influx_manager, from_direct_control)`**: A class method to save device schedules to InfluxDB.

## Models

The `models.py` module defines the core data models and enumerations used for scheduling, such as `ScheduleEvent`, `WeeklyScheduleEvent`, and `PreferenceType`. These models provide a structured and consistent way to represent and manipulate time-based events.

### Key Data Models

- **`ScheduleEvent`**: Represents a single, non-recurring scheduled event with a specific start and end time.
- **`WeeklyScheduleEvent`**: Represents a recurring weekly schedule entry for events that repeat on specific days of the week at a fixed time.
- **`Schedule`**: A container for a collection of scheduled events.
- **`ScheduleEventData`**: A data container for transferring schedule event information.
- **`AbstractScheduler`**: An abstract base class defining the interface for all scheduler implementations.

### Enumerations

- **`Weekday`**: Enum for the days of the week.
- **`PreferenceType`**: Enum for different types of user preferences that can be scheduled.
- **`ControlType`**: Enum for different types of controls that can be applied to devices.

## Monitor

The `monitor.py` module contains the `SchedulerMonitor` class, which serves as a central registry and controller for all schedulers in the system. It is responsible for loading device configurations, creating scheduler instances, and tracking changes in scheduled events.

### Class: `SchedulerMonitor`

- **`get_device_scheduler(device_id, type_key)`**: Gets the scheduler for a specific device and type.
- **`get_device_event_data(device_id, type_key, timestamp)`**: Retrieves scheduled event data for a specific device at a given timestamp, with fallback to preference types.
- **`get_device_event_data_with_changed_flag(device_id, type_key, timestamp)`**: Gets event data along with a flag indicating if the event has changed from the previous time step.

## Weekly Scheduler

The `weekly_scheduler.py` module implements the `WeeklyRecurringScheduler` class for managing weekly recurring events. It supports multiple schedules with specific time slots and handles conflict detection to ensure schedule integrity.

### Class: `WeeklyRecurringScheduler`

- **`get_event(timestamp)`**: Gets the active schedule event at the specified timestamp.
- **`get_event_data(timestamp)`**: Gets the complete event data for the specified timestamp, implementing the `AbstractScheduler` interface.