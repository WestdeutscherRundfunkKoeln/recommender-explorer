from typing import Any

from google.api_core.exceptions import GoogleAPICallError


class MockBlob:
    def __init__(self, data: str, name: str):
        self.data = data
        self.name = name

    def download_as_text(self):
        if not self.data:
            err = GoogleAPICallError("Blob not found")
            err.code = 400
            raise err
        return self.data

    def upload_from_string(self, data: str):
        self.data = data


class MockBucket:
    def __init__(self, data: dict[str, Any]):
        self.data = {k: MockBlob(v, k) for k, v in data.items()}

    def blob(self, blob_name: str):
        if blob_name not in self.data:
            self.data[blob_name] = MockBlob("", blob_name)
        return self.data[blob_name]

    def list_blobs(self, *args, **kwargs):
        prefix = kwargs["match_glob"].split("/")[0]
        if prefix == "raise_error":
            raise Exception("Test error")
        for blob in self.data.values():
            if blob.name.startswith(prefix):
                yield blob


class MockStorageClient:
    def __init__(self, data: dict[str, str]):
        self._buckets = {"wdr-recommender-exporter-dev-import": MockBucket(data)}
        self.bucket_name = None

    def bucket(self, bucket_name: str):
        if bucket_name not in self._buckets:
            self._buckets[bucket_name] = MockBucket({})
        return self._buckets[bucket_name]
