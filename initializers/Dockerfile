# Use a Python 3.13 image
FROM python:3.13-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy the source code
COPY pyproject.toml uv.lock ./
COPY common common
COPY initializers initializers

# Install dependencies and the project into a virtual environment
RUN uv venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Install common first
RUN uv pip install ./common

# Install initializers
RUN uv pip install ./initializers

# Final stage
FROM python:3.13-slim AS runtime

WORKDIR /app

# Copy the virtual environment and application code from the builder
COPY --from=builder /app /app

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

WORKDIR /app/initializers

# Command to run the application
ENTRYPOINT ["python", "-m", "initializers.app"]