from enum import Enum


class HistoricType(Enum):
    """Types of historics."""

    TZ_TEMPERATURE = "tz-temperature"
    TZ_HISTORIC_SETPOINT = "tz-historic-setpoint"
    TZ_ELECTRIC_CONSUMPTION = "tz-electric-consumption"
    NON_CONTROLLABLE_LOADS = "non-controllable-loads"
    VEHICLE_CONSUMPTION = "vehicle-consumption"


class ForecastType(Enum):
    """Types of forecasts."""

    NON_CONTROLLABLE_LOADS = "non-controllable-loads"


class PreferencesType(Enum):
    """Types of preferences."""

    TZ_SETPOINT_PREFERENCES = "setpoint-preferences"
    TZ_OCCUPANCY_PREFERENCES = "occupancy_preferences"
    ELECTRIC_BATTERY_SOC_PREFERENCES = "electric-battery-soc-preferences"
    VEHICLE_BRANCHED_PREFERENCES = "vehicle-branched-preferences"
    VEHICLE_SOC_PREFERENCES = "vehicle-soc-preferences"
    WATER_HEATER_CONSUMPTION_PREFERENCES = "water-heater-consumption-preferences"


class WeatherForecastType(Enum):
    """Weather variables."""

    CLOUD_BASE = "cloudBase"
    CLOUD_CEILING = "cloudCeiling"
    CLOUD_COVER = "cloudCover"
    DEW_POINT = "dewPoint"
    EVAPO_TRANSPIRATION = "evapotranspiration"
    FREEZING_RAIN_INTENSITY = "freezingRainIntensity"
    HUMIDITY = "humidity"
    ICE_ACCUMULATION = "iceAccumulation"
    ICE_ACCUMULATION_LWE = "iceAccumulationLwe"
    PRECIPITATION_PROBABILITY = "precipitationProbability"
    PRESSURE_SEA_LEVEL = "pressureSeaLevel"
    PRESSURE_SURFACE_LEVEL = "pressureSurfaceLevel"
    RAIN_ACCUMULATION = "rainAccumulation"
    RAIN_INTENSITY = "rainIntensity"
    SLEET_ACCUMULATION = "sleetAccumulation"
    SLEET_ACCUMULATION_LWE = "sleetAccumulationLwe"
    SLEET_INTENSITY = "sleetIntensity"
    SNOW_ACCUMULATION = "snowAccumulation"
    SNOW_ACCUMULATION_LWE = "snowAccumulationLwe"
    SNOW_DEPTH = "snowDepth"
    SNOW_INTENSITY = "snowIntensity"
    TEMPERATURE = "temperature"
    TEMPERATURE_APPARENT = "temperatureApparent"
    UV_HEALTH_CONCERN = "uvHealtConcern"
    UV_INDEX = "uvIndex"
    VISIBILITY = "visibility"
    WEATHER_CODE = "weatherCode"
    WIND_DIRECTION = "windDirection"
    WIND_GUST = "windGust"
    WIND_SPEED = "windSpeed"


class WeatherHistoricType(Enum):
    """Weather variables."""

    CLOUD_BASE = "cloudBase"
    CLOUD_CEILING = "cloudCeiling"
    CLOUD_COVER = "cloudCover"
    DEW_POINT = "dewPoint"
    FREEZING_RAIN_INTENSITY = "freezingRainIntensity"
    HUMIDITY = "humidity"
    PRECIPITATION_PROBABILITY = "precipitationProbability"
    PRESSURE_SEA_LEVEL = "pressureSeaLevel"
    PRESSURE_SURFACE_LEVEL = "pressureSurfaceLevel"
    RAIN_INTENSITY = "rainIntensity"
    SLEET_INTENSITY = "sleetIntensity"
    SNOW_INTENSITY = "snowIntensity"
    TEMPERATURE = "temperature"
    TEMPERATURE_APPARENT = "temperatureApparent"
    UV_HEALTH_CONCERN = "uvHealtConcern"
    UV_INDEX = "uvIndex"
    VISIBILITY = "visibility"
    WEATHER_CODE = "weatherCode"
    WIND_DIRECTION = "windDirection"
    WIND_GUST = "windGust"
    WIND_SPEED = "windSpeed"
