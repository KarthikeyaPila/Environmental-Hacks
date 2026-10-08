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
    DelhiArea("area_rohini", "Rohini", 28.7495, 77.0565),
    DelhiArea("area_pitampura", "Pitampura", 28.7033, 77.1322),
    DelhiArea("area_model_town", "Model Town", 28.7177, 77.1931),
    DelhiArea("area_civil_lines", "Civil Lines", 28.6773, 77.2250),
    DelhiArea("area_karol_bagh", "Karol Bagh", 28.6514, 77.1907),
    DelhiArea("area_connaught_place", "Connaught Place", 28.6315, 77.2167),
    DelhiArea("area_lajpat_nagar", "Lajpat Nagar", 28.5677, 77.2433),
    DelhiArea("area_hauz_khas", "Hauz Khas", 28.5494, 77.2001),
    DelhiArea("area_saket", "Saket", 28.5244, 77.2066),
    DelhiArea("area_dwarka", "Dwarka", 28.5921, 77.0460),
    DelhiArea("area_janakpuri", "Janakpuri", 28.6219, 77.0878),
    DelhiArea("area_mayur_vihar", "Mayur Vihar", 28.6047, 77.2924),
    DelhiArea("area_shahdara", "Shahdara", 28.6735, 77.2890),
    DelhiArea("area_okhla", "Okhla", 28.5355, 77.2750),
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
