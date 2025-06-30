"""
This module provides the RedisClient class for simplified interactions with a Redis database.

It offers methods for storing, retrieving, and managing data with optional expiration times,
handling JSON serialization and deserialization automatically.
"""

import json
import os

from typing import Any

import redis

from common.util.logging import LoggingUtil


logger = LoggingUtil.get_logger(__name__)


class RedisClient:
    """
    A client for interacting with a Redis database.

    This class provides methods for saving and retrieving data from Redis,
    including support for JSON serialization and setting expiration times for keys.
    """

    def __init__(
        self,
        host: str = str(os.getenv("REDIS_HOST")),
        port: int = int(os.getenv("REDIS_PORT", 6379)),
        password: str = str(os.getenv("REDIS_PASSWORD")),
    ):
        """
        Initializes the RedisClient with connection parameters.

        Args:
            host (str): The hostname or IP address of the Redis server. Defaults to REDIS_HOST environment variable.
            port (int): The port number of the Redis server. Defaults to REDIS_PORT environment variable, or 6379.
            password (str): The password for Redis authentication. Defaults to REDIS_PASSWORD environment variable.
        """
        self.redis_db = redis.Redis(host=host, port=port, password=password)

    def save_in_redis(self, key: str, value: Any) -> None:
        """
        Saves a value to the Redis database under a specified key.

        The value is serialized to JSON before being stored.

        Args:
            key (str): The key under which to store the value.
            value (Any): The value to be stored.
        Raises:
            redis.RedisError: If a Redis-specific error occurs during the operation.
        """
        try:
            self.redis_db.set(key, json.dumps(value))
        except redis.RedisError as e:
            logger.exception(f"Redis error during set: {e}")
            raise

    def safe_read_from_redis(self, key: str) -> Any | None:
        """
        Retrieves a value from the Redis database for a given key.

        The retrieved value is deserialized from JSON. If the key does not exist or an error occurs,
        None is returned.

        Args:
            key (str): The key whose value is to be retrieved.

        Returns:
            Any | None: The deserialized value if found, otherwise None.
        """
        try:
            value = self.redis_db.get(key)
            return json.loads(value) if value else None
        except redis.RedisError as e:
            logger.exception(f"Redis error during get: {e}")
            return None

    def save_in_redis_with_expiration(self, key: str, value: Any, expiration_in_seconds: int) -> None:
        """
        Saves a value to the Redis database with a specified expiration time.

        The value is serialized to JSON before being stored.

        Args:
            key (str): The key under which to store the value.
            value (Any): The value to be stored.
            expiration_in_seconds (int): The time-to-live for the key in seconds.
        Raises:
            redis.RedisError: If a Redis-specific error occurs during the operation.
        """
        try:
            self.redis_db.set(
                name=key,
                value=json.dumps(value),
                ex=int(expiration_in_seconds),
            )
        except redis.RedisError as e:
            logger.exception(f"Redis error during setex: {e}")
            raise
