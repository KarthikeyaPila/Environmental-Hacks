import unittest

from src.recovery_domain import Profile, RecoveryService, Role


class MetricsTests(unittest.TestCase):
    def setUp(self):
        self.service = RecoveryService()
        self.service.add_profile(Profile("home", Role.HOUSEHOLD, "Home", 28.65, 77.19))
        self.service.add_profile(Profile("kab", Role.KABADIWALA, "Kabadiwala", 28.65, 77.19, 1, {"pet"}))
        self.service.add_profile(Profile("rec", Role.RECYCLER, "Recycler", 28.65, 77.19))

    def test_household_metrics_are_record_based(self):
        material = self.service.add_material("home", "pet", 2)
        self.service.create_collection_request("home", [material.id])
        self.service.accept_request("kab", next(iter(self.service.requests)))
        self.service.collect_request("kab", next(iter(self.service.requests)))
        metrics = self.service.household_metrics("home")
        self.assertEqual(metrics["totalRecordedKg"], 2)
        self.assertEqual(metrics["totalCollectedKg"], 2)
        self.assertEqual(metrics["byMaterialType"], {"pet": 2})

    def test_kabadiwala_metrics_include_collected_inventory(self):
        material = self.service.add_material("home", "pet", 2)
        request = self.service.create_collection_request("home", [material.id])
        self.service.accept_request("kab", request.id)
        self.service.collect_request("kab", request.id)
        metrics = self.service.kabadiwala_metrics("kab")
        self.assertEqual(metrics["collectionsCompleted"], 1)
        self.assertEqual(metrics["estimatedRevenueInr"], 50)

    def test_kabadiwala_profile_indicators_are_explicitly_demo_values(self):
        profile = self.service.profiles["kab"]
        profile.demo_rating = 4.8
        profile.payout_index = 1.08
        summary = self.service.profile_summary("kab")
        self.assertEqual(summary["demoRating"], 4.8)
        self.assertEqual(summary["payoutIndex"], 1.08)

    def test_recycler_metrics_track_requirements_and_bookings(self):
        requirement = self.service.create_requirement("rec", "pet", 5)
        metrics = self.service.recycler_metrics("rec")
        self.assertEqual(metrics["requirements"][0]["status"], "open")
        self.assertEqual(metrics["fulfilledQuantityKg"], 0)
        self.assertEqual(metrics["reservedBookings"], 0)


if __name__ == "__main__":
    unittest.main()
