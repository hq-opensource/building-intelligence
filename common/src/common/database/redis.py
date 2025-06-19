import json
import os

from typing import Any

import redis

from common.util.logging import LoggingUtil


logger = LoggingUtil.get_logger(__name__)


class RedisClient:
    def __init__(
        self,
        host: str = str(os.getenv("REDIS_HOST")),
        port: int = int(os.getenv("REDIS_PORT", 6379)),
        password: str = str(os.getenv("REDIS_PASSWORD")),
    ):
        """Initialize Redis client with basic connection setup."""
        self.redis_db = redis.Redis(host=host, port=port, password=password)

    def save_in_redis(self, key: str, value: Any) -> None:
        """Set a value in the Redis database."""
        try:
            self.redis_db.set(key, json.dumps(value))
        except redis.RedisError as e:
            logger.exception(f"Redis error during set: {e}")
            raise

    def safe_read_from_redis(self, key: str) -> Any | None:
        """Get a value from the Redis database."""
        try:
            value = self.redis_db.get(key)
            return json.loads(value) if value else None
        except redis.RedisError as e:
            logger.exception(f"Redis error during get: {e}")
            return None

    def save_in_redis_with_expiration(self, key: str, value: Any, expiration_in_seconds: int) -> None:
        """Set a value with an expiration time."""
        try:
            self.redis_db.set(
                name=key,
                value=json.dumps(value),
                ex=int(expiration_in_seconds),
            )
        except redis.RedisError as e:
            logger.exception(f"Redis error during setex: {e}")
            raise
