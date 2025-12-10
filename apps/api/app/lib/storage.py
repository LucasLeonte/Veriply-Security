import os
from io import BytesIO
from typing import Optional

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_BUCKET = os.getenv("MINIO_BUCKET_DOCUMENTS", "veriply-documents")


def _ensure_local_dir():
    path = os.path.join(os.getcwd(), "storage", "documents")
    os.makedirs(path, exist_ok=True)
    return path


def upload_bytes(path: str, data: bytes, content_type: Optional[str] = None) -> str:
    """Upload bytes to MinIO if configured, otherwise save to local storage and return storage path.

    Returns a storage path string (s3://bucket/.. or file://...)
    """
    if MINIO_ENDPOINT and MINIO_ACCESS_KEY and MINIO_SECRET_KEY:
        try:
            from minio import Minio
            client = Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY, secret_key=MINIO_SECRET_KEY, secure=False)
            # ensure bucket exists
            if not client.bucket_exists(MINIO_BUCKET):
                client.make_bucket(MINIO_BUCKET)
            # put object
            data_stream = BytesIO(data)
            client.put_object(MINIO_BUCKET, path, data_stream, length=len(data), content_type=content_type or "application/octet-stream")
            return f"s3://{MINIO_BUCKET}/{path}"
        except Exception:
            # Fall back to local storage on any error
            pass

    # Local fallback
    base = _ensure_local_dir()
    target = os.path.join(base, path.replace("/", os.sep))
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "wb") as f:
        f.write(data)
    return f"file://{target}"
