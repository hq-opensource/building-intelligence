---
id: database
title: Database
sidebar_label: Database
---

The `data_engine.database` package provides a suite of modules for robust interaction with various database systems, primarily focusing on InfluxDB for time-series data and Redis for caching and configuration management. These modules are essential for the data engine's core operations, ensuring efficient data retrieval, storage, and synchronization.

## InfluxMirror

The `InfluxMirror` class is responsible for synchronizing time-series data from a remote InfluxDB Cloud instance to a local InfluxDB server. This module handles the fetching of measurements, fields, and historical data, providing a reliable mechanism for data replication.

### Key Responsibilities:

- **Data Synchronization**: Mirrors data from an InfluxDB Cloud instance to a local InfluxDB server.
- **Measurement and Field Fetching**: Retrieves all measurements and their corresponding fields from the source bucket.
- **Historical Data**: Fetches historical data, with special handling for certain measurements like `historic` to retrieve a longer time range (e.g., 20 days).
- **Scheduled Syncs**: Runs synchronization tasks at regular intervals (e.g., hourly) to keep the local database up-to-date.
- **Error Handling**: Implements back-off strategies for handling rate-limiting errors (HTTP 429) from the InfluxDB Cloud API.
- **Resource Management**: Ensures that InfluxDB client connections are properly closed upon object destruction.

## RetrieveDataForCloud

The `RetrieveDataForCloud` class is designed to fetch and organize real-time measurement data from InfluxDB. It prepares the data for cloud consumption by structuring it for telemetry, handling potential data gaps, and ensuring the data is in a suitable format for upstream services.

### Key Responsibilities:

- **Real-time Data Retrieval**: Fetches the latest data points for measurements containing "real" in their names.
- **Data Aggregation**: Retrieves data from all available InfluxDB buckets.
- **Telemetry Formatting**: Organizes the retrieved data into a nested dictionary format suitable for cloud telemetry, including timestamps and geographical coordinates.
- **Dynamic Query Generation**: Constructs InfluxDB Flux queries dynamically to fetch data for specified fields and tags.
- **Data Cleaning**: Handles missing data by replacing NaN values with 0.0.