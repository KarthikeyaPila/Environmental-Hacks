"""Dependency-free local API and demo server.

Run with: ``python3 -m src.api_server``
"""

from __future__ import annotations

import json
import os
import base64
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

try:
    from botocore.exceptions import ClientError
except ImportError:  # boto3 is optional for local mock mode
    class ClientError(Exception):
        pass

from .area_opportunities import AreaOpportunityService, DELHI_AREAS
from .image_classifier import classify_s3_object, classify_with_rekognition
from .image_storage import create_upload, delete_upload
from .route_planner import plan_preview
from .recovery_domain import Profile, RecoveryService, RequestStatus, RequirementStatus, Role


ROOT = Path(__file__).resolve().parent.parent


def build_state(with_demo_requests: bool = False) -> tuple[RecoveryService, AreaOpportunityService]:
    service = RecoveryService()
    areas = {area.name: area for area in DELHI_AREAS}
    household_names = [
        "Asha Verma", "Bharat Singh", "Chitra Rao", "Deepak Sharma", "Esha Mehta", "Farhan Khan",
        "Gauri Nair", "Harish Gupta", "Ishita Jain", "Jatin Kapoor", "Kavita Das", "Lokesh Yadav",
        "Meena Iyer", "Nikhil Batra", " पूजा Shah", "Ravi Menon", "Sara Thomas", "Tarun Bose",
        "Uma Sethi", "Vikram Joshi", "Wafa Ali", "Yash Malhotra", "Zoya Sen", "Anil Roy",
    ]
    household_regions = ["North West", "West", "South West", "Central", "South", "South East"]
    for index, name in enumerate(household_names, start=1):
        area = areas[household_regions[(index - 1) % len(household_regions)]]
        latitude, longitude = area.center_latitude, area.center_longitude
        if index == 1:
            latitude, longitude = 28.7042, 77.1024
        service.add_profile(Profile(f"household_{index}", Role.HOUSEHOLD, name, latitude, longitude, locality=area.name))

    kabadiwalas = [
        ("Ramesh Recovery", "West", {"pet", "cardboard", "paper", "aluminium", "glass", "wood"}),
        ("Farida Collection", "West", {"pet", "cardboard", "paper", "glass"}),
        ("Suresh Kabadi Network", "Central", {"pet", "paper", "aluminium", "glass"}),
        ("Lakshmi Materials", "South", {"pet", "cardboard", "paper", "aluminium", "wood"}),
    ]
    for index, (name, region, materials) in enumerate(kabadiwalas, start=1):
        area = areas[region]
        service.add_profile(Profile(f"kabadiwala_{index}", Role.KABADIWALA, name, area.center_latitude, area.center_longitude, 25, materials, 4.5 + index / 10, 1 + index / 20, locality=region))

    recycler_names = ["GreenCycle Delhi", "ReForm Plastics", "Nayi Disha Paper", "MetalLoop India", "GlassRoot Works", "Urban Fibre Co", "Bharat Materials", "Circular Carton", "CleanCast Industries"]
    recycler_materials = ["pet", "paper", "cardboard", "aluminium", "glass", "paper", "pet", "cardboard", "aluminium"]
    for index, name in enumerate(recycler_names, start=1):
        area = DELHI_AREAS[(index + 2) % len(DELHI_AREAS)]
        service.add_profile(Profile(f"recycler_{index}", Role.RECYCLER, name, area.center_latitude, area.center_longitude, locality=area.name, contact=f"materials{index}@demo-recycler.in"))

    material_types = ["pet", "cardboard", "paper", "aluminium", "glass", "wood"]
    for index in range(1, 25):
        household_id = f"household_{index}"
        first_quantity = 4 if index == 1 else round(1.5 + (index % 7) * 0.75, 2)
        second_quantity = 2 if index == 1 else round(2 + (index % 5) * 0.5, 2)
        first = service.add_material(household_id, material_types[(index - 1) % len(material_types)], first_quantity)
        service.add_material(household_id, material_types[index % len(material_types)], second_quantity)
        if with_demo_requests and index > 1:
            request = service.create_collection_request(household_id, [first.id])
            if index % 4 == 0:
                service.accept_request(f"kabadiwala_{((index // 2) % 4) + 1}", request.id)
            if index % 8 == 0:
                service.collect_request(request.assigned_kabadiwala_id, request.id)

    if with_demo_requests:
        for index in range(1, 10):
            requirement = service.create_requirement(f"recycler_{index}", recycler_materials[index - 1], 8 + index * 2, 2)
            if index % 3 == 0:
                requirement.fulfilled_quantity_kg = requirement.required_quantity_kg
                requirement.status = RequirementStatus.FULFILLED
    return service, AreaOpportunityService()


repository = None
if os.getenv("DYNAMODB_ENABLED", "false").lower() == "true":
    from .dynamodb_repository import DynamoRecoveryRepository

    service, area_service = build_state(with_demo_requests=False)
    repository = DynamoRecoveryRepository(
        table_name=os.getenv("DYNAMODB_TABLE", "environmental-recovery"),
        region_name=os.getenv("AWS_REGION", "ap-south-1"),
    )
    repository.load_service(service)
else:
    service, area_service = build_state(with_demo_requests=True)


class DemoHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / "demo"), **kwargs)

    def _send_json(self, payload: dict, status: int = 200) -> None:
        if repository is not None and getattr(self, "_persist_after_response", False) and status < 400:
            repository.save_service(service)
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", self._cors_origin())
        self.send_header("Vary", "Origin")
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length) or b"{}")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", self._cors_origin())
        self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, x-amz-server-side-encryption")
        self.end_headers()

    def _cors_origin(self) -> str:
        origin = self.headers.get("Origin", "")
        allowed = [item.strip() for item in os.getenv("CORS_ORIGINS", os.getenv("CORS_ORIGIN", "*")).split(",") if item.strip()]
        return origin if origin and ("*" in allowed or origin in allowed) else (allowed[0] if allowed else "*")

    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/")
        try:
            if path == "/api/demo/users":
                users = [{"id": p.id, "role": p.role.value, "name": p.name} for p in service.profiles.values()]
                return self._send_json({"users": users})
            if path == "/api/demo/areas" or path == "/api/kabadiwalas/kabadiwala_1/areas":
                summaries = area_service.summaries(service.requests.values())
                status_counts = {status.value: 0 for status in RequestStatus}
                for request in service.requests.values():
                    status_counts[request.status.value] += 1
                return self._send_json({
                    "areas": summaries,
                    "requestSummary": {
                        "total": len(service.requests),
                        "open": status_counts[RequestStatus.PENDING.value],
                        "accepted": status_counts[RequestStatus.ACCEPTED.value],
                        "collected": status_counts[RequestStatus.COLLECTED.value],
                        "rejected": status_counts[RequestStatus.REJECTED.value],
                        "cancelled": status_counts[RequestStatus.CANCELLED.value],
                    },
                })
            if path.startswith("/api/kabadiwalas/kabadiwala_1/areas/") and path.endswith("/opportunities"):
                area_id = path.split("/")[-2]
                return self._send_json({"opportunities": area_service.opportunities(area_id, service.requests.values())})
            if path == "/api/kabadiwalas/kabadiwala_1/inventory":
                return self._send_json({"inventory": _inventory("kabadiwala_1")})
            if path == "/api/kabadiwalas/kabadiwala_1/requests":
                requests = [
                    r for r in service.requests.values()
                    if r.status == RequestStatus.PENDING
                    or r.assigned_kabadiwala_id == "kabadiwala_1"
                ]
                return self._send_json({"requests": [_request_json(r) for r in requests]})
            if path == "/api/households/household_1/inventory":
                return self._send_json({"inventory": _household_inventory("household_1")})
            if path == "/api/households/household_1/collection-request":
                request = next((r for r in reversed(list(service.requests.values())) if r.household_id == "household_1"), None)
                request_data = _request_json(request) if request else None
                if request_data:
                    region = area_service.area_for(request.latitude, request.longitude)
                    request_data["region"] = region.name
                    request_data["regionId"] = region.id
                return self._send_json({"request": request_data})
            if path == "/api/recyclers/recycler_1/available-material":
                return self._send_json({"availableMaterial": [_available_json(item) for item in service.available_material("recycler_1")]})
            if path == "/api/recyclers/recycler_1/requirements":
                return self._send_json({"requirements": [_requirement_json(r) for r in service.requirements.values() if r.recycler_id == "recycler_1"]})
            if path == "/api/kabadiwalas/kabadiwala_1/route":
                raise ValueError("route planning requires POST")
            if path == "/api/recyclers/recycler_1/bookings":
                return self._send_json({"bookings": [_booking_json(b) for b in service.bookings.values() if b.recycler_id == "recycler_1"]})
            if path == "/api/households/household_1/metrics":
                return self._send_json(service.household_metrics("household_1"))
            if path == "/api/kabadiwalas/kabadiwala_1/metrics":
                return self._send_json(service.kabadiwala_metrics("kabadiwala_1"))
            if path == "/api/kabadiwalas/kabadiwala_1/profile":
                return self._send_json(service.profile_summary("kabadiwala_1"))
            if path == "/api/recyclers/recycler_1/metrics":
                return self._send_json(service.recycler_metrics("recycler_1"))
            return super().do_GET()
        except ValueError as exc:
            self._send_json({"error": {"code": "NOT_FOUND", "message": str(exc)}}, 404)

    def do_POST(self):
        global service, area_service
        self._persist_after_response = True
        path = urlparse(self.path).path.rstrip("/")
        payload = self._body()
        try:
            if path == "/api/demo/reset":
                service, area_service = build_state(with_demo_requests=True)
                return self._send_json({"ok": True})
            if path == "/api/materials":
                material = service.add_material(payload["userId"], payload["materialType"], float(payload["quantityKg"]))
                return self._send_json(_material_json(material), 201)
            if path == "/api/classify-image":
                s3_key = payload.get("s3Key")
                if s3_key and os.getenv("REKOGNITION_MODEL_ARN"):
                    result = classify_s3_object(os.getenv("ML_S3_BUCKET", "environmental-recovery-ml-132218943520"), s3_key)
                    delete_upload(os.getenv("ML_S3_BUCKET", "environmental-recovery-ml-132218943520"), s3_key)
                    return self._send_json(result)
                image_base64 = payload.get("imageBase64")
                if image_base64 and os.getenv("REKOGNITION_MODEL_ARN"):
                    image_bytes = base64.b64decode(image_base64, validate=True)
                    return self._send_json(classify_with_rekognition(image_bytes))
                return self._send_json(_mock_classification(payload.get("filename", "")))
            if path == "/api/image-upload":
                content_type = payload.get("contentType")
                filename = payload.get("filename", "image")
                if content_type not in {"image/jpeg", "image/png"}:
                    raise ValueError("only JPG and PNG images are supported")
                return self._send_json(create_upload(os.getenv("ML_S3_BUCKET", "environmental-recovery-ml-132218943520"), content_type, filename))
            if path == "/api/kabadiwalas/kabadiwala_1/route":
                request_ids = payload.get("requestIds", [])
                opportunities = [item for item in area_service.opportunities(payload.get("areaId", ""), service.requests.values()) if item["requestId"] in request_ids]
                stops = [{"requestId": item["requestId"], "latitude": item["approximateLatitude"], "longitude": item["approximateLongitude"]} for item in opportunities]
                return self._send_json(plan_preview({"latitude": 28.6800, "longitude": 77.1500}, stops))
            if path == "/api/collection-requests":
                household_id = payload["householdId"]
                active = [r for r in service.requests.values() if r.household_id == household_id and r.status in (RequestStatus.PENDING, RequestStatus.ACCEPTED)]
                if active:
                    raise ValueError("household already has an active collection request")
                material_ids = [m.id for m in service.materials.values() if m.source_id == household_id and m.status == "available"]
                request = service.create_collection_request(household_id, material_ids)
                return self._send_json(_request_json(request), 201)
            if path.startswith("/api/collection-requests/") and path.endswith("/accept"):
                request = service.accept_request(payload["kabadiwalaId"], path.split("/")[-2])
                return self._send_json(_request_json(request))
            if path.startswith("/api/collection-requests/") and path.endswith("/reject"):
                request = service.reject_request(payload["kabadiwalaId"], path.split("/")[-2])
                return self._send_json(_request_json(request))
            if path.startswith("/api/collection-requests/") and path.endswith("/collect"):
                request = service.collect_request(payload["kabadiwalaId"], path.split("/")[-2])
                return self._send_json(_request_json(request))
            if path == "/api/recycler-requirements":
                requirement = service.create_requirement(payload["recyclerId"], payload["materialType"], float(payload["requiredQuantityKg"]), float(payload.get("minimumQuantityKg", 0)))
                return self._send_json(_requirement_json(requirement), 201)
            if path == "/api/recyclers/recycler_1/profile":
                profile = service.profiles.get(payload["recyclerId"])
                if not profile or profile.role != Role.RECYCLER:
                    raise ValueError("recycler profile not found")
                profile.name = str(payload.get("name", profile.name)).strip() or profile.name
                profile.locality = str(payload.get("locality", getattr(profile, "locality", "Delhi"))).strip() or "Delhi"
                profile.contact = str(payload.get("contact", getattr(profile, "contact", ""))).strip()
                return self._send_json({"id": profile.id, "role": profile.role.value, "name": profile.name, "locality": profile.locality, "contact": profile.contact})
            if path == "/api/bookings":
                booking = service.book_material(payload["recyclerId"], payload["requirementId"], payload["kabadiwalaId"], float(payload["quantityKg"]))
                return self._send_json(_booking_json(booking), 201)
            if path.startswith("/api/bookings/") and path.endswith("/confirm"):
                booking = service.confirm_booking(payload["recyclerId"], path.split("/")[-2])
                return self._send_json(_booking_json(booking))
            return self._send_json({"error": {"code": "NOT_FOUND", "message": "endpoint not found"}}, 404)
        except ClientError as exc:
            self._send_json({"error": {"code": "AWS_SERVICE_ERROR", "message": exc.response.get("Error", {}).get("Message", "AWS request failed")}}, 503)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            self._send_json({"error": {"code": "INVALID_REQUEST", "message": str(exc)}}, 400)

    def do_PUT(self):
        self._persist_after_response = True
        path = urlparse(self.path).path.rstrip("/")
        payload = self._body()
        try:
            if path.startswith("/api/materials/"):
                material = service.update_material(payload["userId"], path.split("/")[-1], float(payload["quantityKg"]))
                return self._send_json(_material_json(material))
            return self._send_json({"error": {"code": "NOT_FOUND", "message": "endpoint not found"}}, 404)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            self._send_json({"error": {"code": "INVALID_REQUEST", "message": str(exc)}}, 400)

    def do_DELETE(self):
        self._persist_after_response = True
        path = urlparse(self.path).path.rstrip("/")
        try:
            if path.startswith("/api/materials/"):
                material_id = path.split("/")[-1]
                service.remove_material("household_1", material_id)
                if repository is not None:
                    repository.delete_material(material_id)
                return self._send_json({"ok": True})
            return self._send_json({"error": {"code": "NOT_FOUND", "message": "endpoint not found"}}, 404)
        except ValueError as exc:
            self._send_json({"error": {"code": "INVALID_REQUEST", "message": str(exc)}}, 400)


def _material_json(material) -> dict:
    return {"id": material.id, "materialType": material.material_type, "quantityKg": material.quantity_kg, "estimatedValueInr": round(material.estimated_value), "status": material.status}


def _mock_classification(filename: str) -> dict:
    """Deterministic local stand-in for Rekognition Custom Labels."""
    name = filename.lower()
    guesses = [("cardboard", 0.91), ("paper", 0.88), ("aluminium", 0.9), ("glass", 0.86), ("pet", 0.92)]
    material, confidence = next(((label, score) for label, score in guesses if label in name or (label == "pet" and "plastic" in name)), ("other", 0.42))
    return {"detections": [{"materialType": material, "confidence": confidence, "requiresConfirmation": confidence < 0.8 or material == "other"}], "mode": "mock"}


def _request_json(request) -> dict:
    if request is None:
        return None
    region = area_service.area_for(request.latitude, request.longitude)
    return {"id": request.id, "status": request.status.value, "estimatedValueInr": round(request.estimated_value), "quantityByType": request.quantity_by_type, "assignedKabadiwalaId": request.assigned_kabadiwala_id, "region": region.name, "regionId": region.id}


def _requirement_json(requirement) -> dict:
    return {"id": requirement.id, "materialType": requirement.material_type, "requiredQuantityKg": requirement.required_quantity_kg, "minimumQuantityKg": requirement.minimum_quantity_kg, "fulfilledQuantityKg": requirement.fulfilled_quantity_kg, "status": requirement.status.value}


def _booking_json(booking) -> dict:
    return {"id": booking.id, "status": booking.status.value, "materialType": booking.material_type, "quantityKg": booking.quantity_kg, "materialIds": booking.material_ids, "requirementId": booking.requirement_id}


def _available_json(item) -> dict:
    holder = service.profiles.get(item["kabadiwala_id"])
    region = area_service.area_for(holder.latitude, holder.longitude) if holder else None
    return {"kabadiwalaId": item["kabadiwala_id"], "kabadiwalaName": holder.name if holder else item["kabadiwala_id"], "region": region.name if region else "Delhi", "regionId": region.id if region else None, "materialType": item["material_type"], "quantityKg": item["quantity_kg"]}


def _inventory(holder_id: str) -> list[dict]:
    grouped = {}
    for material in service.materials.values():
        if material.current_holder_id == holder_id and material.status == "collected":
            grouped[material.material_type] = grouped.get(material.material_type, 0) + material.quantity_kg
    return [{"materialType": material_type, "quantityKg": round(quantity, 3)} for material_type, quantity in grouped.items()]


def _household_inventory(household_id: str) -> list[dict]:
    grouped = {}
    for material in service.materials.values():
        if material.source_id == household_id and material.status in {"available", "requested"}:
            grouped.setdefault(material.material_type, {"quantityKg": 0, "estimatedValueInr": 0})
            grouped[material.material_type]["quantityKg"] += material.quantity_kg
            grouped[material.material_type]["estimatedValueInr"] += material.estimated_value
    return [{"materialType": t, "quantityKg": round(v["quantityKg"], 3), "estimatedValueInr": round(v["estimatedValueInr"])} for t, v in grouped.items()]


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    print(f"Starting recovery demo at http://localhost:{port}")
    ThreadingHTTPServer(("0.0.0.0", port), DemoHandler).serve_forever()
