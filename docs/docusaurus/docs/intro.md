---
sidebar_position: 1
---

# Building Intelligence

[![License](https://img.shields.io/badge/License-LiLiQ_P-blue.svg)](https://github.com/hq-opensource/building-intelligence/blob/main/LICENSE.md)
[![Contributing](https://img.shields.io/badge/Contributing-Guidelines-green.svg)](https://github.com/hq-opensource/building-intelligence/blob/main/CONTRIBUTING.md)

Welcome to the Building Intelligence project! This documentation provides a comprehensive overview of the architecture, components, and functionalities of this innovative platform for smart building energy management.

## What is Building Intelligence?

![Building Intelligence Diagram](/img/hems.png)

**Building Intelligence** is an open-source platform designed to simplify the interaction between building devices and third-party applications, empowering developers to create advanced energy management solutions. Building Intelligence focuses specifically on the **building intelligence** layer, making utility-scale complex energy optimization scenarios accessible and manageable.

Building Intelligence's core mission is to make it easier for power utilities to develop custom grid services. By handling the ingestion, processing, and storage of data from building actuators, Building Intelligence streamlines development and ensures seamless interaction with both local and cloud-based systems. Additionally, it greatly simplifies the test and development of new grid services to optimize energy efficiency or participate in demand response utility programs.

Building Intelligence acts as a bridge between three different cloud and edge entities:
- **Utility coordinators:** The utility coordinators are cloud entities that could be deployed in a centralized or distributed manner throughout the grid. The utility coordinators are the ones that activate the grid services.
- **Building controllers:** The building controllers refer to systems that gather information about their state and allow control.
- **Grid services:** Third-party applications that enable advanced energy optimization.

## Features

- **Data Management:**  
  Building Intelligence ingests data from building actuators and stores it in robust databases, including:  
  - **InfluxDB** for time-series data.  
  - **Redis** for fast, in-memory storage.  

- **Grid Services Integration:**  
  Building Intelligence enables the deployment and activation of **grid services**, such as:  
  - Energy efficiency optimization.  
  - Dynamic tariff optimization.  
  - Ancillary services for grid stability.  

- **Northbound Cloud Connectivity:**  
  Building Intelligence integrates with cloud systems, allowing users and external systems to activate and manage grid services remotely.

- **Southbound Connections:**  
  Building Intelligence communicates directly with building devices or building control systems, ensuring reliable data ingestion and control.  

- **API for Developers:**  
  Developers can build and deploy custom grid services using Building Intelligence’s core API, making the development of custom grid services accessible to all.

## Use Cases

- **Energy Efficiency:** Automate the reduction of energy waste in buildings.  
- **Demand Response:** React dynamically to grid signals to reduce peak demand.  
- **Dynamic Tariff Optimization:** Adjust energy consumption patterns to benefit from real-time tariff changes.  
- **Ancillary Services:** Support grid stability with advanced control strategies.  
- **Many others:** Building Intelligence allows the development of custom grid services by interacting with a simple API. Thus, many other control algorithms could be easily integrated on Building Intelligence.

## Core Packages

The project is organized into several key packages, each with a specific responsibility:

*   **Common (`common`)**: This package contains the foundational building blocks of the system. It provides shared utilities for database interactions (with InfluxDB for time-series data and Redis for caching and messaging), standardized device definitions, and consistent logging mechanisms. This ensures code reusability and maintainability across the entire platform.

*   **Core API (`core-api`)**: The central nervous system of the platform. Built with FastAPI, it exposes a comprehensive set of API endpoints for managing building data, controlling devices, scheduling operations, and retrieving both historical and forecasted data.

*   **Data Engine (`data-engine`)**: The intelligence hub of the project. This powerful component is responsible for the heavy lifting of data processing, time-series forecasting using advanced models like Prophet, and handling critical grid events such as blackouts through its Grid Response and Protection (GRAP) module.

*   **Frontend (`frontend`)**: The user-facing component of the platform. It is a web application, also built with FastAPI and Jinja2 templates, that provides an intuitive interface for users to monitor their devices, set their preferences, and visualize the results of the energy optimization.

*   **Grid Services API (`grid-services-api`)**: This service acts as a bridge to the wider electricity grid. It exposes endpoints for participating in various grid programs, such as day-ahead energy markets, direct load control, and other demand response initiatives.

*   **Home Assistant Device Interface (`ha-device-interface`)**: To ensure broad compatibility, this service provides a seamless interface for interacting with a wide range of smart home devices, particularly those integrated with the popular Home Assistant platform.

*   **Initializers (`initializers`)**: This package is responsible for the initial setup and configuration of the entire system. It ensures that databases are correctly structured, device configurations are loaded, and user profiles are created, providing a smooth and reliable startup process.

## How Does It Work?

The Building Intelligence platform operates on a continuous loop of data collection, analysis, and action:

1.  **Data Acquisition**: The system continuously collects data from a variety of sources, including smart meters, sensors, and connected devices. This data is stored in a time-series database (InfluxDB) for historical analysis.

2.  **Forecasting and Prediction**: The `data-engine` uses historical data and machine learning models to forecast future energy consumption and generation. This allows the system to anticipate future conditions and plan accordingly.

3.  **Optimization and Scheduling**: Based on the forecasts, user preferences, and grid signals, the system's optimization algorithms create optimal schedules for the operation of controllable devices like HVAC systems, water heaters, electric vehicle chargers, and battery storage systems.

4.  **Control and Actuation**: The schedules are then executed by the `core-api` and `ha-device-interface`, which send control signals to the respective devices, adjusting their operation to achieve the desired energy profile.

5.  **User Interaction**: Throughout this process, users can monitor the system's performance, override schedules, and set their own preferences through the `frontend` application.

## Getting Started

### Installation

#### Requirements:
- Python 3.11+
- Docker (recommended for quick setup)
- `docker-compose` for orchestrating services.

#### Steps:
1. Clone the Repository:
   ```bash
   git clone https://github.com/hq-opensource/building-intelligence.git
   ```

2. Setup Configuration:

    Create the required configuration files. Each configuration file contains an example:
    - **docker.env** : Contains the various environment variables needed by the system.
    - **devices.yaml** : Contains the devices and their specifications.

3. Start Building Intelligence with Docker Compose:
    ```bash
    docker-compose --env-file docker.env up
    ```

## API Documentation
Building Intelligence offers a RESTful API to interact with building devices and activate grid services. Once the system is deployed, the API documentation is available at:
http://localhost:8000/docs (Swagger UI).

By following this documentation, you will gain a deeper understanding of each component and learn how to contribute to this exciting project. Whether you are a developer, a researcher, or simply an enthusiast of smart energy solutions, we welcome you to the Building Intelligence community.
