---
sidebar_position: 1
---

# API Module

The `api` package provides the core API endpoints for the system.

## Building Management

Endpoints for building-level data.

### Get Building Consumption

`GET /consumption`

Retrieves the total energy consumption of the building, averaged over a specified duration.

**Parameters**

| Name     | Type    | In   | Description                                          |
| -------- | ------- | ---- | ---------------------------------------------------- |
| duration | integer | query| Duration in seconds to compute the average consumption. Default: 60, Minimum: 10 |

**Responses**

| Status Code | Description                                       |
| ----------- | ------------------------------------------------- |
| 200         | Successful response with total consumption data.  |
| 400         | Bad request, if the duration is not an integer.   |
| 500         | Internal server error.                            |

### Get GRAP Values

`GET /grap`

Retrieves the Grid Response and Protection (GRAP) state and limit values.

**Responses**

| Status Code | Description                                 |
| ----------- | ------------------------------------------- |
| 200         | Successful response with GRAP values.       |
| 500         | Internal server error.                      |

## Device Management

Endpoints for device management.

### Adjust Device Setpoint

`POST /setpoint/{device_id}`

Adjusts the setpoint of a specific device.

**Parameters**

| Name      | Type    | In   | Description                |
| --------- | ------- | ---- | -------------------------- |
| device_id | string  | path | ID of the device.          |
| setpoint  | number  | query| The desired setpoint value.|

**Responses**

| Status Code | Description                                 |
| ----------- | ------------------------------------------- |
| 200         | Setpoint successfully applied.              |
| 404         | Device not found.                           |

### Schedule Device Dispatches

`POST /schedule/{priority}`

Schedules setpoint dispatches for multiple devices with a given priority.

**Parameters**

| Name     | Type    | In   | Description                                                                                             |
| -------- | ------- | ---- | ------------------------------------------------------------------------------------------------------- |
| priority | integer | path | Priority level (0-100). Higher values indicate higher priority.                                         |
| dispatches| object  | body | A dictionary of device IDs to a dictionary of datetime-setpoint pairs. See example in the original docstring. |

**Responses**

| Status Code | Description                                 |
| ----------- | ------------------------------------------- |
| 200         | Schedule saved successfully.                |
| 400         | Invalid priority value.                     |

### Get Device List

`GET /`

Retrieves the list of all controllable devices.

**Responses**

| Status Code | Description                                 |
| ----------- | ------------------------------------------- |
| 200         | Successful response with the list of devices.|
| 500         | Internal server error.                      |

### Get Device State

`GET /state/{device_id}`

Retrieves the current state of a specific device.

**Parameters**

| Name      | Type   | In   | Description                         |
| --------- | ------ | ---- | ----------------------------------- |
| device_id | string | path | ID of the device.                   |
| field     | string | query| Optional field of the state to read.|

**Responses**

| Status Code | Description                                 |
| ----------- | ------------------------------------------- |
| 200         | Successful response with the device state.  |
| 404         | Device not found.                           |

## Data Management

Endpoints for retrieving forecast, historic, and preferences data.

### Get Forecast Data

`GET /forecast/{forecast_type}`

Retrieves forecast data for non-controllable loads.

**Parameters**

| Name          | Type     | In   | Description                               |
| ------------- | -------- | ---- | ----------------------------------------- |
| forecast_type | string   | path | The type of forecast data to retrieve.    |
| start         | datetime | query| The start timestamp for the forecast data.|
| stop          | datetime | query| The stop timestamp for the forecast data. |

**Responses**

| Status Code | Description                                 |
| ----------- | ------------------------------------------- |
| 200         | Successful response with forecast data.     |
| 404         | Forecast type not found.                    |

### Get Historical Data

`GET /historic/{historic_type}`

Retrieves historical data for various device types.

**Parameters**

| Name          | Type     | In   | Description                                |
| ------------- | -------- | ---- | ------------------------------------------ |
| historic_type | string   | path | The type of historical data to retrieve.   |
| start         | datetime | query| The start timestamp for the historical data.|
| stop          | datetime | query| The stop timestamp for the historical data. |
| device_id     | string   | query| Device ID, if applicable.                  |

**Responses**

| Status Code | Description                                 |
| ----------- | ------------------------------------------- |
| 200         | Successful response with historical data.   |
| 400         | Bad request, if `device_id` is required but not provided. |
| 404         | Historical type not found.                  |

### Get Preferences Data

`GET /preferences/{preferences_type}`

Retrieves user preferences data.

**Parameters**

| Name                  | Type     | In   | Description                                  |
| --------------------- | -------- | ---- | -------------------------------------------- |
| preferences_type      | string   | path | The type of preferences data to retrieve.    |
| device_id             | string   | query| Device ID.                                   |
| start                 | datetime | query| Start timestamp.                             |
| stop                  | datetime | query| Stop timestamp.                              |
| sampling_in_minutes   | integer  | query| Sampling interval in minutes. Default: 10.   |

**Responses**

| Status Code | Description                                 |
| ----------- | ------------------------------------------- |
| 200         | Successful response with preferences data.  |
| 204         | No content found for the given parameters.  |
| 400         | Bad request (e.g., time range > 7 days).    |
| 404         | No data found for the given preferences type.|

### Get Weather Forecast Data

`GET /weather/forecast/{variable}`

Retrieves weather forecast data.

**Parameters**

| Name     | Type     | In   | Description                               |
| -------- | -------- | ---- | ----------------------------------------- |
| variable | string   | path | The weather variable to retrieve.         |
| start    | datetime | query| The start timestamp for the forecast data.|
| stop     | datetime | query| The stop timestamp for the forecast data. |

**Responses**

| Status Code | Description                                 |
| ----------- | ------------------------------------------- |
| 200         | Successful response with weather forecast data. |
| 400         | Bad request (e.g., start time in the past). |
| 500         | Internal server error.                      |

### Get Weather Historic Data

`GET /weather/historic/{variable}`

Retrieves weather historic data.

**Parameters**

| Name     | Type     | In   | Description                               |
| -------- | -------- | ---- | ----------------------------------------- |
| variable | string   | path | The weather variable to retrieve.         |
| start    | datetime | query| The start timestamp for the historic data.|
| stop     | datetime | query| The stop timestamp for the historic data. |

**Responses**

| Status Code | Description                                 |
| ----------- | ------------------------------------------- |
| 200         | Successful response with weather historic data. |
| 400         | Bad request (e.g., start time in the future). |
| 500         | Internal server error.                      |