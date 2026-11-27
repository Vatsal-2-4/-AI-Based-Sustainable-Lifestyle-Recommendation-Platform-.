"""Repeatable smoke tests for the persisted app flows and footprint calculator."""
import tempfile
import unittest
from pathlib import Path

import database.connection as connection
from backend.services.footprint_service import calculate_footprint
from database import repository
from database.schema import initialize_database


class ApplicationSmokeTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_db_path = connection.DB_PATH
        connection.DB_PATH = Path(self.temp_dir.name) / "smoke.sqlite3"
        initialize_database()
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
        snapshot={"schema_version":1,"electricity_kwh_month":100}
        record_id = repository.create_footprint_record(self.user_id, 3, {"Electricity": 3}, response_id=response_id,input_snapshot=snapshot)
        self.assertEqual(repository.get_footprint_records(self.user_id)[0]["record_id"], record_id)
        self.assertEqual(repository.get_footprint_records(self.user_id)[0]["input_snapshot"],snapshot)
        other_user = repository.create_user("other@example.test", "Other User", "another secure password")
        recommendation_id = repository.save_recommendation(other_user, {
            "action_key": "test-action", "category": "Energy", "title": "Save energy",
            "estimated_saving_kg_co2e": 0, "difficulty": 2, "relevance_score": .5, "rank_position": 1,
        })
        with self.assertRaises(ValueError):
            repository.create_progress(self.user_id, "Cross-user action", "Energy", recommendation_id)
        own_recommendation=repository.save_recommendation(self.user_id,{"action_key":"own-action","category":"Energy","title":"My action","difficulty":2,"relevance_score":.5,"rank_position":1})
        goal_id=repository.create_progress(self.user_id,"My action","Energy",own_recommendation)
        repository.update_progress(self.user_id,goal_id,status="paused")
        self.assertEqual(repository.get_progress(self.user_id)[0]["status"],"paused")
        repository.update_progress(self.user_id,goal_id,progress_percent=100,status="completed")
        completed=next(g for g in repository.get_progress(self.user_id) if g["progress_id"]==goal_id)
        self.assertEqual(completed["progress_percent"],100)
        self.assertEqual(completed["status"],"completed")

    def test_export_and_delete_account_data(self):
        response_id=repository.save_lifestyle_response(self.user_id,self._response())
        repository.create_footprint_record(self.user_id,2,{"Electricity":2},response_id=response_id,input_snapshot={"schema_version":1})
        repository.save_recommendation(self.user_id,{"action_key":"export-test","category":"Energy","title":"Reduce use","difficulty":2,"relevance_score":.5,"rank_position":1})
        exported=repository.export_user_data(self.user_id)
        self.assertEqual(exported["account"]["email"],"smoke@example.test")
        self.assertEqual(len(exported["footprint_estimates"]),1)
        self.assertIsNone(exported["recommendations"][0]["estimated_saving_kg_co2e"])
        self.assertFalse(exported["recommendations"][0]["saving_estimate_available"])
        repository.delete_user(self.user_id)
        with self.assertRaises(ValueError): repository.export_user_data(self.user_id)

    def test_migration_adds_input_snapshot_to_existing_footprint_table(self):
        legacy_path=Path(self.temp_dir.name)/"legacy.sqlite3"
        connection.DB_PATH=legacy_path
        import sqlite3
        db=sqlite3.connect(legacy_path)
        try:
            db.execute("CREATE TABLE users(user_id INTEGER PRIMARY KEY,email TEXT UNIQUE,display_name TEXT NOT NULL,password_salt TEXT,password_hash TEXT,created_at TEXT,updated_at TEXT)")
            db.execute("CREATE TABLE carbon_footprint_records(record_id INTEGER PRIMARY KEY,user_id INTEGER NOT NULL,response_id INTEGER,total_kg_co2e REAL NOT NULL,category_breakdown_json TEXT NOT NULL,factor_version TEXT NOT NULL,is_estimate INTEGER NOT NULL,created_at TEXT)")
            db.commit()
        finally:
            db.close()
        initialize_database()
        db=sqlite3.connect(legacy_path)
        try:
            columns={row[1] for row in db.execute("PRAGMA table_info(carbon_footprint_records)")}
        finally:
            db.close()
        self.assertIn("input_snapshot_json",columns)

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
