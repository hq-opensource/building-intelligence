---
id: database
title: Database
---

The `database` package provides common modules for interacting with various databases.

It includes:
- `influxdb`: A client for managing and querying time-series data in InfluxDB.
- `redis`: A client for simplified interactions with a Redis database, including JSON serialization.

## InfluxManager

The `InfluxManager` class is designed to simplify interactions with InfluxDB. It provides a comprehensive set of methods for reading, writing, and querying time-series data, as well as managing InfluxDB buckets and retrieving metadata such as measurements and fields. This class abstracts away the complexity of the underlying InfluxDB client, offering a more intuitive and streamlined interface for common database operations.

### Initialization

To begin using the `InfluxManager`, you first need to initialize it with your InfluxDB connection details. The `__init__` method allows you to configure the manager with the necessary credentials to connect to your InfluxDB instance.

- **`__init__(self, url, org, token)`**: Initializes the `InfluxManager` with the InfluxDB URL, organization, and authentication token. These parameters can be provided directly or through environment variables for easier configuration.

### Core Functionalities

The `InfluxManager` offers a variety of methods to handle different data operations, from simple reads to more complex queries involving data aggregation and downsampling.

- **`read(self, start, stop, msname, fields, bucket, tags=None, interval="10m", agg_func="mean")`**: Reads data from InfluxDB for a specified time range, measurement, and fields. It also supports optional downsampling, allowing you to aggregate data over a given interval (e.g., "10m", "1h") using a specified function (e.g., "mean", "last"). This is particularly useful for handling large datasets efficiently.

- **`synchronous_write(self, bucket, data, data_frame_measurement_name, tags=None)`**: Writes a pandas DataFrame to InfluxDB synchronously. This method is ideal for ensuring that your data is written to the database before proceeding with other operations.

- **`read_all_fields(self, start, stop, msname, bucket, tags=None)`**: Reads all fields from a given measurement within a specified time range. This is useful when you need to retrieve all available data for a particular measurement without specifying each field individually.

- **`read_accumulated_value(self, start, stop, msname, fields, bucket, timestep, tags=None)`**: Reads accumulated values by calculating the difference between consecutive data points. This is particularly useful for meters that report total accumulated values, allowing you to determine consumption over a specific interval.

- **`read_accumulated_value_in_seconds(self, start, stop, msname, fields, bucket, duration, tags=None)`**: Similar to `read_accumulated_value`, but with the duration specified in seconds for more granular control.

- **`read_average_value_in_seconds(self, bucket, measurement, fields, duration, tags=None)`**: Reads the average value of specified fields over a given time range, looking back from the current time. This is useful for getting a quick overview of recent trends.

- **`read_last_data_point(self, bucket, measurement, fields, tags=None)`**: Retrieves the last recorded data point for specified fields. This is ideal for getting the most up-to-date information from your time-series data.

### API Accessors

For more advanced use cases, the `InfluxManager` provides direct access to the underlying InfluxDB client APIs.

- **`get_write_api(self, tags=None)`**: Retrieves a configured `WriteApi` instance, allowing you to perform custom write operations.
- **`get_buckets_api(self)`**: Retrieves the `BucketsApi` instance for managing InfluxDB buckets.
- **`get_query_api(self)`**: Retrieves the `QueryApi` instance for executing custom Flux queries.

### Metadata Retrieval

The `InfluxManager` also includes methods for discovering the structure of your InfluxDB data.

- **`get_measurements_on_bucket(self, bucket)`**: Retrieves all measurement names within a specified bucket.
- **`get_fields(self, bucket, measurement)`**: Retrieves all field names for a given measurement within a bucket.

## RedisClient

The `RedisClient` class provides a simplified and convenient interface for interacting with a Redis database. It handles common operations such as storing, retrieving, and managing data, with built-in support for JSON serialization and deserialization. This makes it easy to work with complex data structures without having to manually handle the conversion to and from strings.

### Initialization

To start using the `RedisClient`, you need to initialize it with the connection details for your Redis server.

- **`__init__(self, host, port, password)`**: Initializes the `RedisClient` with the Redis host, port, and password. These can be provided directly or through environment variables for flexible configuration.

### Core Functionalities

The `RedisClient` offers straightforward methods for data manipulation, ensuring that your interactions with Redis are both simple and safe.

- **`save_in_redis(self, key, value)`**: Saves a value to the Redis database under a specified key. The value is automatically serialized to JSON, allowing you to store complex data types with ease.

- **`safe_read_from_redis(self, key)`**: Retrieves a value from Redis for a given key. The retrieved value is deserialized from JSON, and the method gracefully handles cases where the key does not exist by returning `None`.

- **`save_in_redis_with_expiration(self, key, value, expiration_in_seconds)`**: Saves a value to Redis with a specified expiration time in seconds. This is useful for caching data or storing temporary information that should be automatically removed after a certain period.

By providing these high-level abstractions, the `database` package simplifies database interactions and helps you write cleaner, more maintainable code.