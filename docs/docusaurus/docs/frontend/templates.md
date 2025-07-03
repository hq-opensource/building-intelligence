---
sidebar_position: 4
---

# HTML Templates

The `templates` directory contains Jinja2 HTML templates that are rendered by the FastAPI application to generate the web pages.

## `index.html`

The main landing page of the application. It provides navigation to the other sections of the site, including "Device Prioritization" and "Power Management".

## `priorities.html`

A page for managing device priorities. This interface allows users to set the priority level (high, medium, or low) for different smart home devices.

## `coordinator.html`

A page for the Grid Coordinator interface. This section of the application is used to manage the overall power consumption of the building, potentially in coordination with a smart grid.

## `mpc.html`

A page for triggering and viewing Model Predictive Control (MPC) calculations. This allows users to initiate MPC runs and see the results, which are used to optimize the building's energy usage.