"""Repeatable smoke tests for the persisted app flows and footprint calculator."""
import tempfile
import unittest
from pathlib import Path

import database.connection as connection
from backend.services.footprint_service import calculate_footprint
from database import repository


class ApplicationSmokeTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_db_path = connection.DB_PATH
        connection.DB_PATH = Path(self.temp_dir.name) / "smoke.sqlite3"
        self.user_id = repository.create_user("smoke@example.test", "Smoke User", "a secure password 123")

    def tearDown(self):
        connection.DB_PATH = self.original_db_path
        self.temp_dir.cleanup()

    def test_password_hash_and_authentication(self):
        self.assertEqual(repository.authenticate_user("SMOKE@example.test", "a secure password 123")["user_id"], self.user_id)
        self.assertIsNone(repository.authenticate_user("smoke@example.test", "incorrect password"))

    def test_rejects_invalid_numbers_and_fractional_days(self):
        with self.assertRaises(ValueError):
            repository.create_footprint_record(self.user_id, float("nan"), {"Electricity": 1})
        response = self._response(commute_days_week=2.5)
        with self.assertRaises(ValueError):
            repository.save_lifestyle_response(self.user_id, response)

    def test_persists_records_and_prevents_cross_user_links(self):
        response_id = repository.save_lifestyle_response(self.user_id, self._response())
        record_id = repository.create_footprint_record(self.user_id, 3, {"Electricity": 3}, response_id=response_id)
        self.assertEqual(repository.get_footprint_records(self.user_id)[0]["record_id"], record_id)
        other_user = repository.create_user("other@example.test", "Other User", "another secure password")
        recommendation_id = repository.save_recommendation(other_user, {
            "action_key": "test-action", "category": "Energy", "title": "Save energy",
            "estimated_saving_kg_co2e": 0, "difficulty": 2, "relevance_score": .5, "rank_position": 1,
        })
        with self.assertRaises(ValueError):
            repository.create_progress(self.user_id, "Cross-user action", "Energy", recommendation_id)

    def test_null_record_recommendation_upserts(self):
        fields = {"action_key": "same-action", "category": "Energy", "title": "First title", "difficulty": 2, "relevance_score": .5, "rank_position": 1}
        first_id = repository.save_recommendation(self.user_id, fields)
        fields["title"] = "Updated title"
        self.assertEqual(repository.save_recommendation(self.user_id, fields), first_id)
        self.assertEqual(len(repository.get_recommendations(self.user_id)), 1)

    def test_calculator_annualizes_inputs_and_keeps_water_separate(self):
        result = calculate_footprint({
            "petrol_l_month": 10, "diesel_l_month": 0, "electricity_kwh_month": 100,
            "water_l_person_day": 80, "food_kg_week": {"pulses": 1}, "waste_kg_week": {"food scraps": 1},
        })
        self.assertEqual(result["water_litres_year"], 29200)
        self.assertEqual(result["waste_kg_year"]["food scraps"], 52)
        self.assertEqual(result["total_kg_co2e"], round(sum(result["category_kg_co2e"].values()), 2))
        self.assertEqual(set(result["category_kg_co2e"]), {"Transportation", "Electricity", "Food"})

    @staticmethod
    def _response(**overrides):
        response = {
            "city": "Pune", "commute_mode": "Car", "commute_km_day": 10,
            "commute_days_week": 5, "diet_pattern": "Mixed", "housing_type": "Flat",
            "monthly_budget_inr": 1000, "electricity_kwh_month": 120,
            "ac_usage": "Sometimes", "waste_segregation": "Sometimes", "preferences": {},
        }
        response.update(overrides)
        return response


if __name__ == "__main__":
    unittest.main()
