import json
import subprocess
import sys
import unittest


class SeedDataTests(unittest.TestCase):
    def test_seed_script_is_deterministic_and_populated(self):
        result = subprocess.run([sys.executable, "scripts/seed_demo_data.py"], check=True, capture_output=True, text=True)
        payload = json.loads(result.stdout)
        self.assertGreaterEqual(payload["profiles"], 37)
        self.assertGreaterEqual(payload["households"], 24)
        self.assertEqual(payload["kabadiwalas"], 6)
        self.assertEqual(payload["recyclers"], 9)
        self.assertGreaterEqual(payload["materials"], 48)
        self.assertGreaterEqual(payload["availableInventoryLots"], 24)
        self.assertGreaterEqual(payload["availableInventoryKg"], 120)
        self.assertGreaterEqual(payload["collectionRequests"], 23)
        self.assertEqual(payload["requirements"], 9)
        self.assertGreaterEqual(len(payload["areas"]), 3)
        self.assertTrue(all(3 <= area["requestCount"] <= 6 for area in payload["areas"]))
        self.assertGreater(payload["requestStatuses"]["accepted"], 0)
        self.assertGreater(payload["requestStatuses"]["collected"], 0)

    def test_collector_inventory_seed_is_additive_and_populated(self):
        result = subprocess.run(
            [sys.executable, "scripts/seed_collector_inventory.py"],
            check=True, capture_output=True, text=True,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["mode"], "dry-run")
        self.assertEqual(payload["profiles"], 26)
        self.assertEqual(payload["collectedMaterialRecords"], 24)
        self.assertGreater(payload["collectedInventoryKg"], 120)


if __name__ == "__main__":
    unittest.main()
