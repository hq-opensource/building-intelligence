---
id: forecaster
title: Forecaster
sidebar_label: Forecaster
---

The `data_engine.forecaster` package is dedicated to generating and managing time-series forecasts within the data engine. It provides the necessary tools to predict future data points based on historical trends, which is essential for proactive decision-making and optimization.

## ForecastRetriever

This module contains the `ForecastRetriever` class, which is responsible for computing and managing forecasts, with a particular focus on non-controllable loads. It leverages historical data from InfluxDB and uses forecasting models like Prophet to generate accurate predictions.

### Key Responsibilities:

-   **Forecast Generation**: Computes forecasts for non-controllable loads.
-   **Historical Data Analysis**:
    -   Retrieves historical data for total power consumption and all controllable loads (e.g., thermostats, batteries, EVs, water heaters) from InfluxDB.
    -   Calculates the historical non-controllable load by subtracting the consumption of controllable devices from the total consumption.
-   **Prophet Model Integration**:
    -   **Training**: Trains a Prophet forecasting model using the computed historical non-controllable load data. The model is configured with daily seasonality and a flat growth trend.
    -   **Prediction**: Uses the trained model to generate future forecasts for a specified time period and interval.
-   **Data Persistence**:
    -   Saves the generated forecast back to InfluxDB for future use and analysis.
    -   Stores the historical non-controllable loads in InfluxDB as well.
-   **Configuration Management**:
    -   Loads necessary configurations, such as InfluxDB bucket names and device information, from a Redis database.
-   **Output Formatting**:
    -   Returns the final forecast as a dictionary with timestamps as keys and forecasted values as values, making it easy to consume by other services.