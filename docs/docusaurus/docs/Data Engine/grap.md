---
id: grap
title: GRAP
sidebar_label: GRAP
---

The `data_engine.grap` package is responsible for implementing the GRAP (Grid Response and Protection) functionality within the data engine. This package provides modules for detecting grid events, such as blackouts, and managing the system's response to ensure stability and reliability.

## DetectBlackout

This module contains the `DetectBlackout` class, which is designed to identify blackouts by analyzing data interruptions from InfluxDB. It communicates the GRAP state and related information through Redis and RPC calls, enabling a coordinated response to grid events.

### Key Responsibilities:

-   **Blackout Detection**:
    -   Analyzes the `net_power` measurement in InfluxDB to detect significant data interruptions.
    -   A data gap is considered a blackout if it exceeds a configurable duration (e.g., 1-30 minutes).
-   **State Management**:
    -   Checks Redis to determine if a GRAP event is already in progress to avoid redundant actions.
    -   Saves information about detected blackouts (duration and stop time) to Redis with an expiration time.
-   **RPC Communication**:
    -   If a blackout is detected and no GRAP event is active, it initiates an RPC call to a power limit service to activate the GRAP response.
    -   The RPC request includes details about the blackout and the required power limit for the cold load pickup phase.
-   **Coordination**:
    -   Logs the response from the RPC call.
    -   Updates Redis to indicate that the GRAP function has been called and stores the GRAP event details (e.g., duration of the power limit).
-   **Cloud Integration (Future)**:
    -   Includes a placeholder for future logic to communicate with a cloud service for verifying and updating blackout status and power limits.