SHELL := /bin/bash

.PHONY: tests test test-unit run get-config push-config ecr-push


AWS_PROFILE ?= m14-dev
AWS_DEFAULT_REGION ?= eu-central-1
IMAGE_TAG ?= dev-all-latest
REPO_NAME ?= reco-explorer
LOCAL_IMAGE ?= recommender-explorer


# Run all tests
tests test:
	python3 -m pytest --config=config/config_testing.yaml test

# Run unit tests only
test-unit:
	python3 -m pytest --config=config/config_testing.yaml test/unit

# Sync configuration from S3 into local config folder
# Usage:
#   make get-config S3_URI=s3://my-bucket/path AWS_PROFILE=myprofile [AWS_DEFAULT_REGION=eu-central-1]
get-config:
	AWS_PROFILE="$(AWS_PROFILE)" S3_URI="$(S3_URI)" AWS_DEFAULT_REGION="$(AWS_DEFAULT_REGION)" bash scripts/get_config_from_s3.sh

# Push local config files to S3
# Usage:
#   make push-config S3_URI=s3://my-bucket/path AWS_PROFILE=myprofile
push-config:
	AWS_PROFILE="$(AWS_PROFILE)" S3_URI="$(S3_URI)" AWS_DEFAULT_REGION="$(AWS_DEFAULT_REGION)" LOCAL_DIR="$(LOCAL_DIR)" CONFIG_FILES="$(CONFIG_FILES)" bash scripts/push_config_to_s3.sh

# Run the panel app locally inside Docker using the helper script
# Usage:
#   make run CONFIG_URI=s3://your-bucket/path AWS_REGION=eu-central-1 AWS_PROFILE=your-aws-profile
run-docker:
	CONFIG_URI="$(CONFIG_URI)" AWS_DEFAULT_REGION="$(AWS_DEFAULT_REGION)" AWS_PROFILE="$(AWS_PROFILE)" HOST_PORT="$(HOST_PORT)" bash scripts/run_local_container.sh


# Push a local Docker image to AWS ECR using a named AWS CLI profile
# Usage:
#   make ecr-push REPO_NAME=my-service LOCAL_IMAGE=my-service:latest AWS_PROFILE=myprofile AWS_DEFAULT_REGION=eu-central-1 [IMAGE_TAG=latest]
ecr-push:
	AWS_PROFILE="$(AWS_PROFILE)" AWS_DEFAULT_REGION="$(AWS_DEFAULT_REGION)" \
	REPO_NAME="$(REPO_NAME)" LOCAL_IMAGE="$(LOCAL_IMAGE)" IMAGE_TAG="$(IMAGE_TAG)" \
	bash scripts/push_image_to_ecr.sh

# Get current config files for dev-all
get-config-dev-all: S3_URI = s3://dev-all-reco-explorer-configuration/
get-config-dev-all: get-config

# Get current config files for prod-m14
get-config-prod-m14: S3_URI = s3://prod-m14-reco-explorer-configuration/
get-config-prod-m14: get-config

# Get current config file for prod-wdr
get-config-prod-wdr: S3_URI = s3://prod-wdr-reco-explorer-configuration/
get-config-prod-wdr: get-config

# Push local configs to dev-all S3 storage
push-config-dev-all: S3_URI = s3://dev-all-reco-explorer-configuration/
push-config-dev-all: LOCAL_DIR = config/dev-all-reco-explorer-configuration/
push-config-dev-all: push-config

# Push local config to prod-m14 S3 storage
push-config-prod-m14: S3_URI = s3://prod-m14-reco-explorer-configuration/
push-config-prod-m14: LOCAL_DIR = config/prod-m14-reco-explorer-configuration/
push-config-prod-m14: push-config

# Push local config to prod-wdr S3 storage
push-config-prod-wdr: S3_URI = s3://prod-wdr-reco-explorer-configuration/
push-config-prod-wdr: LOCAL_DIR = config/prod-wdr-reco-explorer-configuration/
push-config-prod-wdr: push-config