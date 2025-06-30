"""
This module provides a utility class, LoggingUtil, for consistent logging across the application.

It offers a static method to configure and retrieve logger instances, allowing for centralized
control over log levels and formatting based on environment variables.
"""

import logging
import os


class LoggingUtil:
    """
    A utility class for configuring and retrieving loggers.

    This class provides a static method to get a logger instance with a predefined
    format and level, configurable via environment variables.
    """

    @staticmethod
    def get_logger(logger_name: str) -> logging.Logger:
        """
        Retrieves a configured logger instance.

        The logger's level is determined by the "LOGLEVEL" environment variable (e.g., "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL").
        If "LOGLEVEL" is not set or is invalid, it defaults to logging.INFO.
        The logger outputs to the console with a specific format including timestamp, logger name, level, and message.

        Args:
            logger_name (str): The name of the logger to retrieve.

        Returns:
            logging.Logger: A configured logger instance.
        """
        logger = logging.getLogger(logger_name)
        log_level = os.getenv("LOGLEVEL", logging.INFO)

        if log_level not in logging._nameToLevel.keys():
            log_level = logging.INFO

        logger.setLevel(log_level)

        # Ensure the logger does not add duplicate handlers if called multiple times for the same logger_name
        if not logger.handlers:
            log_formatter = logging.Formatter("%(asctime)s - [%(name)s][%(levelname)s] %(message)s")
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(log_formatter)
            logger.addHandler(console_handler)

        return logger
