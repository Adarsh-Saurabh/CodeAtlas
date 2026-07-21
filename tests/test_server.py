import zipfile
from io import BytesIO

import pytest

from server import extract_zip, parse_upload


def test_extract_zip_rejects_path_traversal(tmp_path):
    archive = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive, "w") as contents:
        contents.writestr("../outside.py", "x = 1")
    with pytest.raises(ValueError, match="unsafe path"):
        extract_zip(archive, tmp_path / "repo")


def test_parse_upload_accepts_zip():
    boundary = "codeatlas"
    body = (
        b"--codeatlas\r\n"
        b'Content-Disposition: form-data; name="file"; filename="repo.zip"\r\n'
        b"Content-Type: application/zip\r\n\r\n"
        + b"PK\x05\x06" + b"\0" * 18 +
        b"\r\n--codeatlas--\r\n"
    )
    headers = {"Content-Length": str(len(body)), "Content-Type": f"multipart/form-data; boundary={boundary}"}
    assert parse_upload(headers, BytesIO(body))[0] == "repo.zip"
