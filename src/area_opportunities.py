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
    DelhiArea("area_north_delhi", "North Delhi", 28.7041, 77.1025),
    DelhiArea("area_central_delhi", "Central Delhi", 28.6448, 77.2167),
    DelhiArea("area_south_delhi", "South Delhi", 28.5244, 77.1855),
    DelhiArea("area_east_delhi", "East Delhi", 28.6280, 77.2773),
    DelhiArea("area_west_delhi", "West Delhi", 28.6663, 77.0680),
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
        return [self._summary(area, grouped[area.id]) for area in self.areas]

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
        return {
            "areaId": area.id,
            "name": area.name,
            "requestCount": len(requests),
            "materialKg": round(sum(sum(request.quantity_by_type.values()) for request in requests), 3),
            "estimatedValueInr": round(sum(request.estimated_value for request in requests)),
            "center": {"latitude": area.center_latitude, "longitude": area.center_longitude},
        }
