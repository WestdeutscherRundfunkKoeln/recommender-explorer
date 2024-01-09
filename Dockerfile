# Use the official lightweight Python image.
# https://hub.docker.com/_/python
# FROM python:3.10-slim

# USE AWS image due to docker-hub rate limits
FROM public.ecr.aws/docker/library/python:3.10-slim-bullseye

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY src/RecoExplorer.py RecoExplorer.py

#modules
COPY assets assets
COPY config config
COPY src/controller controller
COPY src/exceptions exceptions
COPY src/model model
COPY src/util util
COPY src/view view
COPY src/dto dto
COPY requirements.txt requirements.txt
COPY src/constants.py constants.py

# Install production dependencies.
RUN pip install --no-cache-dir -r requirements.txt

# Run the web service on container startup.
EXPOSE 80

# go
CMD panel serve RecoExplorer.py --address 0.0.0.0 --port 80 --allow-websocket-origin="*" --log-level info
