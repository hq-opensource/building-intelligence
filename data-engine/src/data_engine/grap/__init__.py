"""
The `data_engine.grap` package is responsible for implementing the GRAP functionality within the data engine. This package provides
modules for detecting grid events, such as blackouts, and managing the system's
response to ensure stability and reliability.

Modules:
- `detect_blackout.py`: This module contains the `DetectBlackout` class, which is
  designed to identify blackouts by analyzing data interruptions from InfluxDB.
  It communicates the GRAP state and related information through Redis and RPC
  calls, enabling a coordinated response to grid events.
"""
