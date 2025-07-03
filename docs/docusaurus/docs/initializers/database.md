---
sidebar_position: 1
---

# Database Initializers

The `database` package contains modules for initializing and managing database connections and data.

## Modules

### `influx_init`

This module is responsible for initializing the InfluxDB client. It ensures that the necessary buckets are created for storing time-series data.

### `redis_yaml_saver`

This module provides functionality to upload data from YAML files directly into Redis. This is useful for populating Redis with configuration data or initial datasets.