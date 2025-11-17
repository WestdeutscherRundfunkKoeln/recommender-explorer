#!/usr/bin/env bash

set -euo pipefail

# Simple local runner: reads env vars only and uses sensible defaults
# Defaults (can be overridden via environment)
IMAGE_NAME=${IMAGE_NAME:-recommender-explorer}
IMAGE_TAG=${IMAGE_TAG:-latest}
CONTAINER_NAME=${CONTAINER_NAME:-recommender-explorer}
HOST_PORT=${HOST_PORT:-8080}
CONFIG_URI=${CONFIG_URI:-s3://dev-all-reco-explorer-configuration/}
AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-eu-central-1}
AWS_PROFILE=${AWS_PROFILE:-}

# Require AWS profile
if [[ -z "${AWS_PROFILE}" ]]; then
  echo "Error: AWS_PROFILE is required (set your named AWS profile)" >&2
  exit 1
fi

# Print env vars
echo ""
echo "Running script with the following settings:"
echo "container=${CONTAINER_NAME}"
echo "image=${IMAGE_NAME}:${IMAGE_TAG}"
echo "port=${HOST_PORT}"
echo "config_uri=${CONFIG_URI}"
echo "region=${AWS_DEFAULT_REGION}"
echo "profile=${AWS_PROFILE}"
echo ""

echo "Build image"
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)
cd "$PROJECT_ROOT"

docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" .

echo ""
echo "Stop existing container if present"
if docker ps -a --format '{{.Names}}' | grep -Eq "^${CONTAINER_NAME}$"; then
  docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
fi

# Prepare docker run args
RUN_ARGS=(
  --name "${CONTAINER_NAME}"
  -p "${HOST_PORT}:80"
  -e "CONFIG_URI=${CONFIG_URI}"
  -e "AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION}"
)

# If AWS_PROFILE is set, mount ~/.aws and pass it through
if [[ -n "${AWS_PROFILE}" ]]; then
  RUN_ARGS+=(
    -e "AWS_PROFILE=${AWS_PROFILE}"
    -v "$HOME/.aws:/root/.aws:ro"
  )
fi

echo ""
echo "Run container"
echo "with run args: ${RUN_ARGS[@]}"
echo "and image ${IMAGE_NAME}:${IMAGE_TAG}"
CID=$(docker run -d "${RUN_ARGS[@]}" "${IMAGE_NAME}:${IMAGE_TAG}")

echo ""
echo "See here: http://localhost:${HOST_PORT}"
