"""
This module provides the `RedisYAMLSaver` class for uploading YAML file data to Redis.

It facilitates reading YAML files from a specified folder and storing their content
in Redis, using the filename as the Redis key.
"""

from pathlib import Path

import yaml

from common.database.redis import RedisClient
from common.util.logging import LoggingUtil


logger = LoggingUtil.get_logger(__name__)


class RedisYAMLSaver:
    """
    A utility class for uploading YAML file data to Redis.

    This class provides methods to read YAML files from a specified folder
    and store their content in Redis, using the filename (without extension)
    as the Redis key.
    """

    def __init__(
        self,
        redis_client: RedisClient,
    ) -> None:
        """
        Initializes the RedisYAMLSaver with a Redis client.

        Args:
            redis_client (RedisClient): The Redis client instance used for saving data.
        """
        self._redis_client = redis_client

    def upload_yaml_files_to_redis(self, folder_path: str) -> None:
        """
        Discovers and uploads all YAML files from a given folder to Redis.

        Each YAML file's content is parsed and saved to Redis. The Redis key
        for each entry is derived from the filename (e.g., 'my_config.yaml'
        becomes 'my_config' in Redis).

        Args:
            folder_path (str): The path to the folder containing the YAML files.
        """
        # List all YAML files in the folder
        folder = Path(folder_path)
        yaml_files = [file for file in folder.glob("*.yaml")] + [file for file in folder.glob("*.yml")]

        # Process each YAML file
        for yaml_file in yaml_files:
            self.upload_yaml_file_to_redis(yaml_file)

    def upload_yaml_file_to_redis(self, yaml_file: Path, redis_key: str | None = None) -> None:
        """
        Uploads a single YAML file's content to Redis.

        The content of the YAML file is parsed and stored in Redis. The Redis key
        can be explicitly provided; otherwise, the filename (without extension)
        is used as the key.

        Args:
            yaml_file (Path): The path object of the YAML file to upload.
            redis_key (str | None): Optional. The key to use when saving data to Redis.
                                     If None, the filename (without extension) is used.
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
