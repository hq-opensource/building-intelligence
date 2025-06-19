from pathlib import Path

import yaml

from common.database.redis import RedisClient
from common.util.logging import LoggingUtil


logger = LoggingUtil.get_logger(__name__)


class RedisYAMLSaver:
    def __init__(
        self,
        redis_client: RedisClient,
    ) -> None:
        """
        Initialize the RedisDevicesSaver with a Redis client and the path to the folder containing YAML files.

        Args:
            redis_client (RedisClient): The Redis client instance.
            folder_path (str): The folder that contains the yaml files.
        """
        self._redis_client = redis_client

    def upload_yaml_files_to_redis(self, folder_path: str) -> None:
        """
        Finds all YAML files in the folder and uploads the data to Redis.
        Each file will be saved in Redis with the file name as the key and field data
        (with field IDs as subkeys) as the value.
        """
        # List all YAML files in the folder
        folder = Path(folder_path)
        yaml_files = [file for file in folder.glob("*.yaml")] + [file for file in folder.glob("*.yml")]

        # Process each YAML file
        for yaml_file in yaml_files:
            self.upload_yaml_file_to_redis(yaml_file)

    def upload_yaml_file_to_redis(self, yaml_file: Path, redis_key: str | None = None) -> None:
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
