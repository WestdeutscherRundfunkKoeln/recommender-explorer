#!/usr/bin/env bash
set -euo pipefail

AWS_PROFILE=${AWS_PROFILE:-}
S3_URI=${S3_URI:-s3://dev-all-reco-explorer-configuration/}
AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-eu-central-1}

# Validate AWS profile
if [[ -z "${AWS_PROFILE}" ]]; then
  echo "Error: AWS_PROFILE is required (set your named AWS profile)" >&2
  exit 1
fi

# Validate and parse S3 URI: s3://bucket
if [[ "${S3_URI}" != s3://* ]]; then
  echo "Error: S3_URI must start with s3://" >&2
  exit 1
fi

echo ""
echo "Using: ${AWS_PROFILE} to get config file from ${S3_URI}"

# Strip scheme
uri_no_scheme=${S3_URI#s3://}
bucket=${uri_no_scheme%%/*}
if [[ -z "${bucket}" ]]; then
  echo "Error: Could not parse bucket from S3_URI='${S3_URI}'" >&2
  exit 1
fi

# Determine project root and target dir
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)
TARGET_DIR="$PROJECT_ROOT/config/${bucket}"
mkdir -p "${TARGET_DIR}"
echo "Export config(s) to ${TARGET_DIR}"

# Build and run aws s3 download command
DOWNLOAD_FROM_S3_CMD=(aws s3 sync "${S3_URI}" "${TARGET_DIR}" --profile "${AWS_PROFILE}")
"${DOWNLOAD_FROM_S3_CMD[@]}"
