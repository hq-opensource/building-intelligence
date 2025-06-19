import logging
import os
import time

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import yaml

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from common.database.redis import RedisClient
from frontend.database.redis_yaml_saver import RedisYAMLSaver


# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()
app.mount("/static", StaticFiles(directory="src/frontend/static"), name="static")

templates = Jinja2Templates(directory="src/frontend/templates")

JSON_CONTENT_TYPE = "application/json"

# Cache mémoire pour stocker la dernière valeur de `power_limit`
power_limit_cache = {"value": None}


class MpcRequest(BaseModel):
    space_heating: bool
    electric_storage: bool
    electric_vehicle: bool
    water_heater: bool
    prices: Dict[datetime, float]
    power_limit: Dict[datetime, float]
    interval: int
    start: datetime
    stop: datetime


class Device(BaseModel):
    type: str
    entity_id: str
    description: str
    friendly_name: str
    manufacturer: Optional[str] = Field(None, description="Manufacturer of the device")
    model: Optional[str] = Field(None, description="Model of the device")
    group: str
    priority: int
    critical_state: float
    desired_state: float
    power_capacity: float
    critical_action: float
    activation_action: float
    deactivation_action: float
    modulation_capability: Optional[bool] = Field(None, description="Modulation capability")
    discharge_capability: Optional[bool] = Field(None, description="Discharge capability")
    discharge_action: Optional[float] = Field(None, description="Discharge action")
    preferences_soc: Optional[Dict] = Field(None, description="State of Charge preferences")
    preferences_occupancy: Optional[Dict] = Field(None, description="Occupancy preferences")
    preferences_setpoint: Optional[Dict] = Field(None, description="Setpoint preferences")
    preferences_branched: Optional[Dict] = Field(None, description="EV charging status preferences")


class PowerLimit(BaseModel):
    limit: float


def update_user_devices_on_redis() -> None:
    # Create the redis client
    redis_password = str(os.getenv("REDIS_PASSWORD"))
    redis_host = str(os.getenv("REDIS_HOST"))
    redis_port = int(os.getenv("REDIS_PORT", "6379"))

    redis_client = RedisClient(redis_host, redis_port, redis_password)

    # Create redis yaml saver
    redis_yaml_saver = RedisYAMLSaver(redis_client)

    # Save user devices in RedisDB
    devices_config_file = str(os.getenv("DEVICES_CONFIG_FILE", ""))
    if devices_config_file:
        redis_yaml_saver.upload_yaml_file_to_redis(Path(devices_config_file), "user_devices")
    else:
        logger.error("No devices config file provided")
        raise ValueError("No devices config file provided")


@app.get("/devices", response_model=List[Device])
def get_devices() -> List[Device]:
    try:
        devices_config_file = str(os.getenv("DEVICES_CONFIG_FILE", ""))
        with open(devices_config_file, "r") as file:
            devices = yaml.safe_load(file)
            validated_devices = [Device(**device) for device in devices]
        return validated_devices
    except Exception as e:
        logger.error("Error reading devices.yaml: %s", e)
        raise HTTPException(status_code=500, detail="Error reading devices.yaml") from e


@app.post("/devices")
def update_devices(devices: List[Device]) -> dict:
    try:
        devices_config_file = str(os.getenv("DEVICES_CONFIG_FILE", ""))
        with open(devices_config_file, "w") as file:
            # Custom YAML dumper to keep friendly_name as the first parameter
            class CustomDumper(yaml.Dumper):
                def increase_indent(self, flow: bool = False, indentless: bool = False) -> None:
                    return super(CustomDumper, self).increase_indent(flow, False)

            def dict_representer(dumper: yaml.Dumper, data: dict) -> yaml.nodes.MappingNode:
                # Reorder the dictionary to have friendly_name as the first key
                ordered_data = {k: data[k] for k in ["friendly_name", "entity_id", "group"] if k in data}
                ordered_data.update({k: data[k] for k in data if k not in ordered_data})
                return dumper.represent_dict(ordered_data.items())

            yaml.add_representer(dict, dict_representer, Dumper=CustomDumper)

            formatted_devices = [device.model_dump() for device in devices]
            yaml.dump(formatted_devices, file, Dumper=CustomDumper, default_flow_style=False, sort_keys=False)
            time.sleep(0.5)
            update_user_devices_on_redis()
        return {"message": "Devices updated successfully"}
    except Exception as e:
        logger.error("Error writing to devices.yaml: %s", e)
        raise HTTPException(status_code=500, detail="Error writing to devices.yaml") from e


@app.get("/get-power-limit")
def get_power_limit() -> dict:
    """Récupère la valeur actuelle de la limite de puissance."""
    current_value = power_limit_cache["value"]
    return {"power_limit": current_value}


@app.post("/set-power-limit")
def set_power_limit(power_limit: PowerLimit) -> Any:
    grid_services_url = os.getenv("GRID_SERVICES_API_URL")
    url = f"{grid_services_url}/direct_control/power_limit"

    headers = {
        "accept": JSON_CONTENT_TYPE,
        "Content-Type": JSON_CONTENT_TYPE,
    }

    data = {
        "limit": power_limit.limit,
    }

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()


@app.post("/stop-power-limit")
def stop_power_limit() -> Any:
    grid_services_url = os.getenv("GRID_SERVICES_API_URL")
    url = f"{grid_services_url}/direct_control/power_limit"

    headers = {
        "accept": JSON_CONTENT_TYPE,
    }

    response = requests.post(url, headers=headers)
    response.raise_for_status()
    return response.json()


@app.post("/calculate_mpc")
def calculate_mpc(request: MpcRequest) -> Any:
    grid_services_url = os.getenv("GRID_SERVICES_API_URL")
    url = f"{grid_services_url}/mpc/calculate_mpc"

    headers = {
        "accept": JSON_CONTENT_TYPE,
        "Content-Type": JSON_CONTENT_TYPE,
    }

    data = {
        "space_heating": request.space_heating,
        "electric_storage": request.electric_storage,
        "electric_vehicle": request.electric_vehicle,
        "water_heater": request.water_heater,
        "prices": {k.astimezone().isoformat(): v for k, v in request.prices.items()},
        "power_limit": {k.astimezone().isoformat(): v for k, v in request.power_limit.items()},
        "start": request.start.astimezone().isoformat(),
        "stop": request.stop.astimezone().isoformat(),
        "interval": request.interval,
    }

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


# Page des priorités
@app.get("/priorities", response_class=HTMLResponse)
async def priorities_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("priorities.html", {"request": request})


# Page Grid Coordinator
@app.get("/coordinator", response_class=HTMLResponse)
async def coordinator_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("coordinator.html", {"request": request})


# Page MPC
@app.get("/mpc", response_class=HTMLResponse)
async def mpc_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("mpc.html", {"request": request})


if __name__ == "__main__":
    import uvicorn

    frontend_port = int(os.getenv("FRONTEND_PORT", 8200))
    uvicorn.run(app, host="0.0.0.0", port=frontend_port)
