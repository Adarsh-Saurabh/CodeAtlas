"""Run CodeAtlas locally and accept a project ZIP at /api/analyze."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import zipfile
from email import policy
from email.parser import BytesParser
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from analyzer.graph_builder import build_graph

ROOT = Path(__file__).parent
MAX_UPLOAD_BYTES = 50 * 1024 * 1024


def extract_zip(archive: Path, destination: Path) -> Path:
    """Extract an archive without allowing files to escape its temp directory."""
    destination = destination.resolve()
    with zipfile.ZipFile(archive) as contents:
        for member in contents.infolist():
            target = (destination / member.filename).resolve()
            try:
                target.relative_to(destination)
            except ValueError as error:
                raise ValueError("ZIP contains an unsafe path") from error
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with contents.open(member) as source, target.open("wb") as output:
                    shutil.copyfileobj(source, output)
    return destination


def parse_upload(headers, stream) -> tuple[str, bytes]:
    length = int(headers.get("Content-Length", "0"))
    if length > MAX_UPLOAD_BYTES:
        raise ValueError("ZIP must be smaller than 50 MB.")
    raw = stream.read(length)
    content_type = headers.get("Content-Type", "")
    message = BytesParser(policy=policy.default).parsebytes(
        f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode() + raw
    )
    for part in message.iter_parts():
        if part.get_content_disposition() == "form-data" and part.get_param("name", header="content-disposition") == "file":
            filename = part.get_filename() or ""
            if not filename.lower().endswith(".zip"):
                raise ValueError("Choose a .zip project file.")
            return filename, part.get_payload(decode=True)
    raise ValueError("Choose a .zip project file.")


class CodeAtlasHandler(SimpleHTTPRequestHandler):
    def send_json(self, value: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        payload = json.dumps(value).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self) -> None:
        if self.path != "/api/analyze":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        try:
            _, payload = parse_upload(self.headers, self.rfile)
            with tempfile.TemporaryDirectory() as work:
                archive = Path(work) / "project.zip"
                archive.write_bytes(payload)
                self.send_json(build_graph(extract_zip(archive, Path(work) / "repo")))
        except (ValueError, zipfile.BadZipFile) as error:
            self.send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
        except Exception as error:
            self.send_json({"error": f"Analysis failed: {error}"}, HTTPStatus.INTERNAL_SERVER_ERROR)


if __name__ == "__main__":
    handler = partial(CodeAtlasHandler, directory=ROOT / "frontend")
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8001
    print(f"CodeAtlas ready at http://localhost:{port}")
    ThreadingHTTPServer(("", port), handler).serve_forever()
