---
id: intro
title: Data Engine
sidebar_label: Introduction
---

The `data_engine` package serves as the central component for data processing, forecasting, and event handling within the system. It is composed of several specialized sub-packages that work together to manage data, devices, and grid events.

## Sub-packages

-   **database**: Provides modules for interacting with database systems, including InfluxDB for time-series data and Redis for caching and configuration. It handles data synchronization and retrieval for cloud telemetry.

-   **device**: Contains modules for device classification and management. It defines device types and provides a standardized way to handle various devices within the system.

-   **events**: Manages event-driven communication, particularly for handling RPC requests and responses related to forecasting. It ensures reliable and efficient asynchronous interactions.

-   **forecaster**: Dedicated to generating and managing time-series forecasts. It uses historical data and forecasting models to predict future data points, enabling proactive decision-making.

-   **grap**: Implements Grid Response and Protection (GRAP) functionality. It detects grid events like blackouts and manages the system's response to ensure stability and reliability.