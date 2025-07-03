"""
This module defines the `RedisDataInitializer` class, which is responsible for
initializing and uploading various user-specific data profiles to Redis.

It plays a crucial role in setting up the initial state of the system by
populating Redis with necessary data for different device types and user preferences,
utilizing `ProfileGenerators` for data creation and `DeviceHelper` for device-specific logic.
"""

from typing import List

import numpy as np

from common.database.redis import RedisClient
from common.util.logging import LoggingUtil
from initializers.device.device import DeviceHelper, DeviceType
from initializers.user.ProfileGenerators import ProfileGenerators


logger = LoggingUtil.get_logger(__name__)


class RedisDataInitializer:
    """
    Manages the initialization and upload of various user-specific data profiles to Redis.

    This class is responsible for populating Redis with default or generated data
    for different device types and user preferences, which are essential for
    the system's operation. It leverages `ProfileGenerators` for data creation
    and `DeviceHelper` for device-specific logic.
    """

    _redis_client: RedisClient

    def __init__(
        self,
        redis_client: RedisClient,
    ):
        """
        Initializes the RedisDataInitializer with a Redis client.

        Args:
            redis_client (RedisClient): An instance of RedisClient for interacting with Redis.
        """
        # Create self parameters
        self._redis_client = redis_client

        # Read labels
        self._labels_influx = redis_client.safe_read_from_redis("influxdb_mapping")
        self._labels_redis = redis_client.safe_read_from_redis("labels_redis")
        self._labels_market = redis_client.safe_read_from_redis("labels_market")

        # Create an instance of profile generators
        self._profile_generators = ProfileGenerators(redis_client)

    def initialize(
        self,
    ) -> None:
        """
        Orchestrates the upload of all required data profiles to Redis.

        This method retrieves user devices and then calls various private helper
        methods to upload thermal preferences, thermostat setpoints, electric storage
        preferences, EV (V1G and V2G) preferences, power limits, water heater
        preferences, trading preferences, and non-controllable loads.
        """

        # Retrieve devices from the redis database
        devices = self._redis_client.safe_read_from_redis("user_devices")

        self._upload_thermal_preferences_to_redis(devices)
        self._upload_thermostat_setpoints_to_redis(devices)
        self._upload_electric_storage_preferences_to_redis(devices)
        self._upload_v1g_preferences_to_redis(devices)
        self._upload_v2g_preferences_to_redis(devices)
        self._upload_power_limit_to_redis()
        self._upload_water_heater_preferences_to_redis()
        self._upload_trading_preferences_to_redis()
        self._upload_non_controlable_loads_default_to_redis()

    def _upload_thermal_preferences_to_redis(self, devices: List) -> None:
        """
        Uploads default thermal preferences for space heating devices to Redis.

        If space heating devices are present, this method generates random daily
        profiles for occupation preferences and saves them to Redis.

        Args:
            devices (List): A list of device dictionaries.
        """
        if DeviceHelper.has_device_type(devices, DeviceType.SPACE_HEATING):
            logger.info("Saving occupation preferences on RedisDB...")

            # Create the info to save
            devices = DeviceHelper.get_devices_of_type(devices, DeviceType.SPACE_HEATING)
            info_to_save = {}
            for device in devices:
                info_to_save[self._labels_influx["sh_occupation"]["field"] + device["entity_id"]] = (
                    self._profile_generators.random_daily_profile(
                        scaling_factor=0.05,
                        horizon=self._labels_market["dac_horizon"],
                    )["profile"]
                )

            # Save in redis the thermal preferences
            self._redis_client.save_in_redis(self._labels_redis["occupation"], info_to_save)

    def _upload_thermostat_setpoints_to_redis(self, devices: List) -> None:
        """
        Uploads default thermostat setpoints for space heating devices to Redis.

        If space heating devices are present, this method generates random integer
        profiles for thermostat setpoints (between 18 and 22) and saves them to Redis.

        Args:
            devices (List): A list of device dictionaries.
        """
        if DeviceHelper.has_device_type(devices, DeviceType.SPACE_HEATING):
            logger.info("Saving thermostat preferences on RedisDB...")

            # Create the info to save
            devices = DeviceHelper.get_devices_of_type(devices, DeviceType.SPACE_HEATING)
            info_to_save = {}
            for device in devices:
                info_to_save[self._labels_influx["sh_setpoint"]["field"] + device["entity_id"]] = (
                    self._profile_generators.random_profile_generator(18, 22, "integer")["profile"]
                )

            # Save in redis the setpoint preferences
            self._redis_client.save_in_redis(self._labels_redis["thermostat_setpoints"], info_to_save)

    def _upload_electric_storage_preferences_to_redis(self, devices: List) -> None:
        """
        Uploads electric storage preferences (desired SoC and charge preferences) to Redis.

        If electric storage devices are present, this method generates continuous random
        profiles for desired State of Charge (SoC) and charge preferences, based on
        the device's critical state, and saves them to Redis.

        Args:
            devices (List): A list of device dictionaries.
        """
        if DeviceHelper.has_device_type(devices, DeviceType.ELECTRIC_STORAGE):
            logger.info("Saving electric storage preferences on RedisDB...")

            # Extract information of the minimin soc from the information that arrived from redis
            for device in devices:
                if device["type"] == DeviceType.ELECTRIC_STORAGE.value:
                    min_residual_energy = device["critical_state"] / 100

            # Save on redisDB the desired SoC
            info_to_save = self._profile_generators.random_profile_generator(min_residual_energy, 1, "continuous")
            self._redis_client.save_in_redis(self._labels_redis["es_desired_soc"], info_to_save)

            # Save on redisDB the charge preferences
            info_to_save = self._profile_generators.random_profile_generator(min_residual_energy, 1, "continuous")
            self._redis_client.save_in_redis(self._labels_redis["es_charge_preferences"], info_to_save)

    def _upload_v1g_preferences_to_redis(self, devices: List) -> None:
        """
        Uploads V1G (Electric Vehicle V1G) preferences to Redis.

        If V1G devices are present, this method generates random profiles for
        V1G branched status, desired SoC, and consumption, then saves them to Redis.

        Args:
            devices (List): A list of device dictionaries.
        """
        if DeviceHelper.has_device_type(devices, DeviceType.ELECTRIC_VEHICLE_V1G):
            logger.info("Saving V1G preferences on RedisDB...")
            # Extract information of the minimin soc from the information that arrived from redis
            for device in devices:
                if device["type"] == DeviceType.ELECTRIC_VEHICLE_V1G.value:
                    min_residual_energy = device["min_residual_energy"] / 100

            # Save V1G branched
            info_to_save = self._profile_generators.random_profile_generator(0, 2, "integer")
            self._redis_client.save_in_redis(self._labels_redis["v1g_branched"], info_to_save)

            # Save V1G desired SOC
            info_to_save = self._profile_generators.random_profile_generator(min_residual_energy, 1, "continuous")
            self._redis_client.save_in_redis(self._labels_redis["v1g_desired_soc"], info_to_save)

            # Save V1G consumption
            info_to_save = self._profile_generators.generate_ev_default_consumption()
            self._redis_client.save_in_redis(self._labels_redis["v1g_consumption"], info_to_save)

    def _upload_v2g_preferences_to_redis(self, devices: List) -> None:
        """
        Uploads V2G (Electric Vehicle V2G) preferences to Redis.

        If V2G devices are present, this method generates random profiles for
        V2G branched status, desired SoC, and consumption, then saves them to Redis.

        Args:
            devices (List): A list of device dictionaries.
        """
        if DeviceHelper.has_device_type(devices, DeviceType.ELECTRIC_VEHICLE_V2G):
            logger.info("Saving thermostat setpoints on RedisDB...")
            # Extract information of the minimin soc from the information that arrived from redis
            for device in devices:
                if device["type"] == DeviceType.ELECTRIC_VEHICLE_V2G.value:
                    min_residual_energy = device["min_residual_energy"] / 100

            # Save on redisDB
            # Save V2G branched
            info_to_save = self._profile_generators.random_profile_generator(0, 2, "integer")
            self._redis_client.save_in_redis(self._labels_redis["v2g_branched"], info_to_save)

            # Save V2G desired SOC
            info_to_save = self._profile_generators.random_profile_generator(min_residual_energy, 1, "continuous")
            self._redis_client.save_in_redis(self._labels_redis["v2g_desired_soc"], info_to_save)

            # Save V2G consumption
            info_to_save = self._profile_generators.generate_ev_default_consumption()
            self._redis_client.save_in_redis(self._labels_redis["v2g_consumption"], info_to_save)

    def _upload_power_limit_to_redis(self) -> None:
        """
        Uploads a default power limit profile to Redis.

        This method generates a power limit profile using `default_power_limit`
        from `ProfileGenerators` and saves it to Redis under the "power_limit" key.
        """
        logger.info("Saving power limit on RedisDB...")

        # Create the info to save
        info_to_save = {}
        power_limit_gdp = 12.5
        info_to_save[self._labels_redis["power_limit"]] = self._profile_generators.default_power_limit(
            power_limit=power_limit_gdp,
            horizon=self._labels_market["dac_horizon"],
        )["profile"]

        # Save in redis the power limit
        self._redis_client.save_in_redis(self._labels_redis["power_limit"], info_to_save)

    def _upload_water_heater_preferences_to_redis(self) -> None:
        """
        Uploads water heater preferences (state) to Redis.

        This method generates a random integer profile for the water heater state
        (0 or 1) and saves it to Redis.
        """
        logger.info("Saving water heater preferences on RedisDB...")

        # Save on redisDB
        info_to_save = self._profile_generators.random_profile_generator(0, 1, "integer")
        self._redis_client.save_in_redis(self._labels_redis["wh_state"], info_to_save)

    def _upload_trading_preferences_to_redis(self) -> None:
        """
        Uploads trading preferences to Redis.

        This method generates a random continuous profile for trading preferences
        (between 0 and 1) and saves it to Redis.
        """
        logger.info("Saving trading preferences on RedisDB...")

        # Save on redisDB
        info_to_save = self._profile_generators.random_profile_generator(0, 1, "continuous")
        self._redis_client.save_in_redis(self._labels_redis["trading_preferences"], info_to_save)

    def _upload_non_controlable_loads_default_to_redis(self) -> None:
        """
        Uploads a default profile for non-controllable loads to Redis.

        This method generates random normal data for non-controllable loads
        based on a random mean and standard deviation, and saves it to Redis.
        """
        # Create a random number generator
        rng = np.random.default_rng()

        # Generate dummy data for the non controllable loads
        mean_ncl = rng.uniform(3, 10)
        std_ncl = rng.uniform(1, 5)
        ncl_array = self._profile_generators.generate_random_normal_data(
            mean_ncl, std_ncl, self._labels_market["dac_horizon"]
        )

        # Save on redisDB
        info_to_save = {"profile": ncl_array.tolist()}
        self._redis_client.save_in_redis(self._labels_redis["non_controllable_loads"], info_to_save)
