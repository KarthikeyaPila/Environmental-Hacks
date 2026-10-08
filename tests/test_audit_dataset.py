import tempfile
import unittest
from pathlib import Path

from scripts.audit_dataset import audit_dataset


class DatasetAuditTests(unittest.TestCase):
    def test_audit_reports_counts_and_missing_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "training" / "pet").mkdir(parents=True)
            (root / "testing" / "pet").mkdir(parents=True)
            (root / "training" / "pet" / "a.jpg").write_bytes(b"a")
            (root / "testing" / "pet" / "b.jpg").write_bytes(b"b")
            report = audit_dataset(root)
            self.assertEqual(report["training"], {"pet": 1})
            self.assertEqual(report["testing"], {"pet": 1})
            self.assertIn("glass", report["missingLabels"])
            self.assertEqual(report["overlap"], [])


if __name__ == "__main__":
    unittest.main()
