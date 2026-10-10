import json
import subprocess
import sys
import unittest


class SeedDataTests(unittest.TestCase):
    def test_seed_script_is_deterministic_and_populated(self):
        result = subprocess.run([sys.executable, "scripts/seed_demo_data.py"], check=True, capture_output=True, text=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["profiles"], 37)
        self.assertEqual(payload["households"], 24)
        self.assertEqual(payload["kabadiwalas"], 4)
        self.assertEqual(payload["recyclers"], 9)
        self.assertEqual(payload["materials"], 48)
        self.assertEqual(payload["collectionRequests"], 23)
        self.assertEqual(payload["requirements"], 9)
        self.assertGreaterEqual(len(payload["areas"]), 3)


if __name__ == "__main__":
    unittest.main()
