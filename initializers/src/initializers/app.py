import os

from pathlib import Path

from common.database.redis import RedisClient
from common.util.logging import LoggingUtil
from initializers.database.influx_init import InfluxInit
from initializers.database.redis_yaml_saver import RedisYAMLSaver
from initializers.user.redis_data_initializer import RedisDataInitializer


logger = LoggingUtil.get_logger(__name__)


def main() -> None:
    logger.info("Starting the user initialization process...")
    # Create the redis client
    redis_password = str(os.getenv("REDIS_PASSWORD"))
    redis_host = str(os.getenv("REDIS_HOST"))
    redis_port = int(os.getenv("REDIS_PORT", "6379"))

    redis_client = RedisClient(redis_host, redis_port, redis_password)

    # Create redis yaml saver
    redis_yaml_saver = RedisYAMLSaver(redis_client)

    # Save all labels on RedisDB
    folder_labels = os.path.join(os.path.dirname(os.path.realpath(__file__)), "labels_dbs_config")
    redis_yaml_saver.upload_yaml_files_to_redis(folder_labels)

    # Save user devices in RedisDB
    devices_config_file = str(os.getenv("DEVICES_CONFIG_FILE", ""))
    if devices_config_file:
        redis_yaml_saver.upload_yaml_file_to_redis(Path(devices_config_file), "user_devices")
    else:
        logger.error("No devices config file provided")
        raise ValueError("No devices config file provided")

    # Save InfluxDB data mapping in RedisDB
    influxdb_mapping_file = str(os.getenv("INFLUXDB_MAPPING_FILE", ""))
    if influxdb_mapping_file:
        redis_yaml_saver.upload_yaml_file_to_redis(Path(influxdb_mapping_file), "influxdb_mapping")
    else:
        logger.error("No InfluxDB mapping file provided")
        raise ValueError("No InfluxDB mapping file provided")

    # Save grid functions information
    folder_grid_functions = os.path.join(os.path.dirname(os.path.realpath(__file__)), "grid_functions_config")
    redis_yaml_saver.upload_yaml_files_to_redis(folder_grid_functions)

    # Create the user initializer
    redis_initializer = RedisDataInitializer(redis_client)
    redis_initializer.initialize()

    # Create the influx buckets
    influxdb_url = str(os.getenv("INFLUXDB_URL"))
    influxdb_org = str(os.getenv("INFLUXDB_ORG"))
    influxdb_token = str(os.getenv("INFLUXDB_TOKEN"))
    influx_init = InfluxInit(influxdb_url, influxdb_org, influxdb_token, redis_client)
    influx_init.create_simulation_buckets_for_influx()

    logger.info("Finish!")


if __name__ == "__main__":
    main()
