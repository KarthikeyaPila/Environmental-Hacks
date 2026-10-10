import json
import base64
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from src import api_server


class ApiServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), api_server.DemoHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.host, cls.port = cls.server.server_address

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def setUp(self):
        api_server.service, api_server.area_service = api_server.build_state()

    def call(self, method, path, payload=None):
        connection = HTTPConnection(self.host, self.port)
        body = json.dumps(payload).encode() if payload is not None else None
        connection.request(method, path, body, {"Content-Type": "application/json"})
        response = connection.getresponse()
        result = json.loads(response.read())
        connection.close()
        return response.status, result

    def test_http_happy_path(self):
        status, request = self.call("POST", "/api/collection-requests", {"householdId": "household_1"})
        self.assertEqual(status, 201)
        request_id = request["id"]

        status, areas = self.call("GET", "/api/kabadiwalas/kabadiwala_1/areas")
        self.assertEqual(status, 200)
        self.assertEqual(sum(area["requestCount"] for area in areas["areas"]), 1)
        self.assertEqual(areas["requestSummary"]["total"], 1)
        self.assertEqual(areas["requestSummary"]["open"], 1)
        area_id = next(area["areaId"] for area in areas["areas"] if area["requestCount"] == 1)

        status, opportunities = self.call("GET", f"/api/kabadiwalas/kabadiwala_1/areas/{area_id}/opportunities")
        self.assertEqual(status, 200)
        self.assertEqual(opportunities["opportunities"][0]["requestId"], request_id)

        status, accepted = self.call("POST", f"/api/collection-requests/{request_id}/accept", {"kabadiwalaId": "kabadiwala_1"})
        self.assertEqual(status, 200)
        self.assertEqual(accepted["status"], "accepted")
        status, collected = self.call("POST", f"/api/collection-requests/{request_id}/collect", {"kabadiwalaId": "kabadiwala_1"})
        self.assertEqual(status, 200)
        self.assertEqual(collected["status"], "collected")

        status, requirement = self.call("POST", "/api/recycler-requirements", {"recyclerId": "recycler_1", "materialType": "pet", "requiredQuantityKg": 3})
        self.assertEqual(status, 201)
        status, available = self.call("GET", "/api/recyclers/recycler_1/available-material")
        self.assertEqual(status, 200)
        pet = next(item for item in available["availableMaterial"] if item["materialType"] == "pet")

        status, booking = self.call("POST", "/api/bookings", {"recyclerId": "recycler_1", "requirementId": requirement["id"], "kabadiwalaId": pet["kabadiwalaId"], "quantityKg": 3})
        self.assertEqual(status, 201)
        status, reserved = self.call("GET", "/api/recyclers/recycler_1/available-material")
        self.assertEqual(status, 200)
        self.assertEqual(reserved["availableMaterial"], [{"kabadiwalaId": pet["kabadiwalaId"], "kabadiwalaName": "Ramesh Recovery", "region": "West", "regionId": "area_west", "materialType": "pet", "quantityKg": 1.0}, {"kabadiwalaId": pet["kabadiwalaId"], "kabadiwalaName": "Ramesh Recovery", "region": "West", "regionId": "area_west", "materialType": "cardboard", "quantityKg": 2}])

        status, confirmed = self.call("POST", f"/api/bookings/{booking['id']}/confirm", {"recyclerId": "recycler_1"})
        self.assertEqual(status, 200)
        self.assertEqual(confirmed["status"], "completed")

    def test_http_rejects_invalid_transition(self):
        _, request = self.call("POST", "/api/collection-requests", {"householdId": "household_1"})
        status, error = self.call("POST", f"/api/collection-requests/{request['id']}/collect", {"kabadiwalaId": "kabadiwala_1"})
        self.assertEqual(status, 400)
        self.assertEqual(error["error"]["code"], "INVALID_REQUEST")

    def test_http_prevents_duplicate_active_request(self):
        status, _ = self.call("POST", "/api/collection-requests", {"householdId": "household_1"})
        self.assertEqual(status, 201)
        status, error = self.call("POST", "/api/collection-requests", {"householdId": "household_1"})
        self.assertEqual(status, 400)
        self.assertIn("active collection request", error["error"]["message"])

    def test_http_mock_image_classification_is_deterministic(self):
        status, result = self.call("POST", "/api/classify-image", {"filename": "plastic-bottle.jpg"})
        self.assertEqual(status, 200)
        self.assertEqual(result["mode"], "mock")
        self.assertEqual(result["detections"][0]["materialType"], "pet")
        self.assertFalse(result["detections"][0]["requiresConfirmation"])

    def test_http_image_classification_uses_aws_when_configured(self):
        original_arn = api_server.os.environ.get("REKOGNITION_MODEL_ARN")
        original_classifier = api_server.classify_with_rekognition
        api_server.os.environ["REKOGNITION_MODEL_ARN"] = "arn:model"
        api_server.classify_with_rekognition = lambda image: {
            "detections": [{"materialType": "glass", "confidence": 0.95, "requiresConfirmation": False}],
            "mode": "aws",
        }
        try:
            status, result = self.call("POST", "/api/classify-image", {"imageBase64": base64.b64encode(b"image").decode()})
        finally:
            api_server.classify_with_rekognition = original_classifier
            if original_arn is None:
                api_server.os.environ.pop("REKOGNITION_MODEL_ARN", None)
            else:
                api_server.os.environ["REKOGNITION_MODEL_ARN"] = original_arn
        self.assertEqual(status, 200)
        self.assertEqual(result["mode"], "aws")
        self.assertEqual(result["detections"][0]["materialType"], "glass")

    def test_http_exposes_booking_history(self):
        _, request = self.call("POST", "/api/collection-requests", {"householdId": "household_1"})
        self.call("POST", f"/api/collection-requests/{request['id']}/accept", {"kabadiwalaId": "kabadiwala_1"})
        self.call("POST", f"/api/collection-requests/{request['id']}/collect", {"kabadiwalaId": "kabadiwala_1"})
        _, requirement = self.call("POST", "/api/recycler-requirements", {"recyclerId": "recycler_1", "materialType": "pet", "requiredQuantityKg": 1})
        _, available = self.call("GET", "/api/recyclers/recycler_1/available-material")
        pet = next(item for item in available["availableMaterial"] if item["materialType"] == "pet")
        self.call("POST", "/api/bookings", {"recyclerId": "recycler_1", "requirementId": requirement["id"], "kabadiwalaId": pet["kabadiwalaId"], "quantityKg": 1})
        status, bookings = self.call("GET", "/api/recyclers/recycler_1/bookings")
        self.assertEqual(status, 200)
        self.assertEqual(len(bookings["bookings"]), 1)


if __name__ == "__main__":
    unittest.main()
