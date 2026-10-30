"""Tests for AgriAgent Flask REST APIs and database operations."""
import json
import unittest
from app import app


class AppApiTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_home_page(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"AgriAgent", res.data)
        self.assertIn(b"Smart Irrigation", res.data)

    def test_health_endpoint(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        d = res.get_json()
        self.assertTrue(d.get("ok"))
        self.assertEqual(d.get("service"), "AgriAgent")

    def test_status_endpoint(self):
        res = self.client.get("/api/status")
        self.assertEqual(res.status_code, 200)
        d = res.get_json()
        self.assertIn("ai_configured", d)
        self.assertEqual(d.get("supported_crops_count"), 7)

    def test_crops_endpoint(self):
        res = self.client.get("/api/crops")
        self.assertEqual(res.status_code, 200)
        d = res.get_json()
        self.assertIn("rice", d["crops"])
        self.assertIn("wheat", d["crops"])

    def test_stats_endpoint(self):
        res = self.client.get("/api/stats")
        self.assertEqual(res.status_code, 200)
        d = res.get_json()
        self.assertIn("total_fields", d)
        self.assertIn("total_water_litres", d)

    def test_recommend_endpoint_valid(self):
        payload = {
            "crop": "tomato",
            "soil_type": "loamy",
            "soil_moisture": 25.0,
            "temperature": 32.0,
            "humidity": 50.0,
            "area": 2.5,
            "rainfall": 0.0,
            "field_name": "Test Greenhouse"
        }
        res = self.client.post("/api/recommend", json=payload)
        self.assertEqual(res.status_code, 200)
        d = res.get_json()
        self.assertEqual(d["priority"], "High")
        self.assertGreater(d["estimated_water_litres"], 0)
        self.assertEqual(d["target_moisture"], 38)

    def test_recommend_endpoint_invalid_crop(self):
        payload = {"crop": "invalid_crop", "soil_type": "loamy", "soil_moisture": 25.0}
        res = self.client.post("/api/recommend", json=payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn("error", res.get_json())

    def test_recommend_endpoint_invalid_numbers(self):
        payload = {"crop": "rice", "soil_type": "clayey", "soil_moisture": "not_a_number"}
        res = self.client.post("/api/recommend", json=payload)
        self.assertEqual(res.status_code, 400)

    def test_ask_endpoint_empty_query(self):
        res = self.client.post("/api/ask", json={"query": ""})
        self.assertEqual(res.status_code, 400)

    def test_ask_endpoint_dry_run(self):
        res = self.client.post("/api/ask", json={"query": "Test dry run question", "dry_run": True})
        self.assertEqual(res.status_code, 200)
        d = res.get_json()
        self.assertIn("answer", d)
        self.assertIsInstance(d.get("trace"), list)

    def test_ask_endpoint_agri_dry_run(self):
        res = self.client.post("/api/ask", json={"query": "How much water does wheat need?", "dry_run": True})
        self.assertEqual(res.status_code, 200)
        d = res.get_json()
        self.assertIn("Wheat", d["answer"])
        tools = [t["tool"] for t in d.get("trace", [])]
        self.assertIn("crop_guide", tools)

    def test_fields_crud(self):
        # 1. Create Field
        new_field = {
            "name": "Integration Plot Alpha",
            "crop": "cotton",
            "soil_type": "clayey",
            "area": 3.5,
            "location": "Sector 9"
        }
        res_create = self.client.post("/api/fields", json=new_field)
        self.assertEqual(res_create.status_code, 201)
        created_field = res_create.get_json()["field"]
        field_id = created_field["id"]

        # 2. List Fields
        res_list = self.client.get("/api/fields")
        self.assertEqual(res_list.status_code, 200)
        field_names = [f["name"] for f in res_list.get_json()["fields"]]
        self.assertIn("Integration Plot Alpha", field_names)

        # 3. Delete Field
        res_del = self.client.delete(f"/api/fields/{field_id}")
        self.assertEqual(res_del.status_code, 200)

    def test_history_endpoint(self):
        res = self.client.get("/api/history?limit=10")
        self.assertEqual(res.status_code, 200)
        d = res.get_json()
        self.assertIn("history", d)


if __name__ == "__main__":
    unittest.main()
