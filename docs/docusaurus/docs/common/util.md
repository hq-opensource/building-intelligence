---
id: util
title: Util
---

The `util` package provides common utility modules for the application.

It includes:
- `logging`: A utility for configuring and retrieving standardized logger instances.

## LoggingUtil

The `LoggingUtil` class is a utility designed to ensure consistent and centralized logging across the entire application. It provides a straightforward way to configure and retrieve logger instances, allowing for standardized log formatting and level control. By using this utility, you can maintain a uniform logging strategy, which is essential for effective debugging and monitoring.

### Centralized Configuration

One of the key benefits of `LoggingUtil` is its ability to centralize logging configuration. The log level for all loggers obtained through this utility is determined by the `LOGLEVEL` environment variable. This means you can easily adjust the verbosity of your application's logs without modifying the code. For example, you can set `LOGLEVEL` to "DEBUG" during development to get detailed insights, and then switch it to "INFO" or "WARNING" in production to reduce noise.

If the `LOGLEVEL` environment variable is not set or contains an invalid value, the system defaults to `logging.INFO`, ensuring a sensible default behavior.

### Standardized Formatting

`LoggingUtil` also enforces a consistent log format, which includes the timestamp, logger name, log level, and the log message itself. This structured format makes it easier to parse and analyze logs, whether you are reading them directly from the console or using a log management system.

The format is as follows: `%(asctime)s - [%(name)s][%(levelname)s] %(message)s`

### Usage

To use the `LoggingUtil`, you simply need to call the static method `get_logger` and provide a name for your logger. This name is typically the `__name__` of the module where the logger is being used, which helps in identifying the source of the log messages.

- **`get_logger(logger_name: str) -> logging.Logger`**

  This static method retrieves a logger instance with the specified name. If a logger with that name has already been configured, it returns the existing instance; otherwise, it creates and configures a new one. This prevents duplicate handlers from being added, ensuring that log messages are not repeated.

By providing a simple yet powerful way to manage logging, `LoggingUtil` helps improve the maintainability and observability of the application.