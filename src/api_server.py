"""Dependency-free local API and demo server.

Run with: ``python3 -m src.api_server``
"""

from __future__ import annotations

import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

try:
    from botocore.exceptions import ClientError
except ImportError:  # boto3 is optional for local mock mode
    class ClientError(Exception):
        pass

from .area_opportunities import AreaOpportunityService, DELHI_AREAS
from .image_storage import create_upload, delete_upload
from .route_planner import plan_preview
from .recovery_domain import Profile, RecoveryService, RequestStatus, RequirementStatus, Role, new_id


ROOT = Path(__file__).resolve().parent.parent


def build_state(with_demo_requests: bool = False) -> tuple[RecoveryService, AreaOpportunityService]:
    service = RecoveryService()
    area_service = AreaOpportunityService()
    areas = {area.name: area for area in DELHI_AREAS}
    household_names = [
        "Asha Verma", "Bharat Singh", "Chitra Rao", "Deepak Sharma", "Esha Mehta", "Farhan Khan",
        "Gauri Nair", "Harish Gupta", "Ishita Jain", "Jatin Kapoor", "Kavita Das", "Lokesh Yadav",
        "Meena Iyer", "Nikhil Batra", " पूजा Shah", "Ravi Menon", "Sara Thomas", "Tarun Bose",
        "Uma Sethi", "Vikram Joshi", "Wafa Ali", "Yash Malhotra", "Zoya Sen", "Anil Roy",
        "Aarav Kapoor", "Bhavna Malik", "Charu Bansal", "Dev Arora", "Ekta Suri", "Faisal Khan",
        "Gia Khanna", "Himanshu Jain", "Ira Mehta", "Jai Bhatia", "Kiran Sood", "Leena Paul",
        "Manav Kohli", "Naina Seth", "Om Prakash", "Pari Nanda", "Rohan Gill", "Simran Kaur",
        "Tanya Bedi", "Uday Chopra", "Vani Rao",
    ]
    household_regions = [area.name for area in DELHI_AREAS]
    for index, name in enumerate(household_names, start=1):
        area = areas[household_regions[(index - 1) % len(household_regions)]]
        latitude, longitude = area.center_latitude, area.center_longitude
        if index == 1:
            latitude, longitude = 28.7042, 77.1024
        service.add_profile(Profile(f"household_{index}", Role.HOUSEHOLD, name, latitude, longitude, locality=area.name, is_demo=True))

    kabadiwalas = [
        ("Ramesh Recovery", "West", {"pet", "cardboard", "paper", "aluminium", "glass", "wood"}),
        ("Farida Collection", "West", {"pet", "cardboard", "paper", "glass"}),
        ("Suresh Kabadi Network", "Central", {"pet", "paper", "aluminium", "glass"}),
        ("Lakshmi Materials", "South", {"pet", "cardboard", "paper", "aluminium", "wood"}),
        ("Yamuna Circular Collectives", "North East", {"pet", "cardboard", "paper", "aluminium", "glass"}),
        ("Green Lane Recovery", "South West", {"pet", "cardboard", "paper", "aluminium", "wood"}),
    ]
    for index, (name, region, materials) in enumerate(kabadiwalas, start=1):
        area = areas[region]
        service.add_profile(Profile(f"kabadiwala_{index}", Role.KABADIWALA, name, area.center_latitude, area.center_longitude, 25, materials, 4.5 + index / 10, 1 + index / 20, locality=region, is_demo=True))

    recycler_names = ["GreenCycle Delhi", "ReForm Plastics", "Nayi Disha Paper", "MetalLoop India", "GlassRoot Works", "Urban Fibre Co", "Bharat Materials", "Circular Carton", "CleanCast Industries"]
    recycler_materials = ["pet", "paper", "cardboard", "aluminium", "glass", "paper", "pet", "cardboard", "aluminium"]
    for index, name in enumerate(recycler_names, start=1):
        area = DELHI_AREAS[(index + 2) % len(DELHI_AREAS)]
        service.add_profile(Profile(f"recycler_{index}", Role.RECYCLER, name, area.center_latitude, area.center_longitude, locality=area.name, contact=f"materials{index}@demo-recycler.in", is_demo=True))

    material_types = ["pet", "cardboard", "paper", "aluminium", "glass", "wood"]
    for index in range(1, 25):
        household_id = f"household_{index}"
        first_quantity = 4 if index == 1 else round(1.5 + (index % 7) * 0.75, 2)
        second_quantity = 2 if index == 1 else round(2 + (index % 5) * 0.5, 2)
        first = service.add_material(household_id, material_types[(index - 1) % len(material_types)], first_quantity)
        service.add_material(household_id, material_types[index % len(material_types)], second_quantity)
        if with_demo_requests and index > 1:
            request = service.create_collection_request(household_id, [first.id])
            if index in {4, 8, 16, 20}:
                service.accept_request(f"kabadiwala_{((index // 2) % 4) + 1}", request.id)
            if index in {8, 16}:
                service.collect_request(request.assigned_kabadiwala_id, request.id)

    # Keep the map useful as a demo: every displayed Delhi region should have
    # at least four open opportunities, regardless of the regular seed mix.
    if with_demo_requests:
        open_by_area = {area.id: 0 for area in DELHI_AREAS}
        for request in service.requests.values():
            if request.status != RequestStatus.PENDING:
                continue
            area = area_service.area_for(request.latitude, request.longitude)
            if area:
                open_by_area[area.id] = open_by_area.get(area.id, 0) + 1
        for area_index, area in enumerate(DELHI_AREAS):
            target_open = 3 + ((area_index * 7 + 1) % 4)  # deterministic 3–6 range
            slot = 1
            while open_by_area.get(area.id, 0) < target_open:
                profile_id = f"demo_household_{area.id}_{slot}"
                if profile_id in service.profiles:
                    slot += 1
                    continue
                profile = Profile(profile_id, Role.HOUSEHOLD, f"Demo household · {area.name} {slot}", area.center_latitude, area.center_longitude, locality=area.name, is_demo=True)
                service.add_profile(profile)
                material = service.add_material(profile_id, "pet" if slot % 2 else "cardboard", 2.5 + slot)
                service.create_collection_request(profile_id, [material.id])
                open_by_area[area.id] = open_by_area.get(area.id, 0) + 1
                slot += 1

        # Seed traceable recovered stock for every demo kabadiwala. Each lot
        # follows the same household -> request -> accepted -> collected flow
        # as the live workflow, so it appears in recycler marketplace data.
        stock_materials = ("pet", "cardboard", "paper", "aluminium", "glass", "wood")
        for collector_index in range(1, len(kabadiwalas) + 1):
            collector_id = f"kabadiwala_{collector_index}"
            collector = service.profiles[collector_id]
            area = areas[collector.locality]
            for slot in range(4):
                material_type = stock_materials[(collector_index + slot - 1) % len(stock_materials)]
                household_id = f"demo_stock_household_{collector_index}_{slot + 1}"
                household = Profile(
                    household_id, Role.HOUSEHOLD,
                    f"Demo stock household · {area.name} {slot + 1}",
                    area.center_latitude, area.center_longitude,
                    locality=area.name, is_demo=True,
                )
                service.add_profile(household)
                quantity_kg = round(4 + collector_index + slot * 1.5, 2)
                material = service.add_material(household_id, material_type, quantity_kg)
                request = service.create_collection_request(household_id, [material.id])
                service.accept_request(collector_id, request.id)
                service.collect_request(collector_id, request.id)

    if with_demo_requests:
        for index in range(1, 10):
            requirement = service.create_requirement(f"recycler_{index}", recycler_materials[index - 1], 8 + index * 2, 2)
            if index % 3 == 0:
                requirement.fulfilled_quantity_kg = requirement.required_quantity_kg
                requirement.status = RequirementStatus.FULFILLED
    return service, area_service


def add_demo_collector_activity(service: RecoveryService, collector: Profile, area) -> None:
    """Give a newly-created demo collector a small, clearly-marked workflow."""
    examples = (
        ("pending", [("pet", 8.5)]),
        ("accepted", [("cardboard", 5.0)]),
        ("collected", [("pet", 7.0), ("paper", 4.0), ("aluminium", 2.5)]),
    )
    for stage, materials in examples:
        household_id = f"demo_household_{collector.id}_{stage}"
        household = Profile(
            household_id, Role.HOUSEHOLD, f"Demo household · {area.name} · {stage.title()}",
            area.center_latitude, area.center_longitude, locality=area.name, is_demo=True,
        )
        service.add_profile(household)
        material_ids = [service.add_material(household_id, kind, quantity).id for kind, quantity in materials]
        request = service.create_collection_request(household_id, material_ids)
        if stage in {"accepted", "collected"}:
            service.accept_request(collector.id, request.id)
        if stage == "collected":
            service.collect_request(collector.id, request.id)

    # Reserve a small part of the new demo inventory against an existing open
    # recycler requirement where one is available. This makes the transfer
    # stage visible without inventing an unbacked UI-only metric.
    available_types = {kind for _, materials in examples for kind, _ in materials}
    has_matching_requirement = any(
        requirement.status != RequirementStatus.FULFILLED
        and requirement.material_type in available_types
        and requirement.required_quantity_kg - requirement.fulfilled_quantity_kg >= max(requirement.minimum_quantity_kg, 2.0)
        for requirement in service.requirements.values()
    )
    if not has_matching_requirement:
        recycler = next((profile for profile in service.profiles.values() if profile.role == Role.RECYCLER), None)
        if recycler:
            service.create_requirement(recycler.id, "pet", 10.0, 2.0)
    for requirement in service.requirements.values():
        if requirement.status == RequirementStatus.FULFILLED or requirement.material_type not in available_types:
            continue
        remaining = requirement.required_quantity_kg - requirement.fulfilled_quantity_kg
        if remaining >= max(requirement.minimum_quantity_kg, 2.0):
            try:
                service.book_material(requirement.recycler_id, requirement.id, collector.id, 2.0)
                break
            except ValueError:
                continue


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


def refresh_persisted_state() -> None:
    """Reload the shared demo state before a Lambda invocation.

    Lambda execution environments keep module globals warm. Without a refresh,
    a request routed to another warm environment can still hold the snapshot
    from before a newly-created profile or material was written to DynamoDB.
    That made the frontend correctly-created profile look missing immediately
    after the redirect.
    """
    global service, area_service
    if repository is None:
        return
    service, area_service = build_state(with_demo_requests=False)
    repository.load_service(service)


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
            parts = [part for part in path.split("/") if part]
            if path == "/api/demo/areas" or (len(parts) == 4 and parts[:2] == ["api", "kabadiwalas"] and parts[3] == "areas"):
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
            if len(parts) == 6 and parts[:2] == ["api", "kabadiwalas"] and parts[3] == "areas" and parts[5] == "opportunities":
                service._require_role(parts[2], Role.KABADIWALA)
                area_id = parts[4]
                return self._send_json({"opportunities": area_service.opportunities(area_id, service.requests.values())})
            if len(parts) == 4 and parts[:2] == ["api", "kabadiwalas"] and parts[3] in {"inventory", "requests", "metrics", "profile"}:
                kabadiwala_id = parts[2]
                service._require_role(kabadiwala_id, Role.KABADIWALA)
                resource = parts[3]
                if resource == "inventory":
                    return self._send_json({"inventory": _inventory(kabadiwala_id)})
                if resource == "metrics":
                    return self._send_json(service.kabadiwala_metrics(kabadiwala_id))
                if resource == "profile":
                    return self._send_json(service.profile_summary(kabadiwala_id))
                requests = [
                    r for r in service.requests.values()
                    if r.status == RequestStatus.PENDING
                    or r.assigned_kabadiwala_id == kabadiwala_id
                ]
                # Live user requests take priority over seeded demo activity;
                # newest requests remain first within each group.
                requests.sort(key=lambda r: (r.is_demo, r.created_at))
                return self._send_json({"requests": [_request_json(r) for r in requests]})
            if len(parts) == 4 and parts[:2] == ["api", "households"] and parts[3] in {"inventory", "collection-request", "metrics", "profile"}:
                household_id = parts[2]
                service._require_role(household_id, Role.HOUSEHOLD)
                resource = parts[3]
                if resource == "inventory":
                    return self._send_json({"inventory": _household_inventory(household_id)})
                if resource == "metrics":
                    return self._send_json(service.household_metrics(household_id))
                if resource == "profile":
                    return self._send_json(service.profile_summary(household_id))
                request = next((r for r in reversed(list(service.requests.values())) if r.household_id == household_id), None)
                request_data = _request_json(request) if request else None
                if request_data:
                    region = area_service.area_for(request.latitude, request.longitude)
                    request_data["region"] = region.name
                    request_data["regionId"] = region.id
                return self._send_json({"request": request_data})
            if len(parts) == 4 and parts[:2] == ["api", "recyclers"] and parts[3] in {"available-material", "requirements", "bookings", "metrics", "profile"}:
                recycler_id = parts[2]
                service._require_role(recycler_id, Role.RECYCLER)
                resource = parts[3]
                if resource == "available-material":
                    return self._send_json({"availableMaterial": [_available_json(item) for item in service.available_material(recycler_id)]})
                if resource == "requirements":
                    return self._send_json({"requirements": [_requirement_json(r) for r in service.requirements.values() if r.recycler_id == recycler_id]})
                if resource == "bookings":
                    return self._send_json({"bookings": [_booking_json(b) for b in service.bookings.values() if b.recycler_id == recycler_id]})
                if resource == "metrics":
                    return self._send_json(service.recycler_metrics(recycler_id))
                return self._send_json(service.profile_summary(recycler_id))
            if len(parts) == 4 and parts[:2] == ["api", "kabadiwalas"] and parts[3] == "route":
                raise ValueError("route planning requires POST")
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
                if repository is not None:
                    repository.clear()
                service, area_service = build_state(with_demo_requests=True)
                return self._send_json({"ok": True})
            if path == "/api/demo/profiles":
                role = Role(payload["role"])
                name = str(payload.get("name", "")).strip()
                locality = str(payload.get("locality", "")).strip()
                if not name or not locality:
                    raise ValueError("name and locality are required")
                area = next((item for item in DELHI_AREAS if item.name == locality), None)
                if area is None:
                    raise ValueError("choose a valid Delhi locality")
                profile_id = str(payload.get("id", "")).strip()
                profile = service.profiles.get(profile_id) if profile_id else None
                if profile and profile.role != role:
                    raise ValueError("profile role cannot be changed")
                created = not profile
                if not profile:
                    profile_id = new_id(role.value)
                    if role == Role.HOUSEHOLD:
                        profile = Profile(profile_id, role, name, area.center_latitude, area.center_longitude, locality=locality, is_demo=False)
                    elif role == Role.KABADIWALA:
                        profile = Profile(profile_id, role, name, area.center_latitude, area.center_longitude, 25, {"pet", "cardboard", "paper", "aluminium", "glass", "wood"}, 4.5, 1.0, locality=locality, is_demo=False)
                    else:
                        profile = Profile(profile_id, role, name, area.center_latitude, area.center_longitude, locality=locality, contact=str(payload.get("contact", "")).strip(), is_demo=False)
                    service.add_profile(profile)
                    if role == Role.KABADIWALA:
                        add_demo_collector_activity(service, profile, area)
                else:
                    profile.name = name
                    profile.locality = locality
                    profile.latitude = area.center_latitude
                    profile.longitude = area.center_longitude
                    if role == Role.RECYCLER and "contact" in payload:
                        profile.contact = str(payload.get("contact", "")).strip()
                return self._send_json(service.profile_summary(profile.id), 201 if created else 200)
            if path == "/api/materials":
                material = service.add_material(payload["userId"], payload["materialType"], float(payload["quantityKg"]))
                return self._send_json(_material_json(material), 201)
            if path == "/api/classify-image":
                # Keep the demo path local and free: a configured model ARN must
                # never silently turn a demo photo into a billable inference.
                return self._send_json(_mock_classification(payload.get("filename", "")))
            if path == "/api/image-upload":
                content_type = payload.get("contentType")
                filename = payload.get("filename", "image")
                if content_type not in {"image/jpeg", "image/png"}:
                    raise ValueError("only JPG and PNG images are supported")
                return self._send_json(create_upload(os.getenv("ML_S3_BUCKET", "environmental-recovery-ml-132218943520"), content_type, filename))
            if len([part for part in path.split("/") if part]) == 4 and path.startswith("/api/kabadiwalas/") and path.endswith("/route"):
                collector_id = path.split("/")[3]
                service._require_role(collector_id, Role.KABADIWALA)
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
            if path.startswith("/api/recyclers/") and path.endswith("/profile"):
                path_recycler_id = path.split("/")[3]
                profile = service.profiles.get(payload["recyclerId"])
                if path_recycler_id != payload["recyclerId"] or not profile or profile.role != Role.RECYCLER:
                    raise ValueError("recycler profile not found")
                profile.name = str(payload.get("name", profile.name)).strip() or profile.name
                profile.locality = str(payload.get("locality", getattr(profile, "locality", "Delhi"))).strip() or "Delhi"
                profile.contact = str(payload.get("contact", getattr(profile, "contact", ""))).strip()
                return self._send_json(service.profile_summary(profile.id))
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
        payload = self._body()
        try:
            if path.startswith("/api/materials/"):
                material_id = path.split("/")[-1]
                service.remove_material(payload["userId"], material_id)
                if repository is not None:
                    repository.delete_material(material_id)
                return self._send_json({"ok": True})
            return self._send_json({"error": {"code": "NOT_FOUND", "message": "endpoint not found"}}, 404)
        except ValueError as exc:
            self._send_json({"error": {"code": "INVALID_REQUEST", "message": str(exc)}}, 400)


def _material_json(material) -> dict:
    return {"id": material.id, "materialType": material.material_type, "quantityKg": material.quantity_kg, "estimatedValueInr": round(material.estimated_value), "status": material.status}


def _mock_classification(filename: str) -> dict:
    """Return a clearly marked, deterministic demo suggestion without vision."""
    name = filename.lower()
    materials = ["pet", "cardboard", "paper", "aluminium", "glass"]
    material = next((label for label in materials if label in name or (label == "pet" and "plastic" in name)), None)
    if material is None:
        material = materials[sum(name.encode("utf-8")) % len(materials)] if name else "paper"
    return {"detections": [{"materialType": material, "requiresConfirmation": True}], "mode": "demo"}


def _request_json(request) -> dict:
    if request is None:
        return None
    region = area_service.area_for(request.latitude, request.longitude)
    return {"id": request.id, "status": request.status.value, "isDemo": request.is_demo, "estimatedValueInr": round(request.estimated_value), "quantityByType": request.quantity_by_type, "assignedKabadiwalaId": request.assigned_kabadiwala_id, "region": region.name, "regionId": region.id}


def _requirement_json(requirement) -> dict:
    return {"id": requirement.id, "materialType": requirement.material_type, "requiredQuantityKg": requirement.required_quantity_kg, "minimumQuantityKg": requirement.minimum_quantity_kg, "fulfilledQuantityKg": requirement.fulfilled_quantity_kg, "status": requirement.status.value}


def _booking_json(booking) -> dict:
    return {"id": booking.id, "status": booking.status.value, "materialType": booking.material_type, "quantityKg": booking.quantity_kg, "materialIds": booking.material_ids, "requirementId": booking.requirement_id}


def _available_json(item) -> dict:
    holder = service.profiles.get(item["kabadiwala_id"])
    region = area_service.area_for(holder.latitude, holder.longitude) if holder else None
    return {"kabadiwalaId": item["kabadiwala_id"], "kabadiwalaName": holder.name if holder else item["kabadiwala_id"], "region": region.name if region else "Delhi", "regionId": region.id if region else None, "materialType": item["material_type"], "quantityKg": item["quantity_kg"], "isDemo": bool(item.get("is_demo", True))}


def _inventory(holder_id: str) -> list[dict]:
    grouped = {}
    for material in service.materials.values():
        if material.current_holder_id != holder_id or material.status not in {"collected", "reserved"}:
            continue
        source = service.profiles.get(material.source_id)
        key = (material.material_type, material.status, bool(source and source.is_demo))
        grouped[key] = grouped.get(key, 0) + material.quantity_kg
    return [
        {"materialType": material_type, "quantityKg": round(quantity, 3), "status": status, "isDemo": is_demo}
        for (material_type, status, is_demo), quantity in grouped.items()
    ]


def _household_inventory(household_id: str) -> list[dict]:
    # Keep record IDs in the response: the household UI edits/deletes each
    # material record individually, so grouping by type makes those actions
    # target an undefined ID (and the API then reports "material not found").
    return [
        {
            "id": material.id,
            "materialType": material.material_type,
            "quantityKg": round(material.quantity_kg, 3),
            "estimatedValueInr": round(material.estimated_value),
            "status": material.status,
        }
        for material in service.materials.values()
        if material.source_id == household_id and material.status in {"available", "requested"}
    ]


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    print(f"Starting recovery demo at http://localhost:{port}")
    ThreadingHTTPServer(("0.0.0.0", port), DemoHandler).serve_forever()
