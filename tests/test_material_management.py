import unittest

from src.recovery_domain import Profile, RecoveryService, Role


class MaterialManagementTests(unittest.TestCase):
    def setUp(self):
        self.service = RecoveryService()
        self.service.add_profile(Profile("home", Role.HOUSEHOLD, "Home", 28.65, 77.19))
        self.service.add_profile(Profile("kab", Role.KABADIWALA, "Kabadiwala", 28.65, 77.19, 1, {"pet"}))

    def test_new_material_joins_pending_request(self):
        first = self.service.add_material("home", "pet", 2)
        request = self.service.create_collection_request("home", [first.id])
        second = self.service.add_material("home", "pet", 1.5)
        self.assertEqual(second.status, "requested")
        self.assertEqual(request.material_ids, [first.id, second.id])
        self.assertEqual(request.quantity_by_type["pet"], 3.5)

    def test_available_material_can_be_edited_and_removed(self):
        material = self.service.add_material("home", "pet", 2)
        self.service.update_material("home", material.id, 3)
        self.assertEqual(self.service.materials[material.id].quantity_kg, 3)
        self.service.remove_material("home", material.id)
        self.assertNotIn(material.id, self.service.materials)

    def test_requested_material_cannot_be_removed(self):
        material = self.service.add_material("home", "pet", 2)
        self.service.create_collection_request("home", [material.id])
        with self.assertRaisesRegex(ValueError, "available"):
            self.service.remove_material("home", material.id)


if __name__ == "__main__":
    unittest.main()
