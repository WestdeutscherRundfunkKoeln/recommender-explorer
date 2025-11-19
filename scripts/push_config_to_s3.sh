#!/usr/bin/env bash

set -euo pipefail

AWS_PROFILE=${AWS_PROFILE:-}
S3_URI=${S3_URI:-}
AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-}
CONFIG_FILES=${CONFIG_FILES:-}

# Determine project root and default LOCAL_DIR
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)
LOCAL_DIR=${LOCAL_DIR:-"$PROJECT_ROOT/config"}

# Validate tools and inputs
if [[ -z "${AWS_PROFILE}" ]]; then
  echo "Error: AWS_PROFILE is required (set your named AWS profile)" >&2
  exit 1
fi

if [[ "${S3_URI}" != s3://* ]]; then
  echo "Error: S3_URI must start with s3://" >&2
  exit 1
fi

if [[ -z "${CONFIG_FILES}" ]]; then
  if [[ ! -d "${LOCAL_DIR}" ]]; then
    echo "Error: LOCAL_DIR does not exist: ${LOCAL_DIR}" >&2
    exit 1
  fi
fi

# Build candidate file list
files_array=()
if [[ -n "${CONFIG_FILES}" ]]; then
  # Split CONFIG_FILES respecting spaces in path via newline trick
  # Users can separate by newline or space; we re-scan each entry
  while IFS= read -r f; do
    [[ -z "$f" ]] && continue
    files_array+=("$f")
  done < <(printf '%s\n' ${CONFIG_FILES})
else
  # Find recursively under LOCAL_DIR for config_*.yaml (null-delimited for safety)
  while IFS= read -r -d '' f; do
    files_array+=("$f")
  done < <(find "$LOCAL_DIR" -type f -name 'config_*.yaml' -print0)
fi

# Validate we have files
if [[ ${#files_array[@]} -eq 0 ]]; then
  echo "Error: No config_*.yaml files found to upload (LOCAL_DIR='${LOCAL_DIR}')" >&2
  exit 1
fi

# Upload each file
uploaded=0
failed=0
for f in "${files_array[@]}"; do
  if [[ ! -f "$f" ]]; then
    echo "Warning: skipping non-file path: $f" >&2
    ((failed++)) || true
    continue
  fi
  base=$(basename -- "$f")
  dest="${S3_URI%/}/$base"
  CMD=(aws s3 cp "$f" "$dest" --profile "$AWS_PROFILE")
  if [[ -n "$AWS_DEFAULT_REGION" ]]; then
    CMD+=(--region "$AWS_DEFAULT_REGION")
  fi
  # Execute command safely
  if "${CMD[@]}"; then
    ((uploaded++)) || true
  else
    ((failed++)) || true
  fi
done

# If any failed, return non-zero to indicate partial failure, but still print summary
region_out="${AWS_DEFAULT_REGION}"
if [[ -z "${region_out}" ]]; then
  region_out=$(aws configure get region --profile "${AWS_PROFILE}" 2>/dev/null || true)
fi

echo "profile=${AWS_PROFILE} s3_uri=${S3_URI} local_dir=${LOCAL_DIR} files=${#files_array[@]} uploaded=${uploaded} failed=${failed} region=${region_out}"

if [[ $failed -gt 0 ]]; then
  exit 2
fi
