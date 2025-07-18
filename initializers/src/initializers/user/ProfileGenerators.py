"""
This module contains the `ProfileGenerators` class, which is responsible for
generating various synthetic data profiles.

These profiles are used for simulating different aspects of user behavior and
device operation, such as EV consumption, water heater usage, and power limits.
It integrates with Redis to fetch necessary market labels for profile generation.
"""

import random

from datetime import datetime
from typing import Dict, List

import numpy as np
import pandas as pd

from common.database.redis import RedisClient
from common.util.logging import LoggingUtil


logger = LoggingUtil.get_logger(__name__)


class ProfileGenerators:
    """
    A class dedicated to generating synthetic data profiles for various applications,
    such as EV consumption, water heater usage, and power limits.

    This class utilizes statistical methods and predefined patterns to create
    realistic-looking data for simulation and testing purposes. It relies on
    market labels retrieved from a Redis client for configuration.
    """

    def __init__(
        self,
        redis_client: RedisClient,
    ):
        """
        Initializes the ProfileGenerators with a Redis client.

        Args:
            redis_client (RedisClient): An instance of RedisClient to retrieve market labels.
        """
        # Create self parameters
        self._redis_client = redis_client

        # Read labels
        self._labels_market = redis_client.safe_read_from_redis("labels_market")

    def generate_random_normal_data(self, mean: float, std: float, size: int) -> np.ndarray:
        """
        Generates positive random samples from a normal distribution.

        Args:
            mean (float): The mean of the normal distribution.
            std (float): The standard deviation of the normal distribution.
            size (int): The number of samples to generate.

        Returns:
            np.ndarray: An array of positive random samples from the normal distribution.
        """
        rng = np.random.default_rng()
        data_all = rng.normal(mean, std, size)
        only_positive_data = np.clip(data_all, a_min=0, a_max=None)
        return only_positive_data

    def generate_ev_consumption_profile(self, start_date: datetime, end_date: datetime) -> np.ndarray:
        """
        Generates a random Electric Vehicle (EV) consumption profile with realistic charging patterns.

        The profile is generated based on a time index determined by the market's timestep,
        and incorporates random factors like temperature, speed, and traffic, along with
        predefined charging windows (night, work, home).

        Args:
            start_date (datetime): The start datetime for the profile generation.
            end_date (datetime): The end datetime for the profile generation.

        Returns:
            np.ndarray: A tuple containing:
                        - consumption_array (np.ndarray): The generated EV consumption profile.
                        - charging_pattern (np.ndarray): The chosen charging pattern applied.
        """
        # Generate a time index for a 24-hour period with the time step determined by the market.
        time_index = pd.date_range(
            start=start_date, end=end_date, freq=str(self._labels_market["dac_timestep"]) + "min"
        )

        # Create a random generator
        rng = np.random.default_rng()

        # Generate random values for factors affecting consumption
        temperature = rng.uniform(10, 30, len(time_index))  # Temperature in Celsius
        speed = rng.uniform(20, 80, len(time_index))  # Speed in km/h
        traffic = rng.uniform(0, 1, len(time_index))  # Traffic condition (0 to 1)

        # Define charging patterns
        # Predefined charging windows: e.g., at night, during work hours, at home, etc.
        night_charging_window = (time_index.hour >= 22) | (time_index.hour < 6)  # Night charging (10 PM - 6 AM)
        work_charging_window = (time_index.hour >= 9) & (
            time_index.hour < 17
        )  # Charging during work hours (9 AM - 5 PM)
        home_charging_window = (time_index.hour >= 17) & (time_index.hour < 6)  # Charging at home (6 PM - 10 PM)
        charging_patterns = [night_charging_window * 1.0, work_charging_window * 1.0, home_charging_window * 1.0]

        # Choose a charging pattern
        charging_pattern = random.choice(charging_patterns)
        # Calculate energy consumption based on factors and charging patterns
        base_consumption = rng.uniform(10, 20)  # Base consumption in kWh
        consumption = base_consumption + 0.5 * temperature + 0.2 * speed + 0.1 * traffic + 5 * charging_pattern

        # Add some randomness to the consumption values
        consumption += rng.normal(scale=2, size=len(time_index))

        # Ensure consumption values are non-negative
        consumption_array = np.maximum(consumption, 0)

        return consumption_array, charging_pattern

    def generate_ev_default_consumption(self) -> Dict[str, List]:
        """
        Generates a default EV consumption profile for a predefined horizon.

        This method creates a synthetic consumption profile for an Electric Vehicle
        based on random factors like temperature, speed, traffic, and charging status.
        The length of the profile is determined by the 'dac_horizon' from market labels.

        Returns:
            Dict[str, List]: A dictionary containing the generated consumption profile
                             under the key "profile".
        """
        # Create a random generator
        rng = np.random.default_rng()

        # Generate random values for factors affecting consumption
        temperature = rng.uniform(10, 30, self._labels_market["dac_horizon"])  # Temperature in Celsius
        speed = rng.uniform(20, 80, self._labels_market["dac_horizon"])  # Speed in km/h
        traffic = rng.uniform(0, 1, self._labels_market["dac_horizon"])  # Traffic condition (0 to 1)
        charging = rng.choice([0, 1], self._labels_market["dac_horizon"], p=[0.8, 0.2])  # Charging status (0 or 1)

        # Calculate energy consumption based on factors
        base_consumption = rng.uniform(10, 20)  # Base consumption in kWh
        consumption = base_consumption + 0.5 * temperature + 0.2 * speed + 0.1 * traffic + 5 * charging

        # Add some randomness to the consumption values
        consumption += rng.normal(scale=2, size=self._labels_market["dac_horizon"])

        # Ensure consumption values are non-negative
        consumption_array = np.maximum(consumption, 0)

        return {"profile": consumption_array.tolist()}

    def generate_water_heater_profile(self, start_date: datetime, end_date: datetime) -> np.ndarray:
        """
        Generates a synthetic profile of water heater usage.

        The profile is created based on a time index determined by the market's timestep
        and incorporates predefined usage windows (early morning, middle of day, late night)
        and random water heater capacities.

        Args:
            start_date (datetime): The start datetime for the profile generation.
            end_date (datetime): The end datetime for the profile generation.

        Returns:
            np.ndarray: The generated water heater consumption profile.
        """
        # Generate a time index for a 24-hour period with the time step determined by the market.
        time_index = pd.date_range(
            start=start_date, end=end_date, freq=str(self._labels_market["dac_timestep"]) + "min"
        )

        # Define usage patterns for water heater
        # Predefined usage windows: e.g., early morning, middle of the day, late night
        early_morning_window = (time_index.hour >= 5) & (time_index.hour < 9)  # Early morning (5 AM - 9 AM)
        middle_of_day_window = (time_index.hour >= 11) & (time_index.hour < 15)  # Middle of the day (11 AM - 3 PM)
        late_night_window = (time_index.hour >= 21) | (time_index.hour < 2)  # Late night (9 PM - 2 AM)
        usage_patterns = [early_morning_window * 1.0, middle_of_day_window * 1.0, late_night_window * 1.0]

        # Compute consumption
        capacities_of_water_heaters = [3, 4.5, 5, 5, 6, 7.5]
        consumption_profile = random.choice(usage_patterns) * random.choice(capacities_of_water_heaters)

        return consumption_profile

    def generate_power_limit_profile(self, start_date: datetime, end_date: datetime) -> np.ndarray:
        """
        Generates a synthetic power limit profile.

        This profile defines varying power limits over a specified time range,
        with different limits applied during predefined windows (early morning,
        middle of day, afternoon).

        Args:
            start_date (datetime): The start datetime for the profile generation.
            end_date (datetime): The end datetime for the profile generation.

        Returns:
            np.ndarray: The generated power limit profile.
        """
        # Generate a time index for a 24-hour period with the time step determined by the market.
        time_index = pd.date_range(
            start=start_date, end=end_date, freq=str(self._labels_market["dac_timestep"]) + "min"
        )

        # Define usage patterns for water heater with constant values in the specified windows
        max_limit = 25.0
        power_limit_alternatives = [8.5, 10, 12.5, 15]

        # Predefined usage windows: early morning (5 AM - 9 AM), middle of the day (11 AM - 3 PM), late night (9 PM - 2 AM)
        early_morning_window = (time_index.hour >= 5) & (time_index.hour < 9)
        middle_of_day_window = (time_index.hour >= 11) & (time_index.hour < 15)
        afternoon_window = (time_index.hour >= 21) | (time_index.hour < 2)

        # Initialize power limit profile with the max limit
        morning = np.full(len(time_index), max_limit)
        noon = np.full(len(time_index), max_limit)
        afternoon = np.full(len(time_index), max_limit)

        # Set the power limit within the windows to the window limit
        window_limit = random.choice(power_limit_alternatives)
        morning[early_morning_window] = window_limit
        noon[middle_of_day_window] = window_limit
        afternoon[afternoon_window] = window_limit

        power_limit_profile = random.choice([morning, noon, afternoon])

        return power_limit_profile

    def random_profile_generator(
        self, low_limit: float, high_limit: float, number_type: str = "integer"
    ) -> Dict[str, List]:
        """
        Creates a random profile with values within a specified range, either as integers or continuous floats.

        The profile's length is determined by the 'dac_horizon' from market labels.
        It introduces variations within quarters of the profile.

        Args:
            low_limit (float): The lower bound for the random values.
            high_limit (float): The upper bound for the random values.
            number_type (str): The type of numbers to generate. Can be "integer" or "continuous".
                               Defaults to "integer".

        Returns:
            Dict[str, List]: A dictionary containing the generated profile under the key "profile".

        Raises:
            ValueError: If an invalid `number_type` is provided.
        """
        rng = np.random.default_rng()

        if number_type == "integer":
            daily_profile = np.ones(self._labels_market["dac_horizon"]) * rng.integers(low_limit, high_limit)
            quarter = int(self._labels_market["dac_horizon"] / 4)
            start_1 = rng.integers(0, quarter)
            end_1 = rng.integers(quarter, 2 * quarter)
            daily_profile[start_1:end_1] = rng.integers(low_limit, high_limit)
            start_2 = rng.integers(2 * quarter, 3 * quarter)
            end_2 = rng.integers(3 * quarter, 4 * quarter)
            daily_profile[start_2:end_2] = rng.integers(low_limit, high_limit)
        elif number_type == "continuous":
            daily_profile = np.ones(self._labels_market["dac_horizon"]) * rng.uniform(low_limit, high_limit)
            quarter = int(self._labels_market["dac_horizon"] / 4)
            start_1 = rng.integers(0, quarter)
            end_1 = rng.integers(quarter, 2 * quarter)
            daily_profile[start_1:end_1] = rng.uniform(low_limit, high_limit)
            start_2 = rng.integers(2 * quarter, 3 * quarter)
            end_2 = rng.integers(3 * quarter, 4 * quarter)
            daily_profile[start_2:end_2] = rng.uniform(low_limit, high_limit)
        else:
            raise ValueError("Invalid number_type. Use 'integer' or 'continuous'.")

        return {"profile": daily_profile.tolist()}

    def random_daily_profile(
        self,
        scaling_factor: float,
        horizon: int,
    ) -> Dict[str, List]:
        """
        Creates a random profile following a daily consumption pattern and a scaling factor.

        This method generates a profile that simulates daily variations, applying a
        `scaling_factor` during a randomly determined "active" period of the day.

        Args:
            scaling_factor (float): The factor by which to scale values during the active period.
            horizon (int): The total number of time steps in the profile (e.g., 24 for hours).

        Returns:
            Dict[str, List]: A dictionary containing the generated thermal preferences profile
                             under the key "profile".
        """
        # Compute the timesteps per hour
        time_steps_per_hour = int(horizon / 24)

        # Create the start and stop positions for the ones
        rng = np.random.default_rng()  # Initialize the default random number generator
        start_morning = rng.integers(
            low=5 * time_steps_per_hour, high=9 * time_steps_per_hour
        )  # Choose a random start point
        stop_afternoon = rng.integers(
            low=17 * time_steps_per_hour, high=20 * time_steps_per_hour
        )  # Compute the stopping point

        # Create the profile of preferences by zone
        base_array = np.ones(horizon)  # Create one day of ones
        base_array[start_morning:stop_afternoon] = scaling_factor  # Create morning interval
        # Create one day of preferences and reapeat it over the horizon
        preference_value = rng.uniform(0, 0.2, 1)  # Random preference value
        thermal_preferences = np.around((preference_value * base_array), 5)  # Build one day of preferences per zone

        return {"profile": thermal_preferences.tolist()}

    def default_power_limit(self, power_limit: float, horizon: int) -> Dict[str, List]:
        """
        Creates a default power limit profile with specific limits during predefined daily windows.

        This method generates a power limit profile for a given `horizon`, applying a
        specified `power_limit` during early morning, middle of the day, and afternoon windows.
        The base power limit outside these windows is set to 25.0.

        Args:
            power_limit (float): The power limit to apply during the specified windows.
            horizon (int): The total number of time steps in the profile.

        Returns:
            Dict[str, List]: A dictionary containing a randomly chosen power limit profile
                             under the key "profile".
        """
        # Compute the timesteps per hour
        time_steps_per_hour = int(horizon / 24)

        # Define the windows in hours
        early_morning_start = 5 * time_steps_per_hour
        early_morning_end = 9 * time_steps_per_hour

        middle_of_day_start = 11 * time_steps_per_hour
        middle_of_day_end = 14 * time_steps_per_hour

        afternoon_start = 17 * time_steps_per_hour
        afternoon_end = 21 * time_steps_per_hour

        # Create the profile
        morning = np.full(horizon, 25.0)  # Initialize with 25
        noon = np.full(horizon, 25.0)  # Initialize with 25
        afternoon = np.full(horizon, 25.0)  # Initialize with 25

        morning[early_morning_start:early_morning_end] = power_limit  # Early morning window
        noon[middle_of_day_start:middle_of_day_end] = power_limit  # Middle of day window
        afternoon[afternoon_start:afternoon_end] = power_limit  # Late night window (part 1)
        gdp_alternatives = [morning.tolist(), noon.tolist(), afternoon.tolist()]

        return {"profile": random.choice(gdp_alternatives)}
