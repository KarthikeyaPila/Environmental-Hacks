"""Core recovery-network business logic.

The module deliberately has no web framework or database dependency.  Its service
methods are the contract that an HTTP/Lambda adapter can expose later.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from math import asin, cos, radians, sin, sqrt
from typing import Dict, Iterable, Optional
from uuid import uuid4


class Role(str, Enum):
    HOUSEHOLD = "household"
    KABADIWALA = "kabadiwala"
    RECYCLER = "recycler"


class RequestStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COLLECTED = "collected"
    CANCELLED = "cancelled"


class RequirementStatus(str, Enum):
    OPEN = "open"
    PARTIALLY_FULFILLED = "partially_fulfilled"
    FULFILLED = "fulfilled"


class BookingStatus(str, Enum):
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


@dataclass(frozen=True)
class MaterialRate:
    material_type: str
    rate_per_kg: float


@dataclass
class Profile:
    id: str
    role: Role
    name: str
    latitude: float
    longitude: float
    service_radius_km: float = 0.0
    supported_materials: set[str] = field(default_factory=set)
    demo_rating: float = 0.0
    payout_index: float = 1.0
    locality: str = "Delhi"
    contact: str = ""


@dataclass
class MaterialRecord:
    id: str
    material_type: str
    quantity_kg: float
    estimated_value: float
    source_id: str
    current_holder_id: str
    status: str = "available"
    destination_id: Optional[str] = None
    created_at: str = field(default_factory=now)
    updated_at: str = field(default_factory=now)


@dataclass
class CollectionRequest:
    id: str
    household_id: str
    material_ids: list[str]
    quantity_by_type: dict[str, float]
    estimated_value: float
    latitude: float
    longitude: float
    status: RequestStatus = RequestStatus.PENDING
    assigned_kabadiwala_id: Optional[str] = None
    created_at: str = field(default_factory=now)
    updated_at: str = field(default_factory=now)


@dataclass
class RecyclerRequirement:
    id: str
    recycler_id: str
    material_type: str
    required_quantity_kg: float
    fulfilled_quantity_kg: float = 0.0
    status: RequirementStatus = RequirementStatus.OPEN
    created_at: str = field(default_factory=now)
    updated_at: str = field(default_factory=now)


@dataclass
class Booking:
    id: str
    recycler_id: str
    kabadiwala_id: str
    requirement_id: str
    material_type: str
    quantity_kg: float
    material_ids: list[str] = field(default_factory=list)
    status: BookingStatus = BookingStatus.CONFIRMED
    created_at: str = field(default_factory=now)
    updated_at: str = field(default_factory=now)


class RecoveryService:
    """Use-case service for the household-to-recycler material lifecycle."""

    def __init__(self, rates: Optional[Iterable[MaterialRate]] = None) -> None:
        self.profiles: Dict[str, Profile] = {}
        self.materials: Dict[str, MaterialRecord] = {}
        self.requests: Dict[str, CollectionRequest] = {}
        self.requirements: Dict[str, RecyclerRequirement] = {}
        self.bookings: Dict[str, Booking] = {}
        self.rates = {r.material_type: r.rate_per_kg for r in (rates or default_rates())}

    def add_profile(self, profile: Profile) -> Profile:
        self._validate_coordinates(profile.latitude, profile.longitude)
        self.profiles[profile.id] = profile
        return profile

    def add_material(self, household_id: str, material_type: str, quantity_kg: float) -> MaterialRecord:
        self._require_role(household_id, Role.HOUSEHOLD)
        material_type = self._normalize_material(material_type)
        self._positive(quantity_kg, "quantity_kg")
        record = MaterialRecord(
            id=new_id("mat"), material_type=material_type, quantity_kg=quantity_kg,
            estimated_value=round(quantity_kg * self.rates.get(material_type, 0.0), 2),
            source_id=household_id, current_holder_id=household_id,
        )
        self.materials[record.id] = record
        pending = next((r for r in self.requests.values() if r.household_id == household_id and r.status == RequestStatus.PENDING), None)
        if pending:
            record.status = "requested"
            pending.material_ids.append(record.id)
            pending.quantity_by_type[material_type] = pending.quantity_by_type.get(material_type, 0) + quantity_kg
            pending.estimated_value += record.estimated_value
            pending.updated_at = now()
        return record

    def update_material(self, household_id: str, material_id: str, quantity_kg: float) -> MaterialRecord:
        self._require_role(household_id, Role.HOUSEHOLD)
        record = self._get_material(material_id)
        if record.source_id != household_id or record.status != "available":
            raise ValueError("only available household material can be edited")
        self._positive(quantity_kg, "quantity_kg")
        record.quantity_kg = quantity_kg
        record.estimated_value = round(quantity_kg * self.rates.get(record.material_type, 0.0), 2)
        record.updated_at = now()
        return record

    def remove_material(self, household_id: str, material_id: str) -> None:
        self._require_role(household_id, Role.HOUSEHOLD)
        record = self._get_material(material_id)
        if record.source_id != household_id or record.status != "available":
            raise ValueError("only available household material can be removed")
        del self.materials[material_id]

    def create_collection_request(self, household_id: str, material_ids: list[str]) -> CollectionRequest:
        household = self._require_role(household_id, Role.HOUSEHOLD)
        if not material_ids:
            raise ValueError("at least one material is required")
        records = [self._get_material(mid) for mid in material_ids]
        if any(r.source_id != household_id or r.current_holder_id != household_id for r in records):
            raise ValueError("all materials must belong to the household and be available")
        quantity_by_type: dict[str, float] = {}
        for record in records:
            quantity_by_type[record.material_type] = quantity_by_type.get(record.material_type, 0) + record.quantity_kg
        request = CollectionRequest(
            id=new_id("req"), household_id=household_id, material_ids=material_ids,
            quantity_by_type=quantity_by_type, estimated_value=round(sum(r.estimated_value for r in records), 2),
            latitude=household.latitude, longitude=household.longitude,
        )
        for record in records:
            record.status = "requested"
            record.updated_at = now()
        self.requests[request.id] = request
        return request

    def nearby_requests(self, kabadiwala_id: str, radius_km: Optional[float] = None) -> list[dict]:
        collector = self._require_role(kabadiwala_id, Role.KABADIWALA)
        radius = radius_km if radius_km is not None else collector.service_radius_km
        self._positive(radius, "radius_km")
        results = []
        for request in self.requests.values():
            if request.status != RequestStatus.PENDING:
                continue
            distance = distance_km(collector.latitude, collector.longitude, request.latitude, request.longitude)
            if distance <= radius and all(t in collector.supported_materials for t in request.quantity_by_type):
                results.append({"request": request, "distance_km": round(distance, 3)})
        return sorted(results, key=lambda item: item["distance_km"])

    def accept_request(self, kabadiwala_id: str, request_id: str) -> CollectionRequest:
        self._require_role(kabadiwala_id, Role.KABADIWALA)
        request = self._get_request(request_id)
        if request.status != RequestStatus.PENDING:
            raise ValueError("only pending requests can be accepted")
        request.status = RequestStatus.ACCEPTED
        request.assigned_kabadiwala_id = kabadiwala_id
        request.updated_at = now()
        return request

    def reject_request(self, kabadiwala_id: str, request_id: str) -> CollectionRequest:
        self._require_role(kabadiwala_id, Role.KABADIWALA)
        request = self._get_request(request_id)
        if request.status != RequestStatus.PENDING:
            raise ValueError("only pending requests can be rejected")
        request.status = RequestStatus.REJECTED
        request.updated_at = now()
        return request

    def collect_request(self, kabadiwala_id: str, request_id: str) -> CollectionRequest:
        self._require_role(kabadiwala_id, Role.KABADIWALA)
        request = self._get_request(request_id)
        if request.status != RequestStatus.ACCEPTED or request.assigned_kabadiwala_id != kabadiwala_id:
            raise ValueError("request must be accepted by this kabadiwala before collection")
        for material_id in request.material_ids:
            material = self._get_material(material_id)
            material.current_holder_id = kabadiwala_id
            material.status = "collected"
            material.updated_at = now()
        request.status = RequestStatus.COLLECTED
        request.updated_at = now()
        return request

    def create_requirement(self, recycler_id: str, material_type: str, quantity_kg: float) -> RecyclerRequirement:
        self._require_role(recycler_id, Role.RECYCLER)
        self._positive(quantity_kg, "quantity_kg")
        requirement = RecyclerRequirement(new_id("need"), recycler_id, self._normalize_material(material_type), quantity_kg)
        self.requirements[requirement.id] = requirement
        return requirement

    def available_material(self, recycler_id: str) -> list[dict]:
        self._require_role(recycler_id, Role.RECYCLER)
        inventory: dict[tuple[str, str], float] = {}
        for material in self.materials.values():
            holder = self.profiles.get(material.current_holder_id)
            if material.status == "collected" and holder and holder.role == Role.KABADIWALA:
                key = (holder.id, material.material_type)
                inventory[key] = inventory.get(key, 0) + material.quantity_kg
        return [{"kabadiwala_id": k, "material_type": t, "quantity_kg": round(q, 3)} for (k, t), q in inventory.items()]

    def book_material(self, recycler_id: str, requirement_id: str, kabadiwala_id: str, quantity_kg: float) -> Booking:
        self._require_role(recycler_id, Role.RECYCLER)
        self._require_role(kabadiwala_id, Role.KABADIWALA)
        self._positive(quantity_kg, "quantity_kg")
        requirement = self.requirements.get(requirement_id)
        if not requirement or requirement.recycler_id != recycler_id:
            raise ValueError("requirement not found for recycler")
        available_records = [m for m in self.materials.values() if m.current_holder_id == kabadiwala_id and m.material_type == requirement.material_type and m.status == "collected"]
        available = sum(m.quantity_kg for m in available_records)
        remaining = requirement.required_quantity_kg - requirement.fulfilled_quantity_kg
        if quantity_kg > min(available, remaining):
            raise ValueError("requested booking exceeds available or required quantity")
        selected_ids = []
        remaining_to_reserve = quantity_kg
        for material in available_records:
            if remaining_to_reserve <= 0:
                break
            material.status = "reserved"
            material.updated_at = now()
            selected_ids.append(material.id)
            remaining_to_reserve -= material.quantity_kg
        booking = Booking(new_id("book"), recycler_id, kabadiwala_id, requirement_id, requirement.material_type, quantity_kg, selected_ids)
        self.bookings[booking.id] = booking
        return booking

    def confirm_booking(self, recycler_id: str, booking_id: str) -> Booking:
        self._require_role(recycler_id, Role.RECYCLER)
        booking = self.bookings.get(booking_id)
        if not booking or booking.recycler_id != recycler_id:
            raise ValueError("booking not found for recycler")
        if booking.status != BookingStatus.CONFIRMED:
            raise ValueError("only confirmed bookings can be completed")
        requirement = self.requirements[booking.requirement_id]
        for material_id in booking.material_ids:
            material = self._get_material(material_id)
            if material.status != "reserved" or material.current_holder_id != booking.kabadiwala_id:
                raise ValueError("reserved material is no longer available")
            material.current_holder_id = recycler_id
            material.destination_id = recycler_id
            material.status = "transferred"
            material.updated_at = now()
        booking.status = BookingStatus.COMPLETED
        booking.updated_at = now()
        requirement.fulfilled_quantity_kg += booking.quantity_kg
        requirement.status = RequirementStatus.FULFILLED if requirement.fulfilled_quantity_kg >= requirement.required_quantity_kg else RequirementStatus.PARTIALLY_FULFILLED
        requirement.updated_at = now()
        return booking

    def contribution(self, household_id: str) -> dict:
        self._require_role(household_id, Role.HOUSEHOLD)
        records = [m for m in self.materials.values() if m.source_id == household_id]
        collected = [m for m in records if m.status in {"collected", "reserved", "transferred"}]
        by_type: dict[str, float] = {}
        for material in collected:
            by_type[material.material_type] = by_type.get(material.material_type, 0) + material.quantity_kg
        return {"material_kg": round(sum(by_type.values()), 3), "by_type": by_type, "collections_completed": sum(r.status == RequestStatus.COLLECTED for r in self.requests.values() if r.household_id == household_id)}

    def household_metrics(self, household_id: str) -> dict:
        self._require_role(household_id, Role.HOUSEHOLD)
        records = [m for m in self.materials.values() if m.source_id == household_id]
        tracked = [m for m in records if m.status in {"collected", "reserved", "transferred"}]
        by_type = _sum_by_type(tracked)
        destinations = sorted({m.destination_id for m in tracked if m.destination_id})
        return {
            "totalRecordedKg": round(sum(m.quantity_kg for m in records), 3),
            "totalCollectedKg": round(sum(m.quantity_kg for m in tracked), 3),
            "byMaterialType": by_type,
            "estimatedValueInr": round(sum(m.estimated_value for m in records)),
            "collectionsCompleted": sum(r.status == RequestStatus.COLLECTED for r in self.requests.values() if r.household_id == household_id),
            "downstreamDestinations": destinations,
        }

    def kabadiwala_metrics(self, kabadiwala_id: str) -> dict:
        profile = self._require_role(kabadiwala_id, Role.KABADIWALA)
        records = [m for m in self.materials.values() if m.current_holder_id == kabadiwala_id and m.status in {"collected", "reserved"}]
        by_type = _sum_by_type(records)
        requests = [r for r in self.requests.values() if r.assigned_kabadiwala_id == kabadiwala_id]
        return {
            "requestsAccepted": sum(r.status in {RequestStatus.ACCEPTED, RequestStatus.COLLECTED} for r in requests),
            "collectionsCompleted": sum(r.status == RequestStatus.COLLECTED for r in requests),
            "totalCollectedKg": round(sum(m.quantity_kg for m in records), 3),
            "estimatedRevenueInr": round(sum(m.estimated_value for m in records)),
            "byMaterialType": by_type,
            "demoRating": profile.demo_rating,
            "payoutIndex": profile.payout_index,
        }

    def profile_summary(self, profile_id: str) -> dict:
        profile = self.profiles.get(profile_id)
        if not profile:
            raise ValueError("profile not found")
        summary = {"id": profile.id, "role": profile.role.value, "name": profile.name, "locality": profile.locality, "contact": profile.contact}
        if profile.role == Role.KABADIWALA:
            summary.update({"demoRating": profile.demo_rating, "payoutIndex": profile.payout_index, "supportedMaterials": sorted(profile.supported_materials)})
        return summary

    def recycler_metrics(self, recycler_id: str) -> dict:
        self._require_role(recycler_id, Role.RECYCLER)
        requirements = [r for r in self.requirements.values() if r.recycler_id == recycler_id]
        bookings = [b for b in self.bookings.values() if b.recycler_id == recycler_id]
        return {
            "requirements": [{"id": r.id, "materialType": r.material_type, "requiredQuantityKg": r.required_quantity_kg, "fulfilledQuantityKg": r.fulfilled_quantity_kg, "status": r.status.value} for r in requirements],
            "fulfilledQuantityKg": round(sum(r.fulfilled_quantity_kg for r in requirements), 3),
            "completedBookings": sum(b.status == BookingStatus.COMPLETED for b in bookings),
            "reservedBookings": sum(b.status == BookingStatus.CONFIRMED for b in bookings),
        }

    def _get_material(self, material_id: str) -> MaterialRecord:
        if material_id not in self.materials:
            raise ValueError("material not found")
        return self.materials[material_id]

    def _get_request(self, request_id: str) -> CollectionRequest:
        if request_id not in self.requests:
            raise ValueError("collection request not found")
        return self.requests[request_id]

    def _require_role(self, profile_id: str, role: Role) -> Profile:
        profile = self.profiles.get(profile_id)
        if not profile or profile.role != role:
            raise ValueError(f"{role.value} profile not found")
        return profile

    @staticmethod
    def _positive(value: float, name: str) -> None:
        if value <= 0:
            raise ValueError(f"{name} must be greater than zero")

    @staticmethod
    def _normalize_material(value: str) -> str:
        value = value.strip().lower()
        if not value:
            raise ValueError("material_type is required")
        return value

    @staticmethod
    def _validate_coordinates(latitude: float, longitude: float) -> None:
        if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
            raise ValueError("invalid coordinates")


def default_rates() -> list[MaterialRate]:
    return [MaterialRate("pet", 25), MaterialRate("cardboard", 12), MaterialRate("paper", 15), MaterialRate("aluminium", 100), MaterialRate("glass", 5)]


def _sum_by_type(records: Iterable[MaterialRecord]) -> dict[str, float]:
    result: dict[str, float] = {}
    for record in records:
        result[record.material_type] = round(result.get(record.material_type, 0) + record.quantity_kg, 3)
    return result


def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Approximate great-circle distance without requiring a maps dependency."""
    earth_radius_km = 6371.0
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * earth_radius_km * asin(sqrt(a))
