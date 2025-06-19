# Building Intelligence

[![License](https://img.shields.io/badge/License-LiLiQ_P-blue.svg)](LICENSE.md)
[![Contributing](https://img.shields.io/badge/Contributing-Guidelines-green.svg)](CONTRIBUTING.md)

**Building Intelligence** is an open-source platform designed to simplify the interaction between building devices and third-party applications, empowering developers to create advanced energy management solutions. Building Intelligence focuses specifically on the **building intelligence** layer, making utility scale complex energy optimization scenarios accessible and manageable.  

---

## 🌟 **What is Building Intelligence?**

Building Intelligence core mission is to make it easier for power utilities to develop custom grid services. By handling the ingestion, processing, and storage of data from building actuators, Building Intelligence streamlines development and ensures seamless interaction with both local and cloud-based systems.
Additionally, it greatly simplifies the test and development of new grid services to optimize energy efficiency or participate on demand response utility programs. 

Building Intelligence acts as a bridge between three different cloud and edge entities:
- **Utility coordinators:** The utility coordinators are cloud entities that could be deployed in a centralized or distributed manner trought the grid. The utility coordinators are the ones that activate the grid services. 
- **Building controllers:** The buiding controllers refer to systems that . The building actuators gather information about their state and allow 
- **Grid services:** Third-party applications that enable advanced energy optimization.

---

## 🚀 **Features**

- **Data Management:**  
  Building Intelligence ingests data from building actuators and stores it in robust databases, including:  
  - **InfluxDB** for time-series data.  
  - **Redis** for fast, in-memory storage.  
  - **GraphDB** for structured relationships between devices and services.

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
  Developers can build and deploy custom grid services using Building Intelligence’s core API, making the development of custom grid services accesible to all.


---

## 🌐 **Use Cases**

- **Energy Efficiency:** Automate the reduction of energy waste in buildings.  
- **Demand Response:** React dynamically to grid signals to reduce peak demand.  
- **Dynamic Tariff Optimization:** Adjust energy consumption patterns to benefit from real-time tariff changes.  
- **Ancillary Services:** Support grid stability with advanced control strategies.  
- **Many others:** Building Intelligence allows the development of custom grid services by interacting with a simple API. Thus, many other control algorithms could be easily integrated on Building Intelligence. 
---

## 🛠️ **Getting Started**

### **Installation**

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
    - **influxdb_mapping.yaml** : Contains the data mapping structure in InfluxDB.
    - **devices.yaml** : Contains the devices and their specifications.

    Our Influx cloud instance is free to use. Contact us if you want to use our instances, but, read the [contributor license agreement](CONTRIBUTOR_LICENSE_AGREEMENT.md) file first. 

3. Start Building Intelligence with Docker Compose:
    ```bash
    docker-compose --env-file docker.env up
    ```

## API Documentation
Building Intelligence offers a RESTful API to interact with building devices and activate grid services. Once the system is deployed, the API documentation is available at:
http://localhost:8000/docs (Swagger UI).

## 📖 Contributing
See how to contribute to Building Intelligence [here](CONTRIBUTING.md).

## 📜 License
See the license of Building Intelligence [here](LICENSE.md).

