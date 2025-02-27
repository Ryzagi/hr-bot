# Dockerfile
FROM python:3.10-slim-bullseye

# Set the working directory in the container to /app
WORKDIR /app

# Copy the entire project into the container at /app
COPY . /app

# Install pip dependencies (the paths are now relative to the project root)
RUN pip install .
