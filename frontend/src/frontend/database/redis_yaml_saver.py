"""
This module contains the RedisYAMLSaver class, a utility for reading data from
YAML files and storing it into a Redis database.

The primary functionality allows for scanning a directory for YAML files (`.yml` or
`.yaml`) and uploading the contents of each file to Redis. The Redis key for
each entry is typically derived from the filename, but can also be specified
manually. This is useful for initializing or updating Redis-based configurations
or data stores from human-readable YAML sources.
"""

from pathlib import Path

import yaml

from common.database.redis import RedisClient
from common.util.logging import LoggingUtil


logger = LoggingUtil.get_logger(__name__)


class RedisYAMLSaver:
    """A utility class to save data from YAML files to a Redis database."""

    def __init__(
        self,
        redis_client: RedisClient,
    ) -> None:
        """
        Initializes the RedisYAMLSaver with a Redis client.

        Args:
            redis_client (RedisClient): An instance of the Redis client.
        """
        self._redis_client = redis_client

    def upload_yaml_files_to_redis(self, folder_path: str) -> None:
        """
        Scans a directory for YAML files and uploads their contents to Redis.

        Each YAML file's content is stored in Redis under a key derived from the
        file's name (without the extension).

        Args:
            folder_path (str): The path to the directory containing the YAML files.
        """
        # List all YAML files in the folder
        folder = Path(folder_path)
        yaml_files = [file for file in folder.glob("*.yaml")] + [file for file in folder.glob("*.yml")]

        # Process each YAML file
        for yaml_file in yaml_files:
            self.upload_yaml_file_to_redis(yaml_file)

    def upload_yaml_file_to_redis(self, yaml_file: Path, redis_key: str | None = None) -> None:
        """
        Uploads the content of a single YAML file to Redis.

        The data is parsed from the YAML file and stored in Redis. If a Redis
        key is not provided, it is generated from the YAML file's name.

        Args:
            yaml_file (Path): The path to the YAML file.
            redis_key (str | None, optional): The key to use for storing the data
                in Redis. Defaults to None, in which case the file stem is used.
        """
        try:
            with yaml_file.open("r") as f:
                # Parse the YAML file
                data_to_store = yaml.safe_load(f)

            # Create a dictionary to store data with field ids as keys
            if redis_key is None:
                redis_key = yaml_file.stem  # Use the filename (without extension) as Redis key

            # Save the data to Redis
            self._redis_client.save_in_redis(redis_key, data_to_store)
            logger.info(f"Successfully uploaded {yaml_file.name} data to Redis under key: {redis_key}")

        except yaml.YAMLError as exc:
            logger.error(f"Error reading YAML file {yaml_file.name}: {exc}")
        except Exception as e:
            logger.error(f"Unexpected error while processing {yaml_file.name}: {e}")
