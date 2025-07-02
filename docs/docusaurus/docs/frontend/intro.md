---
sidebar_position: 1
---

# Frontend

This package implements the frontend web application for the building intelligence system. It provides a user interface for monitoring and controlling various smart home devices.

The application is built using the FastAPI framework and includes the following key components:

- **app.py**: The main entry point of the FastAPI application. It defines all the API endpoints for device management, power control, and Model Predictive Control (MPC) calculations. It also serves the static web pages.

- **database**: A subpackage containing database-related utilities.
  - `redis_yaml_saver`: A tool for loading device configurations from YAML files into a Redis database.

- **static**: A directory containing all the static assets for the web interface, including:
  - `styles.css`: Cascading Style Sheets for styling the HTML pages.
  - `scripts.js`: JavaScript for interactive UI elements and client-side logic.
  - `smart-home.jpg`: An image file used in the web interface.

- **templates**: A directory containing Jinja2 HTML templates that are rendered by the FastAPI application to generate the web pages:
  - `index.html`: The main landing page of the application.
  - `priorities.html`: A page for managing device priorities.
  - `coordinator.html`: A page for the Grid Coordinator interface.
  - `mpc.html`: A page for triggering and viewing MPC calculations.