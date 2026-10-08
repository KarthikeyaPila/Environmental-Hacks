import json
import subprocess
import sys
import unittest


class SeedDataTests(unittest.TestCase):
    def test_seed_script_is_deterministic_and_populated(self):
        result = subprocess.run([sys.executable, "scripts/seed_demo_data.py"], check=True, capture_output=True, text=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["profiles"], 6)
        self.assertEqual(payload["materials"], 5)
        self.assertEqual(payload["collectionRequests"], 3)
        self.assertGreaterEqual(len(payload["areas"]), 3)


if __name__ == "__main__":
    unittest.main()
