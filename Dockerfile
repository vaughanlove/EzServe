# syntax=docker/dockerfile:1

# Comments are provided throughout this file to help you get started.
# If you need more help, visit the Dockerfile reference guide at
# https://docs.docker.com/engine/reference/builder/

# if we want to use our custom fork of langchain, install git in the container
# RUN apt-get update && apt-get install -y git
# and in requirements.txt put 
# -e 'url_to_fork'

FROM ubuntu:22.04
RUN sudo apt install -y linux-tools-virtual hwdata
RUN update-alternatives --install /usr/local/bin/usbip usbip `ls /usr/lib/linux-tools/*/usbip | tail -n1` 20
RUN apt-get update -y 
RUN apt-get install -y alsa-utils 
RUN apt-get install -y libsndfile1-dev
RUN apt-get install -y libportaudio2
RUN apt-get update

ARG PYTHON_VERSION=
FROM python:3.11.4-slim as base

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND noninteractive

# Install package dependencies


RUN apt-get clean

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Download dependencies as a separate step to take advantage of Docker's caching.
# Leverage a cache mount to /root/.cache/pip to speed up subsequent builds.
# Leverage a bind mount to requirements.txt to avoid having to copy them into
# into this layer.
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt \
    pip install wavio \
    pip install scipy \ 
    pip install sounddevice
    
# Switch to the non-privileged user to run the application.
#USER appuser

# Copy the source code into the container.
COPY . .

# Expose the port that the application listens on.
EXPOSE 8000

# Run the application.
CMD python app/main.py
