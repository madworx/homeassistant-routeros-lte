FROM mcr.microsoft.com/devcontainers/python:3.13

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Pre-install Home Assistant Core for development
RUN pip install --no-cache-dir homeassistant

# Create HA config directory
RUN mkdir -p /workspaces/homeassistant-routeros/config && \
    echo "default_config:" > /workspaces/homeassistant-routeros/config/configuration.yaml
