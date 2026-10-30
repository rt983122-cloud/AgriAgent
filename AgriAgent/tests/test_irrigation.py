"""Tests for deterministic irrigation calculations and agronomic tools."""
import unittest
from tools.irrigation import (
    build_irrigation_recommendation,
    IrrigationAdvisor,
    CropGuide,
    CROP_THRESHOLDS,
    SOIL_FACTOR
)


class IrrigationLogicTests(unittest.TestCase):
    def test_crop_thresholds_exist(self):
        for crop in ["rice", "wheat", "maize", "tomato", "cotton", "sugarcane", "groundnut"]:
            self.assertIn(crop, CROP_THRESHOLDS)
            self.assertGreater(CROP_THRESHOLDS[crop], 0)

    def test_soil_factors_exist(self):
        for soil in ["sandy", "loamy", "clayey"]:
            self.assertIn(soil, SOIL_FACTOR)
        self.assertGreater(SOIL_FACTOR["sandy"], SOIL_FACTOR["loamy"])
        self.assertLess(SOIL_FACTOR["clayey"], SOIL_FACTOR["loamy"])

    def test_deficit_and_water_calculation(self):
        # Rice target is 45. Soil moisture = 30 => deficit = 15.
        rec = build_irrigation_recommendation(
            crop="rice",
            soil_moisture=30.0,
            temperature=30.0,
            humidity=60.0,
            area=2.0,
            soil_type="loamy",
            rainfall=0.0
        )
        self.assertEqual(rec["priority"], "High")
        self.assertEqual(rec["crop_key"], "rice")
        self.assertGreater(rec["estimated_water_mm"], 0)
        self.assertGreater(rec["estimated_water_litres"], 0)

    def test_sufficient_moisture_low_priority(self):
        # Moisture above target
        rec = build_irrigation_recommendation(
            crop="wheat",
            soil_moisture=40.0,  # Target is 35%
            temperature=25.0,
            humidity=50.0,
            area=1.0,
            soil_type="loamy"
        )
        self.assertEqual(rec["priority"], "Low")
        self.assertEqual(rec["estimated_water_mm"], 0.0)
        self.assertEqual(rec["estimated_water_litres"], 0)
        self.assertIn("No irrigation needed", rec["status"])

    def test_rainfall_offset(self):
        # Without rainfall
        dry_rec = build_irrigation_recommendation(
            crop="tomato",
            soil_moisture=20.0,
            temperature=30.0,
            humidity=60.0,
            area=1.0,
            soil_type="loamy",
            rainfall=0.0
        )
        # With significant rainfall
        wet_rec = build_irrigation_recommendation(
            crop="tomato",
            soil_moisture=20.0,
            temperature=30.0,
            humidity=60.0,
            area=1.0,
            soil_type="loamy",
            rainfall=20.0
        )
        self.assertLess(wet_rec["estimated_water_mm"], dry_rec["estimated_water_mm"])
        self.assertLess(wet_rec["estimated_water_litres"], dry_rec["estimated_water_litres"])

    def test_invalid_crop_raises_value_error(self):
        with self.assertRaises(ValueError):
            build_irrigation_recommendation("bananas", 30, 25, 50, 1, "loamy")

    def test_invalid_soil_raises_value_error(self):
        with self.assertRaises(ValueError):
            build_irrigation_recommendation("rice", 30, 25, 50, 1, "gravel")

    def test_invalid_bounds_raise(self):
        with self.assertRaises(ValueError):
            build_irrigation_recommendation("rice", -5, 25, 50, 1, "loamy")
        with self.assertRaises(ValueError):
            build_irrigation_recommendation("rice", 50, 75, 50, 1, "loamy")
        with self.assertRaises(ValueError):
            build_irrigation_recommendation("rice", 50, 25, 50, 0, "loamy")

    def test_irrigation_advisor_tool(self):
        tool = IrrigationAdvisor()
        res = tool.execute(crop="maize", soil_moisture=25, temperature=30, humidity=50, area=2, soil_type="sandy")
        self.assertIsInstance(res, dict)
        self.assertIn("estimated_water_litres", res)
        self.assertEqual(res["priority"], "High")

    def test_crop_guide_tool(self):
        tool = CropGuide()
        res = tool.execute(crop="wheat")
        self.assertIn("Wheat", res)
        self.assertIn("Target Moisture: 35%", res)
        self.assertIn("Sprinkler", res)


if __name__ == "__main__":
    unittest.main()
