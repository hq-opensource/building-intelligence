---
id: events
title: Events
sidebar_label: Events
---

The `data_engine.events` package is responsible for handling event-driven communication within the data engine. It provides modules that manage asynchronous interactions, such as handling RPC (Remote Procedure Call) requests and responses, which are crucial for the distributed nature of the system.

## Forecaster RPC Answer

This module is dedicated to managing forecast-related RPCs. It subscribes to forecast request topics, processes incoming messages, and coordinates the retrieval of cached or newly computed forecasts. The module integrates with InfluxDB for data retrieval and Redis for caching and message brokering, ensuring efficient and reliable forecast delivery.

### Key Responsibilities:

-   **RPC Handling**: Manages RPC (Remote Procedure Call) answers for forecaster requests.
-   **Subscription to Topics**: Subscribes to forecast request topics using a Redis-based event broker (`FastStream`).
-   **Request Processing**: Handles incoming requests for non-controllable load forecasts.
-   **Caching Mechanism**:
    -   Checks for a cached forecast in Redis that matches the request parameters (start, stop, interval).
    -   If a valid cache exists, it returns the cached data to avoid re-computation.
    -   If no valid cache is found, it proceeds to compute a new forecast.
-   **Forecast Computation**:
    -   Utilizes the `ForecastRetriever` to compute new forecasts when a cached version is unavailable or outdated.
    -   Saves the newly computed forecast to the Redis cache with an expiration time (e.g., 24 hours).
-   **Integration**:
    -   Connects to InfluxDB for retrieving the necessary data for forecasting.
    -   Uses a Redis client for both caching and as a message broker.
-   **Logging**: Provides detailed logging for received requests, cache status (hit or miss), and the source of the returned forecast (cached or newly computed).