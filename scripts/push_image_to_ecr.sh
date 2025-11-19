#!/usr/bin/env bash

set -euo pipefail

AWS_PROFILE=${AWS_PROFILE:-}
AWS_REGION=${AWS_DEFAULT_REGION:-}
REPO_NAME=${REPO_NAME:-}
LOCAL_IMAGE=${LOCAL_IMAGE:-}
IMAGE_TAG=${IMAGE_TAG:-latest}

if [[ -z "${AWS_PROFILE}" || -z "${AWS_REGION}" || -z "${REPO_NAME}" || -z "${LOCAL_IMAGE}" ]]; then
  echo "Usage error: Missing required env vars." >&2
  echo "Required: AWS_PROFILE, AWS_DEFAULT_REGION, REPO_NAME, LOCAL_IMAGE" >&2
  exit 1
fi

echo "=== Resolving AWS account using profile '${AWS_PROFILE}' ==="
ACCOUNT_ID=$(aws sts get-caller-identity --profile "${AWS_PROFILE}" --query Account --output text)
REGISTRY="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "=== Logging in to ECR: ${REGISTRY} (region: ${AWS_REGION}) ==="
aws ecr get-login-password --region "${AWS_REGION}" --profile "${AWS_PROFILE}" \
  | docker login --username AWS --password-stdin "${REGISTRY}"

echo "=== Ensuring repository exists: ${REPO_NAME} ==="
if ! aws ecr describe-repositories --repository-names "${REPO_NAME}" \
  --region "${AWS_REGION}" --profile "${AWS_PROFILE}" >/dev/null 2>&1; then
  aws ecr create-repository --repository-name "${REPO_NAME}" \
    --region "${AWS_REGION}" --profile "${AWS_PROFILE}" >/dev/null
  echo "Created repository: ${REPO_NAME}"
fi

TARGET_IMAGE="${REGISTRY}/${REPO_NAME}:${IMAGE_TAG}"
echo "=== Tagging image ==="
echo "Local:  ${LOCAL_IMAGE}"
echo "Target: ${TARGET_IMAGE}"
docker tag "${LOCAL_IMAGE}" "${TARGET_IMAGE}"

echo "=== Pushing to ECR ==="
docker push "${TARGET_IMAGE}"

echo "=== Done ==="
echo "Pushed: ${TARGET_IMAGE}"
