"""Dependency-free local API and demo server.

Run with: ``python3 -m src.api_server``
"""

from __future__ import annotations

import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .area_opportunities import AreaOpportunityService
from .recovery_domain import Profile, RecoveryService, Role


ROOT = Path(__file__).resolve().parent.parent


def build_state() -> tuple[RecoveryService, AreaOpportunityService]:
    service = RecoveryService()
    service.add_profile(Profile("household_1", Role.HOUSEHOLD, "Household A", 28.7042, 77.1024))
    service.add_profile(Profile("household_2", Role.HOUSEHOLD, "Household B", 28.6450, 77.2165))
    service.add_profile(Profile("kabadiwala_1", Role.KABADIWALA, "Ramesh Recovery", 28.6800, 77.1500, 1, {"pet", "cardboard", "paper", "aluminium", "glass", "wood"}))
    service.add_profile(Profile("recycler_1", Role.RECYCLER, "GreenCycle Delhi", 28.6500, 77.2000))
    first = service.add_material("household_1", "pet", 4)
    service.add_material("household_1", "cardboard", 2)
    second = service.add_material("household_2", "aluminium", 1.5)
    service.create_collection_request("household_1", [first.id, next(m.id for m in service.materials.values() if m.source_id == "household_1" and m.material_type == "cardboard")])
    service.create_collection_request("household_2", [second.id])
    return service, AreaOpportunityService()


service, area_service = build_state()


class DemoHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / "demo"), **kwargs)

    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length) or b"{}")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/")
        try:
            if path == "/api/demo/users":
                users = [{"id": p.id, "role": p.role.value, "name": p.name} for p in service.profiles.values()]
                return self._send_json({"users": users})
            if path == "/api/demo/areas" or path == "/api/kabadiwalas/kabadiwala_1/areas":
                return self._send_json({"areas": area_service.summaries(service.requests.values())})
            if path.startswith("/api/kabadiwalas/kabadiwala_1/areas/") and path.endswith("/opportunities"):
                area_id = path.split("/")[-2]
                return self._send_json({"opportunities": area_service.opportunities(area_id, service.requests.values())})
            if path == "/api/kabadiwalas/kabadiwala_1/inventory":
                return self._send_json({"inventory": _inventory("kabadiwala_1")})
            if path == "/api/recyclers/recycler_1/available-material":
                return self._send_json({"availableMaterial": service.available_material("recycler_1")})
            return super().do_GET()
        except ValueError as exc:
            self._send_json({"error": {"code": "NOT_FOUND", "message": str(exc)}}, 404)

    def do_POST(self):
        global service, area_service
        path = urlparse(self.path).path.rstrip("/")
        payload = self._body()
        try:
            if path == "/api/demo/reset":
                service, area_service = build_state()
                return self._send_json({"ok": True})
            if path == "/api/materials":
                material = service.add_material(payload["userId"], payload["materialType"], float(payload["quantityKg"]))
                return self._send_json(_material_json(material), 201)
            if path.startswith("/api/collection-requests/") and path.endswith("/accept"):
                request = service.accept_request(payload["kabadiwalaId"], path.split("/")[-2])
                return self._send_json(_request_json(request))
            if path.startswith("/api/collection-requests/") and path.endswith("/collect"):
                request = service.collect_request(payload["kabadiwalaId"], path.split("/")[-2])
                return self._send_json(_request_json(request))
            return self._send_json({"error": {"code": "NOT_FOUND", "message": "endpoint not found"}}, 404)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            self._send_json({"error": {"code": "INVALID_REQUEST", "message": str(exc)}}, 400)


def _material_json(material) -> dict:
    return {"id": material.id, "materialType": material.material_type, "quantityKg": material.quantity_kg, "estimatedValueInr": round(material.estimated_value), "status": material.status}


def _request_json(request) -> dict:
    return {"id": request.id, "status": request.status.value, "estimatedValueInr": round(request.estimated_value), "quantityByType": request.quantity_by_type, "assignedKabadiwalaId": request.assigned_kabadiwala_id}


def _inventory(holder_id: str) -> list[dict]:
    grouped = {}
    for material in service.materials.values():
        if material.current_holder_id == holder_id and material.status == "collected":
            grouped[material.material_type] = grouped.get(material.material_type, 0) + material.quantity_kg
    return [{"materialType": material_type, "quantityKg": round(quantity, 3)} for material_type, quantity in grouped.items()]


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    print(f"Starting recovery demo at http://localhost:{port}")
    ThreadingHTTPServer(("0.0.0.0", port), DemoHandler).serve_forever()
