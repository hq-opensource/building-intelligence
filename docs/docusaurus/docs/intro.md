---
sidebar_position: 1
---

# Building Intelligence

[![License](https://img.shields.io/badge/License-LiLiQ_P-blue.svg)](https://github.com/hq-opensource/building-intelligence/blob/main/LICENSE.md)
[![Contributing](https://img.shields.io/badge/Contributing-Guidelines-green.svg)](https://github.com/hq-opensource/building-intelligence/blob/main/CONTRIBUTING.md)

Welcome to the Building Intelligence project! This documentation provides a comprehensive overview of the architecture, components, and functionalities of this innovative platform for smart building energy management.

## What is Building Intelligence?


**Building Intelligence** is an open-source platform designed to simplify the interaction between building devices and third-party applications, empowering developers to create advanced energy management solutions. Building Intelligence focuses specifically on the **building intelligence** layer, making utility-scale complex energy optimization scenarios accessible and manageable.

Building Intelligence's core mission is to make it easier for power utilities to develop custom grid services. By handling the ingestion, processing, and storage of data from building actuators, Building Intelligence streamlines development and ensures seamless interaction with both local and cloud-based systems. Additionally, it greatly simplifies the test and development of new grid services to optimize energy efficiency or participate in demand response utility programs.

## System Architecture
![Building Intelligence Diagram](/img/hems.png)


The architecture of the Building Intelligence platform is modular, consisting of three primary layers: **Smart Devices**, **Building Intelligence**, and **Grid Services**. This design separates the device-level communication, data management, and high-level control logic, creating a flexible and scalable system.

### Smart Devices

This layer represents the physical hardware and communication protocols at the building level. It is responsible for interfacing with various smart devices and sensors.

-   **Communication Protocols**: The platform supports standard industry protocols like **Modbus**, **Bacnet**, and **Zigbee** to ensure broad compatibility with a wide range of devices.
-   **Event Broker**: A local event broker is used to decouple the communication between the physical devices and the higher-level interfaces.
-   **Interfaces**:
    -   **Telegraf**: An open-source agent for collecting and reporting metrics and data. It is primarily used for data ingestion from various sources.
    -   **Home Assistant Interface**: This component provides a two-way communication link with devices integrated through the Home Assistant platform, allowing for both data collection and control signal actuation.

### Building Intelligence

This is the core middleware of the platform, acting as the central hub for data processing, storage, and communication.

-   **Databases (DBs)**: The platform uses a combination of **InfluxDB** for storing time-series data and **Redis** for caching and real-time messaging, ensuring both performance and scalability.
-   **Data Engine**: This is the "brains" of the data processing operations. It includes modules for:
    -   **Telemetry**: Collecting and processing data from the smart devices.
    -   **Forecasters**: Using machine learning models to predict future energy consumption and generation.
    -   **Learners**: Continuously improving the models based on new data.
-   **Initializer**: This component is responsible for setting up the initial system configuration, including default user preferences, which are stored in the databases.
-   **Event Broker**: A central message bus that facilitates communication between the various internal components of the Building Intelligence layer.
-   **Core API (REST)**: A RESTful API that exposes the platform's data and functionalities to the **Grid Services** layer. This is the primary integration point for external control logic.
-   **Grid Services API & Frontend**: These components provide the user interface of the platform. The **Frontend** allows users to monitor their devices, set preferences, and visualize data. It communicates with the backend through the **Grid Services API**.

### Grid Services

This layer contains the high-level optimization and control logic. These services are external to the Building Intelligence platform and interact with it through the **Core API**. This separation allows for the development and deployment of various control strategies without modifying the core platform.

The diagram shows several examples of Grid Services, some of which are already developed (in green) and others that are on the roadmap (in yellow):

-   **Developed by the LTE**:
    -   `CLPU - Reactive`
    -   `CLPU - Predictive (MPC+RTC)`
    -   `Dynamic Tariffs (MPC)`
-   **On the Roadmap**:
    -   `MPC for Commercial and Institutional buildings`
    -   `Demand Coordination`
    -   `AI Energy Assistant`
    -   `Energy Efficiency`

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

## Data and Control Flow

The platform operates through a continuous and cyclical flow of data and control signals, ensuring a responsive and intelligent energy management system.

### Data Flow (Southbound to Northbound)

1.  **Device Communication**: **Smart Devices** communicate using their native protocols (Modbus, Bacnet, Zigbee). This communication is captured by a local **Event Broker**.
2.  **Data Collection**: The **Telegraf** and **Home Assistant Interface** components subscribe to the device-level event broker.
3.  **Data Ingestion**:
    *   **Telegraf** sends the collected time-series data directly to the **Databases (InfluxDB)**.
    *   The **Home Assistant Interface** forwards device data to the central **Event Broker** within the Building Intelligence layer.
4.  **Data Processing**: The **Data Engine** subscribes to the central event broker, processes the incoming data, performs forecasting and learning, and stores the results and raw data in the **Databases (InfluxDB and Redis)**.
5.  **API Exposure**: The **Core API** provides a RESTful interface to the data stored in the databases, making it available to the **Grid Services**.

### Control Flow (Northbound to Southbound)

1.  **Optimization**: The **Grid Services** retrieve data from the **Core API**, execute their optimization algorithms (e.g., MPC, CLPU), and generate control signals.
2.  **Command Transmission**: These control signals are sent back to the **Core API**.
3.  **Internal Routing**: The **Core API** publishes the control commands to the central **Event Broker**.
4.  **Device Actuation**: The **Home Assistant Interface** subscribes to these commands from the event broker and sends them to the appropriate **Smart Devices** through the device-level event broker and communication protocols.

### User Interaction

-   The **Frontend**, through the **Grid Services API**, allows users to view data, monitor device status, and set preferences. These preferences are saved via the **Initializer** and can be accessed by the **Grid Services** through the **Core API** to tailor the control logic to the user's needs.

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
