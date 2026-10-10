"""Area-level opportunity views for the kabadiwala workflow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .recovery_domain import CollectionRequest, RequestStatus


@dataclass(frozen=True)
class DelhiArea:
    id: str
    name: str
    center_latitude: float
    center_longitude: float


DELHI_AREAS = (
    DelhiArea("area_north", "North", 28.7500, 77.2000),
    DelhiArea("area_north_west", "North West", 28.7200, 77.1000),
    DelhiArea("area_west", "West", 28.6600, 77.1000),
    DelhiArea("area_south_west", "South West", 28.5900, 77.0500),
    DelhiArea("area_central", "Central", 28.6600, 77.2200),
    DelhiArea("area_new_delhi", "New Delhi", 28.6100, 77.2100),
    DelhiArea("area_north_east", "North East", 28.7000, 77.2800),
    DelhiArea("area_shahdara", "Shahdara", 28.6700, 77.2900),
    DelhiArea("area_east", "East", 28.6300, 77.2900),
    DelhiArea("area_south_east", "South East", 28.5500, 77.2800),
    DelhiArea("area_south", "South", 28.5200, 77.2000),
)


class AreaOpportunityService:
    """Maps approximate requests to seeded areas and produces summaries."""

    def __init__(self, areas: Iterable[DelhiArea] = DELHI_AREAS) -> None:
        self.areas = tuple(areas)

    def summaries(self, requests: Iterable[CollectionRequest]) -> list[dict]:
        grouped = {area.id: [] for area in self.areas}
        for request in requests:
            if request.status != RequestStatus.PENDING:
                continue
            area = self.area_for(request.latitude, request.longitude)
            grouped[area.id].append(request)
        summaries = [self._summary(area, grouped[area.id]) for area in self.areas]
        ranked = sorted(summaries, key=lambda item: (item["estimatedValueInr"], item["materialKg"]), reverse=True)
        ranks = {item["areaId"]: index + 1 for index, item in enumerate(ranked)}
        for summary in summaries:
            summary["opportunityRank"] = ranks[summary["areaId"]]
        return summaries

    def opportunities(self, area_id: str, requests: Iterable[CollectionRequest]) -> list[dict]:
        area = self._area(area_id)
        result = []
        for request in requests:
            if request.status == RequestStatus.PENDING and self.area_for(request.latitude, request.longitude).id == area.id:
                result.append({
                    "requestId": request.id,
                    "approximateLatitude": request.latitude,
                    "approximateLongitude": request.longitude,
                    "quantityByType": request.quantity_by_type,
                    "estimatedValueInr": round(request.estimated_value),
                    "status": request.status.value,
                })
        return result

    def area_for(self, latitude: float, longitude: float) -> DelhiArea:
        return min(self.areas, key=lambda area: (area.center_latitude - latitude) ** 2 + (area.center_longitude - longitude) ** 2)

    def _area(self, area_id: str) -> DelhiArea:
        for area in self.areas:
            if area.id == area_id:
                return area
        raise ValueError("area not found")

    @staticmethod
    def _summary(area: DelhiArea, requests: list[CollectionRequest]) -> dict:
        material_breakdown: dict[str, float] = {}
        for request in requests:
            for material_type, quantity in request.quantity_by_type.items():
                material_breakdown[material_type] = round(material_breakdown.get(material_type, 0) + quantity, 3)
        return {
            "areaId": area.id,
            "name": area.name,
            "requestCount": len(requests),
            "materialKg": round(sum(sum(request.quantity_by_type.values()) for request in requests), 3),
            "estimatedValueInr": round(sum(request.estimated_value for request in requests)),
            "materialBreakdown": material_breakdown,
            "center": {"latitude": area.center_latitude, "longitude": area.center_longitude},
        }
