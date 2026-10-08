import unittest

from src.recovery_domain import Profile, RecoveryService, Role, RequestStatus, RequirementStatus


def setup_service():
    service = RecoveryService()
    service.add_profile(Profile("home_1", Role.HOUSEHOLD, "Household 1", 12.9717, 77.5940))
    service.add_profile(Profile("kab_1", Role.KABADIWALA, "Ramesh", 12.9720, 77.5942, 2, {"pet", "cardboard"}))
    service.add_profile(Profile("rec_1", Role.RECYCLER, "Green Recycler", 12.9, 77.5))
    return service


class RecoveryDomainTests(unittest.TestCase):
  def test_complete_material_lifecycle(self):
    service = setup_service()
    pet = service.add_material("home_1", "PET", 4)
    cardboard = service.add_material("home_1", "cardboard", 2)
    request = service.create_collection_request("home_1", [pet.id, cardboard.id])

    opportunities = service.nearby_requests("kab_1")
    self.assertEqual(opportunities[0]["request"].id, request.id)
    service.accept_request("kab_1", request.id)
    service.collect_request("kab_1", request.id)

    requirement = service.create_requirement("rec_1", "pet", 10)
    self.assertEqual(service.available_material("rec_1")[0]["quantity_kg"], 4)
    booking = service.book_material("rec_1", requirement.id, "kab_1", 3)

    self.assertEqual(booking.quantity_kg, 3)
    self.assertEqual(service.requirements[requirement.id].fulfilled_quantity_kg, 0)
    service.confirm_booking("rec_1", booking.id)
    self.assertEqual(service.requirements[requirement.id].status, RequirementStatus.PARTIALLY_FULFILLED)
    self.assertEqual(service.contribution("home_1")["material_kg"], 6)


  def test_invalid_state_transitions_are_rejected(self):
    service = setup_service()
    material = service.add_material("home_1", "pet", 1)
    request = service.create_collection_request("home_1", [material.id])

    with self.assertRaisesRegex(ValueError, "accepted"):
        service.collect_request("kab_1", request.id)
    self.assertEqual(request.status, RequestStatus.PENDING)

    service.reject_request("kab_1", request.id)
    with self.assertRaisesRegex(ValueError, "pending"):
        service.accept_request("kab_1", request.id)


  def test_booking_cannot_exceed_inventory_or_requirement(self):
    service = setup_service()
    material = service.add_material("home_1", "pet", 2)
    request = service.create_collection_request("home_1", [material.id])
    service.accept_request("kab_1", request.id)
    service.collect_request("kab_1", request.id)
    requirement = service.create_requirement("rec_1", "pet", 1)

    with self.assertRaisesRegex(ValueError, "exceeds"):
        service.book_material("rec_1", requirement.id, "kab_1", 1.1)


if __name__ == "__main__":
    unittest.main()
