import json
import tempfile
import unittest
from pathlib import Path

from scripts.prepare_taco_dataset import prepare_taco


class TacoPreparationTests(unittest.TestCase):
    def test_maps_relevant_categories_and_preserves_boxes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image_root = root / "images"
            (image_root / "batch_1").mkdir(parents=True)
            (image_root / "batch_1" / "one.jpg").write_bytes(b"image")
            annotation_file = root / "annotations.json"
            annotation_file.write_text(json.dumps({
                "images": [{"id": 1, "file_name": "batch_1/one.jpg", "width": 100, "height": 80}],
                "categories": [{"id": 4, "name": "Clear plastic bottle"}, {"id": 25, "name": "Food waste"}],
                "annotations": [{"id": 7, "image_id": 1, "category_id": 4, "bbox": [1, 2, 30, 40], "area": 1200}],
            }))
            result = prepare_taco(annotation_file, image_root, root / "output")
            self.assertEqual(result["images"], 1)
            self.assertEqual(result["annotations"], 1)
            mapped = json.loads((root / "output" / "annotations_mapped.json").read_text())
            self.assertEqual(mapped["categories"][0]["name"], "pet")
            self.assertEqual(mapped["annotations"][0]["bbox"], [1, 2, 30, 40])


if __name__ == "__main__":
    unittest.main()
