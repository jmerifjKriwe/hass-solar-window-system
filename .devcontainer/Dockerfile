FROM mcr.microsoft.com/devcontainers/python:3.14

# Install system dependencies including FFmpeg, libpcap, and libturbojpeg
RUN apt-get update && apt-get install -y ffmpeg libpcap0.8 libturbojpeg0 --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements-test.txt /tmp/requirements-test.txt

# Install dependencies from requirements-test.txt
RUN pip install --no-cache-dir -r /tmp/requirements-test.txt

# Create config directory
RUN mkdir -p /workspaces/solar_window_system/config

# Set working directory
WORKDIR /workspaces/solar_window_system

# Keep container running
CMD ["sleep", "infinity"]
