"""
The `initializers` package serves as the primary entry point for setting up the
foundational components and data structures required for the building intelligence system.
It orchestrates the initialization of databases, device configurations, user profiles,
and other critical settings by aggregating several specialized sub-packages.

Sub-packages:
    - `database`: This package is responsible for all database-related initializations.
        - The `influx_init` submodule handles the setup of the InfluxDB client and ensures
          the creation of necessary data buckets for time-series data.
        - The `redis_yaml_saver` submodule provides functionality to parse YAML configuration
          files and upload their contents into the Redis database.

    - `device`: This package centralizes device-related definitions and helper utilities.
        - The `device` submodule defines the `DeviceType` enumeration, which categorizes
          all supported devices, and the `DeviceHelper` class, which offers static
          methods for querying and managing device lists.

    - `grid_functions_config`: This package contains static configuration files that
      define the behavior of grid-facing services.
        - `grid_service_grap.yaml` provides configuration for the Grid Response
          Aggregation Platform (GRAP).

    - `labels_dbs_config`: This package holds various YAML files that define labels,
      keys, and mappings used across different databases and APIs, ensuring
      consistent data referencing.
        - It includes configurations for APIs (`labels_apis.yaml`), communication
          channels (`labels_channels.yaml`), market parameters (`labels_market.yaml`),
          measurements (`labels_measures.yaml`), and Redis keys (`labels_redis.yaml`).

    - `user`: This package focuses on user-specific data.
        - The `ProfileGenerators` submodule contains tools to create synthetic data
          profiles for simulating user behavior, such as EV charging and water heater usage.
        - The `redis_data_initializer` submodule uses these generated profiles to
          populate the Redis database with initial user data.
"""
