"""
The `data_engine.forecaster` package is dedicated to generating and managing
time-series forecasts within the data engine. It provides the necessary tools
to predict future data points based on historical trends, which is essential for
proactive decision-making and optimization.

Modules:
- `forecast_retriever.py`: This module contains the `ForecastRetriever` class,
  which is responsible for computing and managing forecasts, with a particular
  focus on non-controllable loads. It leverages historical data from InfluxDB
  and uses forecasting models like Prophet to generate accurate predictions.
"""
