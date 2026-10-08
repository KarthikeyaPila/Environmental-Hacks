import sys
import types
import unittest

from src.image_classifier import classify_with_rekognition


class ImageClassifierTests(unittest.TestCase):
    def test_normalizes_aws_labels_and_confidence(self):
        calls = {}

        class FakeClient:
            def detect_custom_labels(self, **kwargs):
                calls.update(kwargs)
                return {"CustomLabels": [{"Name": "Plastic", "Confidence": 92.0}, {"Name": "Glass", "Confidence": 61.0}]}

        sys.modules["boto3"] = types.SimpleNamespace(client=lambda *args, **kwargs: FakeClient())
        try:
            result = classify_with_rekognition(b"image", "arn:model")
        finally:
            del sys.modules["boto3"]

        self.assertEqual(calls["ProjectVersionArn"], "arn:model")
        self.assertEqual(calls["Image"], {"Bytes": b"image"})
        self.assertEqual(result["mode"], "aws")
        self.assertEqual(result["detections"][0]["materialType"], "pet")
        self.assertFalse(result["detections"][0]["requiresConfirmation"])
        self.assertTrue(result["detections"][1]["requiresConfirmation"])


if __name__ == "__main__":
    unittest.main()
