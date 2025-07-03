---
sidebar_position: 2
---

# Database

This section covers the database utilities used in the frontend application.

## RedisYAMLSaver

The `RedisYAMLSaver` class is a utility for reading data from YAML files and storing it into a Redis database.

### Functionality

The primary functionality allows for scanning a directory for YAML files (`.yml` or `.yaml`) and uploading the contents of each file to Redis. The Redis key for each entry is typically derived from the filename, but can also be specified manually. This is useful for initializing or updating Redis-based configurations or data stores from human-readable YAML sources.

### Methods

- `__init__(self, redis_client: RedisClient)`: Initializes the `RedisYAMLSaver` with a Redis client.
- `upload_yaml_files_to_redis(self, folder_path: str)`: Scans a directory for YAML files and uploads their contents to Redis.
- `upload_yaml_file_to_redis(self, yaml_file: Path, redis_key: str | None = None)`: Uploads the content of a single YAML file to Redis.