"""AWS Lambda adapter for the existing JSON HTTP API."""

from __future__ import annotations

import base64
import io
import json
from http.client import HTTPMessage
from urllib.parse import urlencode

from .api_server import DemoHandler


class _Response:
    def __init__(self) -> None:
        self.status = 200
        self.headers: dict[str, str] = {}
        self.body = io.BytesIO()

    def send_response(self, status: int) -> None:
        self.status = status

    def send_header(self, name: str, value: str) -> None:
        self.headers[name] = value

    def end_headers(self) -> None:
        return None


class _Request(DemoHandler):
    def __init__(self, event: dict, response: _Response) -> None:
        self.path = event.get("rawPath") or event.get("path") or "/"
        query = event.get("queryStringParameters") or {}
        if query:
            self.path += "?" + urlencode(query)
        self.command = event.get("requestContext", {}).get("http", {}).get("method", "GET")
        self.headers = HTTPMessage()
        for key, value in (event.get("headers") or {}).items():
            self.headers[key] = value
        body = event.get("body") or ""
        if event.get("isBase64Encoded"):
            body = base64.b64decode(body).decode()
        self.rfile = io.BytesIO(body.encode())
        self.wfile = response.body
        self._lambda_response = response

    def send_response(self, status: int) -> None:
        self._lambda_response.send_response(status)

    def send_header(self, name: str, value: str) -> None:
        self._lambda_response.send_header(name, value)

    def end_headers(self) -> None:
        self._lambda_response.end_headers()


def handler(event: dict, context) -> dict:
    response = _Response()
    request = _Request(event, response)
    method = request.command.upper()
    if method == "GET":
        request.do_GET()
    elif method == "POST":
        request.do_POST()
    elif method == "PUT":
        request.do_PUT()
    elif method == "DELETE":
        request.do_DELETE()
    elif method == "OPTIONS":
        request.do_OPTIONS()
    else:
        response.status = 405
        response.body.write(json.dumps({"error": {"code": "METHOD_NOT_ALLOWED", "message": "method not allowed"}}).encode())
    payload = response.body.getvalue()
    return {"statusCode": response.status, "headers": response.headers, "isBase64Encoded": False, "body": payload.decode()}
