import os
from app.lib import storage


def test_upload_bytes_local(tmp_path, monkeypatch):
    # Ensure MinIO env not set so local fallback is used
    monkeypatch.delenv('MINIO_ENDPOINT', raising=False)
    monkeypatch.delenv('MINIO_ACCESS_KEY', raising=False)
    monkeypatch.delenv('MINIO_SECRET_KEY', raising=False)
    monkeypatch.setenv('PWD', str(tmp_path))

    data = b"hello world"
    path = "tenant1/bot1/doc1/test.txt"
    result = storage.upload_bytes(path, data, content_type="text/plain")

    assert result.startswith("file://")
    local_path = result.replace("file://", "")
    assert os.path.exists(local_path)
    with open(local_path, "rb") as f:
        assert f.read() == data
