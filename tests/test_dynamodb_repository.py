import unittest
from types import SimpleNamespace

from src.dynamodb_repository import DynamoRecoveryRepository
from src.recovery_domain import Profile, Role


class FakeTable:
    def __init__(self):
        self.items = []

    def put_item(self, **kwargs):
        self.items.append(kwargs["Item"])


class FakeResource:
    def __init__(self, table):
        self._table = table

    def Table(self, name):
        return self._table


class DynamoRepositoryTests(unittest.TestCase):
    def test_profile_has_single_table_keys_and_gsi(self):
        table = FakeTable()
        repository = DynamoRecoveryRepository(resource=FakeResource(table))
        repository.put_profile(Profile("household_1", Role.HOUSEHOLD, "A", 28.7, 77.1))
        item = table.items[0]
        self.assertEqual(item["pk"], "PROFILE#household_1")
        self.assertEqual(item["sk"], "PROFILE")
        self.assertEqual(item["gsi1pk"], "ROLE#household")


if __name__ == "__main__":
    unittest.main()
