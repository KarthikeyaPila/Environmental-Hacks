import tempfile
import unittest
from pathlib import Path

from scripts.prepare_dataset import prepare_dataset


class DatasetPreparationTests(unittest.TestCase):
    def test_maps_classes_and_skips_unmapped_images(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            for class_name in ("plastic", "metal", "trash"):
                class_dir = source / class_name
                class_dir.mkdir(parents=True)
                for index in range(10):
                    (class_dir / f"image_{index}.jpg").write_bytes(b"test image")
            counts = prepare_dataset(source, root / "output")
            self.assertEqual(sum(counts["training"].values()) + sum(counts["testing"].values()), 20)
            self.assertEqual(counts["skipped"], {"trash": 10})
            self.assertTrue((root / "output" / "training" / "pet").exists())
            self.assertTrue((root / "output" / "testing" / "aluminium").exists())


if __name__ == "__main__":
    unittest.main()
