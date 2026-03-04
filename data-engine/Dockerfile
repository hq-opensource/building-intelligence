# Use a Python 3.13 image
FROM python:3.13-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    & rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy the source code
COPY common common
COPY data-engine data-engine

# Install dependencies and the project into a virtual environment
RUN uv venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Install common first
RUN uv pip install ./common

# Install data-engine
RUN uv pip install ./data-engine

# Final stage
FROM python:3.13-slim AS runtime

WORKDIR /app

# Copy the virtual environment and application code from the builder
COPY --from=builder /app /app

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

WORKDIR /app/data-engine

# Command to run the application
ENTRYPOINT ["python", "-m", "data_engine.app"]