"""Storage abstraction layer for assets.

Current implementation: local file system.
Future migration: OSS/S3 by swapping the backend class.
"""

import os
from abc import ABC, abstractmethod


class StorageBackend(ABC):
    """Abstract storage backend."""

    @abstractmethod
    def save(self, key: str, data: bytes) -> str:
        """Save file and return storage URI."""
        ...

    @abstractmethod
    def read(self, key: str) -> bytes:
        """Read file by key."""
        ...

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if file exists."""
        ...

    @abstractmethod
    def get_url(self, key: str) -> str:
        """Get download URL for the file."""
        ...

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete file."""
        ...


class LocalFileStorage(StorageBackend):
    """Local file system storage backend."""

    def __init__(self, base_path: str = "./data/storage"):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    def _path(self, key: str) -> str:
        return os.path.join(self.base_path, key)

    def save(self, key: str, data: bytes) -> str:
        file_path = self._path(key)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(data)
        return file_path

    def read(self, key: str) -> bytes:
        with open(self._path(key), "rb") as f:
            return f.read()

    def exists(self, key: str) -> bool:
        return os.path.exists(self._path(key))

    def get_url(self, key: str) -> str:
        return f"/v1/assets/download?key={key}"

    def delete(self, key: str) -> None:
        path = self._path(key)
        if os.path.exists(path):
            os.remove(path)


class OSSStorage(StorageBackend):
    """OSS/S3 storage backend (placeholder for future migration)."""

    def __init__(self, bucket: str = "kk-ai-assets"):
        self.bucket = bucket

    def save(self, key: str, data: bytes) -> str:
        raise NotImplementedError("OSS backend not implemented yet")

    def read(self, key: str) -> bytes:
        raise NotImplementedError("OSS backend not implemented yet")

    def exists(self, key: str) -> bool:
        raise NotImplementedError("OSS backend not implemented yet")

    def get_url(self, key: str) -> str:
        return f"https://{self.bucket}.oss-cn-beijing.aliyuncs.com/{key}"

    def delete(self, key: str) -> None:
        raise NotImplementedError("OSS backend not implemented yet")


_storage_instance: StorageBackend | None = None


def get_storage() -> StorageBackend:
    """Get singleton storage backend."""
    global _storage_instance
    if _storage_instance is None:
        # Read from env or config to select backend
        backend_type = os.getenv("ASSET_STORAGE_BACKEND", "local")
        if backend_type == "oss":
            _storage_instance = OSSStorage()
        else:
            _storage_instance = LocalFileStorage()
    return _storage_instance
