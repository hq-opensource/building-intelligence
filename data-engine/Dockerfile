FROM python:3.11.0-slim-bullseye AS builder

# Install Poetry tool
RUN pip3 install poetry && poetry --version

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

# Copy the application source files
COPY common common
COPY data-engine data-engine

WORKDIR /app/data-engine

# Install the dependencies and create a virtual environment
RUN poetry install

# The runtime
FROM python:3.11.0-slim-bullseye AS runtime

# Add the virtual environment binaries to PATH
ENV PATH="/app/data-engine/.venv/bin:$PATH"

# Copy the files (including the virtual environment) from the builder
COPY --from=builder /app /app

WORKDIR /app/data-engine

ENTRYPOINT ["python", "-m", "data_engine.app"]