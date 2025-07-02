---
id: common-intro
title: Introduction to the Common Package
sidebar_position: 1
---

The `common` package is a foundational component of the building intelligence system, designed to encapsulate shared modules and utilities that are used across multiple services. Its primary purpose is to promote code reuse, reduce redundancy, and provide centralized, standardized implementations for essential functionalities such as database interactions, device management, and logging.

By consolidating these core services into a single package, the `common` package helps ensure consistency and maintainability throughout the entire system. It provides a reliable foundation that other components can build upon, streamlining development and reducing the risk of errors.

### Key Features

The `common` package is organized into several sub-packages, each dedicated to a specific area of functionality:

- **`database`**: This package provides a set of modules for interacting with various databases.
  - The `influxdb` submodule offers a high-level client for managing and querying time-series data in InfluxDB, simplifying operations like reading, writing, and data aggregation.
  - The `redis` submodule includes a simplified client for interacting with a Redis database, with built-in support for JSON serialization and data expiration.

- **`device`**: This package centralizes all device-related definitions and helper utilities, ensuring a consistent approach to device management.
  - The `helper` submodule defines the `DeviceHelper` Enum, which categorizes different device types. It also provides a collection of static methods for common device operations, such as counting devices by type or filtering them based on specific criteria.

- **`util`**: This package contains common utility modules that provide essential services for the application.
  - The `logging` submodule offers a utility for configuring and retrieving standardized logger instances. This ensures that logging practices are consistent across all components, making it easier to monitor and debug the system.

By providing these well-defined and reusable components, the `common` package plays a crucial role in the overall architecture of the building intelligence system, promoting a more robust, scalable, and maintainable codebase.