import unittest

from src.area_opportunities import AreaOpportunityService
from src.recovery_domain import CollectionRequest, RequestStatus


class AreaOpportunityTests(unittest.TestCase):
    def test_pending_requests_are_aggregated_by_nearest_delhi_area(self):
        request = CollectionRequest(
            id="req_1", household_id="home_1", material_ids=["mat_1"],
            quantity_by_type={"pet": 4, "cardboard": 2}, estimated_value=124,
            latitude=28.6515, longitude=77.1908,
        )
        summaries = AreaOpportunityService().summaries([request])
        karol_bagh = next(summary for summary in summaries if summary["areaId"] == "area_karol_bagh")
        self.assertEqual(karol_bagh["requestCount"], 1)
        self.assertEqual(karol_bagh["materialKg"], 6)
        self.assertEqual(karol_bagh["estimatedValueInr"], 124)

    def test_non_pending_requests_are_not_opportunities(self):
        request = CollectionRequest(
            id="req_1", household_id="home_1", material_ids=["mat_1"],
            quantity_by_type={"pet": 4}, estimated_value=100,
            latitude=28.6515, longitude=77.1908, status=RequestStatus.ACCEPTED,
        )
        service = AreaOpportunityService()
        self.assertEqual(sum(s["requestCount"] for s in service.summaries([request])), 0)
        self.assertEqual(service.opportunities("area_karol_bagh", [request]), [])


if __name__ == "__main__":
    unittest.main()
