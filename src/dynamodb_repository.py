"""DynamoDB persistence adapter for the recovery domain.

The adapter is intentionally separate from the domain service so local demos
can continue using in-memory state while the API is migrated incrementally.
"""

from __future__ import annotations

from dataclasses import asdict
from decimal import Decimal
from enum import Enum
from typing import Any

from .recovery_domain import (
    Booking,
    BookingStatus,
    CollectionRequest,
    MaterialRecord,
    Profile,
    RecyclerRequirement,
    RequirementStatus,
    RequestStatus,
    Role,
)


def _native(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, set):
        return sorted(value)
    if isinstance(value, dict):
        return {key: _native(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_native(item) for item in value]
    return value


class DynamoRecoveryRepository:
    """Single-table repository using the access patterns in docs/dynamodb_schema.md."""

    def __init__(self, table_name: str = "environmental-recovery", region_name: str = "ap-south-1", resource=None):
        if resource is None:
            import boto3

            resource = boto3.resource("dynamodb", region_name=region_name)
        self.table = resource.Table(table_name)

    def put_profile(self, profile) -> None:
        item = _native(asdict(profile))
        item.update(pk=f"PROFILE#{profile.id}", sk="PROFILE", gsi1pk=f"ROLE#{profile.role.value}", gsi1sk=profile.id)
        self.table.put_item(Item=item)

    def put_material(self, material) -> None:
        item = _native(asdict(material))
        item.update(
            pk=f"MATERIAL#{material.id}", sk="MATERIAL",
            gsi1pk=f"OWNER#{material.current_holder_id}", gsi1sk=f"{material.status}#{material.id}",
            gsi2pk=f"MATERIAL#{material.material_type}#{material.status}", gsi2sk=material.id,
        )
        self.table.put_item(Item=item)

    def put_request(self, request) -> None:
        item = _native(asdict(request))
        item.update(
            pk=f"REQUEST#{request.id}", sk="REQUEST",
            gsi1pk=f"HOUSEHOLD#{request.household_id}", gsi1sk=f"{request.created_at}#{request.id}",
            gsi2pk=f"REQUEST_STATUS#{request.status.value}", gsi2sk=f"{request.created_at}#{request.id}",
        )
        self.table.put_item(Item=item)

    def put_requirement(self, requirement) -> None:
        item = _native(asdict(requirement))
        item.update(pk=f"REQUIREMENT#{requirement.id}", sk="REQUIREMENT", gsi1pk=f"RECYCLER#{requirement.recycler_id}", gsi1sk=f"{requirement.status.value}#{requirement.id}")
        self.table.put_item(Item=item)

    def put_booking(self, booking) -> None:
        item = _native(asdict(booking))
        item.update(pk=f"BOOKING#{booking.id}", sk="BOOKING", gsi1pk=f"RECYCLER#{booking.recycler_id}", gsi1sk=f"{booking.created_at}#{booking.id}")
        self.table.put_item(Item=item)

    def delete_material(self, material_id: str) -> None:
        self.table.delete_item(Key={"pk": f"MATERIAL#{material_id}", "sk": "MATERIAL"})

    def clear(self) -> None:
        """Delete all records from this demo table before a deterministic reseed."""
        response = self.table.scan(ProjectionExpression="pk, sk")
        items = response.get("Items", [])
        while response.get("LastEvaluatedKey"):
            response = self.table.scan(ProjectionExpression="pk, sk", ExclusiveStartKey=response["LastEvaluatedKey"])
            items.extend(response.get("Items", []))
        with self.table.batch_writer() as batch:
            for item in items:
                batch.delete_item(Key={"pk": item["pk"], "sk": item["sk"]})

    def save_service(self, service) -> None:
        """Batch-save the current domain snapshot; useful during migration/backfill."""
        with self.table.batch_writer(overwrite_by_pkeys=["pk", "sk"]) as batch:
            for profile in service.profiles.values():
                item = _native(asdict(profile))
                item.update(pk=f"PROFILE#{profile.id}", sk="PROFILE", gsi1pk=f"ROLE#{profile.role.value}", gsi1sk=profile.id)
                batch.put_item(Item=item)
            for material in service.materials.values():
                item = _native(asdict(material))
                item.update(pk=f"MATERIAL#{material.id}", sk="MATERIAL", gsi1pk=f"OWNER#{material.current_holder_id}", gsi1sk=f"{material.status}#{material.id}", gsi2pk=f"MATERIAL#{material.material_type}#{material.status}", gsi2sk=material.id)
                batch.put_item(Item=item)
            for request in service.requests.values():
                item = _native(asdict(request))
                item.update(pk=f"REQUEST#{request.id}", sk="REQUEST", gsi1pk=f"HOUSEHOLD#{request.household_id}", gsi1sk=f"{request.created_at}#{request.id}", gsi2pk=f"REQUEST_STATUS#{request.status.value}", gsi2sk=f"{request.created_at}#{request.id}")
                batch.put_item(Item=item)
            for requirement in service.requirements.values():
                self.put_requirement(requirement)
            for booking in service.bookings.values():
                self.put_booking(booking)

    def load_service(self, service) -> None:
        """Restore persisted entities into an existing RecoveryService."""
        response = self.table.scan()
        items = response.get("Items", [])
        while response.get("LastEvaluatedKey"):
            response = self.table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
            items.extend(response.get("Items", []))
        for item in items:
            kind = item.get("sk")
            if kind == "PROFILE":
                service.profiles[item["id"]] = Profile(item["id"], Role(item["role"]), item["name"], float(item["latitude"]), float(item["longitude"]), float(item.get("service_radius_km", 0)), set(item.get("supported_materials", [])), float(item.get("demo_rating", 0)), float(item.get("payout_index", 1)), item.get("locality", "Delhi"), item.get("contact", ""))
            elif kind == "MATERIAL":
                service.materials[item["id"]] = MaterialRecord(item["id"], item["material_type"], float(item["quantity_kg"]), float(item["estimated_value"]), item["source_id"], item["current_holder_id"], item.get("status", "available"), item.get("destination_id"), item["created_at"], item["updated_at"])
            elif kind == "REQUEST":
                service.requests[item["id"]] = CollectionRequest(item["id"], item["household_id"], list(item["material_ids"]), {key: float(value) for key, value in item["quantity_by_type"].items()}, float(item["estimated_value"]), float(item["latitude"]), float(item["longitude"]), RequestStatus(item["status"]), item.get("assigned_kabadiwala_id"), item["created_at"], item["updated_at"])
            elif kind == "REQUIREMENT":
                service.requirements[item["id"]] = RecyclerRequirement(item["id"], item["recycler_id"], item["material_type"], float(item["required_quantity_kg"]), float(item.get("minimum_quantity_kg", 0)), float(item.get("fulfilled_quantity_kg", 0)), RequirementStatus(item["status"]), item["created_at"], item["updated_at"])
            elif kind == "BOOKING":
                service.bookings[item["id"]] = Booking(item["id"], item["recycler_id"], item["kabadiwala_id"], item["requirement_id"], item["material_type"], float(item["quantity_kg"]), list(item.get("material_ids", [])), BookingStatus(item["status"]), item["created_at"], item["updated_at"])
