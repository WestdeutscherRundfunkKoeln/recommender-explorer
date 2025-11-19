import os
import tempfile
from pathlib import Path
from typing import Optional

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError


class S3Location:
    def __init__(self, bucket: str, key: str):
        self.bucket = bucket
        self.key = key


def parse_s3_uri(s3_uri: str, *, allow_bucket_root: bool = False) -> S3Location:
    """
    Parse an S3 URI into bucket + key.

    - When allow_bucket_root=True, accept forms like `s3://bucket` or `s3://bucket/`
      and return an empty key (""), which indicates the bucket root (useful for listing).
    - When allow_bucket_root=False (default), require a non-empty key.
    """
    if not s3_uri.startswith("s3://"):
        raise ValueError(f"Not an S3 URI: {s3_uri}")
    without_scheme = s3_uri[len("s3://"):]

    # Accept s3://bucket (no slash) when allowed
    if "/" not in without_scheme:
        if not without_scheme:
            raise ValueError(f"Invalid S3 URI (bucket required): {s3_uri}")
        if allow_bucket_root:
            return S3Location(bucket=without_scheme, key="")
        raise ValueError(f"Invalid S3 URI (bucket/key required): {s3_uri}")

    bucket, rest = without_scheme.split("/", 1)
    if rest == "" and allow_bucket_root:
        # s3://bucket/
        return S3Location(bucket=bucket, key="")

    if not bucket or not rest:
        raise ValueError(f"Invalid S3 URI (bucket/key required): {s3_uri}")
    return S3Location(bucket=bucket, key=rest)


def _boto3_client(service: str, region: Optional[str] = None):
    region_name = region or os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
    return boto3.client(service, region_name=region_name, config=BotoConfig(retries={"max_attempts": 5}))


def download_s3_object_to_temp(s3_uri: str, *, suffix: Optional[str] = None) -> Path:
    # Keep strict parsing here: we must have a concrete key to download
    loc = parse_s3_uri(s3_uri)
    s3 = _boto3_client("s3")
    filename = os.path.basename(loc.key) or "config.yaml"
    # Create a dedicated temp directory and preserve the original filename so downstream
    # client inference based on '/config_<client>.yaml' keeps working.
    tmp_dir = tempfile.mkdtemp(prefix="reco-")
    out = Path(tmp_dir) / (filename if not suffix else f"{filename}{suffix}")

    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        s3.download_file(loc.bucket, loc.key, str(out))
    except ClientError as e:
        raise RuntimeError(f"Failed to download {s3_uri}: {e}") from e

    return out



def list_s3_objects(s3_uri: str, pattern: str = "config_*.yaml") -> list[str]:
    """
    List S3 objects under a given s3://bucket[/prefix]/ and return fully-qualified s3 URIs
    matching the provided filename pattern (fnmatch applied to the basename).

    If s3_uri points to a specific object (e.g., endswith .yaml and not a "directory"),
    this function will simply return [s3_uri] without listing.
    """
    from fnmatch import fnmatch

    # Allow bucket-root (empty key) for listing
    loc = parse_s3_uri(s3_uri, allow_bucket_root=True)

    # If a concrete file was provided, return it as-is
    if loc.key and not loc.key.endswith("/") and (loc.key.endswith(".yaml") or loc.key.endswith(".yml")):
        return [s3_uri]

    prefix = loc.key or ""
    if prefix and not prefix.endswith("/"):
        # Consider non-suffixed path also as a prefix
        prefix = prefix + "/"

    s3 = _boto3_client("s3")

    uris: list[str] = []
    continuation_token = None
    while True:
        kwargs = {"Bucket": loc.bucket, "Prefix": prefix}
        if continuation_token:
            kwargs["ContinuationToken"] = continuation_token
        resp = s3.list_objects_v2(**kwargs)
        for obj in resp.get("Contents", []):
            key = obj.get("Key")
            if not key:
                continue
            name = os.path.basename(key)
            if fnmatch(name, pattern):
                uris.append(f"s3://{loc.bucket}/{key}")
        if resp.get("IsTruncated"):
            continuation_token = resp.get("NextContinuationToken")
        else:
            break

    return uris