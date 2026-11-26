"""Unit tests for data safety and personalized action ranking."""
import sqlite3
import tempfile
import unittest
from pathlib import Path

import database.connection as connection
from backend.services.footprint_service import calculate_footprint
from database import repository
from ml.models.content_recommender import recommend


class IsolatedDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir=tempfile.TemporaryDirectory()
        self.original_db_path=connection.DB_PATH
        connection.DB_PATH=Path(self.temp_dir.name)/"unit-tests.sqlite3"

    def tearDown(self):
        connection.DB_PATH=self.original_db_path
        self.temp_dir.cleanup()

    @staticmethod
    def _response():
        return {
            "city":"Bengaluru","commute_mode":"Petrol / diesel car","commute_km_day":12,
            "commute_days_week":5,"diet_pattern":"Mixed diet","housing_type":"Rented apartment",
            "monthly_budget_inr":1200,"electricity_kwh_month":180,"ac_usage":"Some days",
            "waste_segregation":"Sometimes","preferences":{"water_usage":"Moderate"},
        }

    def _add_account_records(self,user_id):
        response_id=repository.save_lifestyle_response(user_id,self._response())
        footprint_id=repository.create_footprint_record(
            user_id,2,{"Electricity":2},response_id=response_id,factor_version="unit-test-factors",
            input_snapshot={"schema_version":1,"electricity_kwh_month":2},
        )
        recommendation_id=repository.save_recommendation(user_id,{
            "action_key":"unit-test-action","category":"Electricity","title":"Check appliance settings",
            "explanation":"Matched to the profile's electricity use.","difficulty":1,
            "relevance_score":.7,"rank_position":1,
        },record_id=footprint_id)
        repository.update_recommendation_status(user_id,recommendation_id,"saved")
        progress_id=repository.create_progress(user_id,"Check appliance settings","Electricity",recommendation_id)
        return response_id,footprint_id,recommendation_id,progress_id

    def test_account_backup_is_valid_scoped_sqlite_and_omits_password_hashes(self):
        account_id=repository.create_user("owner@example.test","Owner User","a strong sample password")
        self._add_account_records(account_id)
        other_id=repository.create_user("other@example.test","Other User","another strong password")
        self._add_account_records(other_id)

        backup_bytes=repository.backup_user_database(account_id)
        self.assertIsInstance(backup_bytes,bytes)
        self.assertGreater(len(backup_bytes),0)
        backup_path=Path(self.temp_dir.name)/"downloaded-backup.sqlite3"
        backup_path.write_bytes(backup_bytes)
        backup=sqlite3.connect(backup_path)
        try:
            self.assertEqual(backup.execute("PRAGMA integrity_check").fetchone()[0],"ok")
            self.assertEqual(backup.execute("PRAGMA foreign_key_check").fetchall(),[])
            self.assertEqual(backup.execute("SELECT email FROM users").fetchall(),[("owner@example.test",)])
            self.assertEqual(backup.execute("SELECT password_hash FROM users").fetchall(),[(None,)])
            for table in ("lifestyle_questionnaire_responses","carbon_footprint_records","ai_recommendations","user_progress"):
                with self.subTest(table=table):
                    self.assertEqual(backup.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0],1)
        finally:
            backup.close()

    def test_demo_reset_clears_only_demo_records_and_refuses_regular_accounts(self):
        demo_id=repository.get_or_create_user("demo@example.local","Demo User")
        other_id=repository.create_user("regular@example.test","Regular User","a strong sample password")
        self._add_account_records(demo_id)
        self._add_account_records(other_id)

        with self.assertRaisesRegex(ValueError,"built-in demo profile"):
            repository.reset_demo_data(other_id)
        removed=repository.reset_demo_data(demo_id)
        self.assertEqual(removed["user_progress"],1)
        self.assertEqual(removed["ai_recommendations"],1)
        self.assertEqual(removed["carbon_footprint_records"],1)
        self.assertEqual(removed["lifestyle_questionnaire_responses"],1)
        self.assertIsNotNone(repository.get_user(demo_id))
        self.assertEqual(repository.get_footprint_records(demo_id),[])
        self.assertEqual(len(repository.get_footprint_records(other_id)),1)
        self.assertEqual(len(repository.get_progress(other_id)),1)

    def test_validation_errors_identify_the_problem(self):
        with self.assertRaisesRegex(ValueError,"Enter display name using 1 to 120 characters"):
            repository.create_user("blank@example.test"," ","a strong sample password")
        with self.assertRaisesRegex(ValueError,"Password must contain at least 12 characters"):
            repository.create_user("short@example.test","Short Password","short")
        user_id=repository.create_user("range@example.test","Range User","a strong sample password")
        with self.assertRaisesRegex(ValueError,"Total footprint cannot be less than 0"):
            repository.create_footprint_record(user_id,-1,{"Electricity":0})


class RecommendationUnitTests(unittest.TestCase):
    @staticmethod
    def _profile(**overrides):
        profile={
            "commute":"Petrol / diesel car","commute_km":16,"commute_days":5,
            "electricity":220,"diet":"Mixed diet","water_usage":"Moderate",
            "food_waste":"Sometimes","shopping_habit":"Monthly","segregation":"Sometimes",
            "public_transport_available":True,"shops_in_person":True,"budget":1000,
            "ac":"Some days","composting_possible":False,
        }
        profile.update(overrides)
        return profile

    def test_recommendations_are_ranked_explained_and_bounded(self):
        actions=recommend(self._profile(),top_n=8)
        self.assertEqual(len(actions),8)
        scores=[action["relevance_score"] for action in actions]
        self.assertEqual(scores,sorted(scores,reverse=True))
        for action in actions:
            with self.subTest(action=action["action_id"]):
                self.assertGreaterEqual(action["relevance_score"],0)
                self.assertLessEqual(action["relevance_score"],1)
                self.assertTrue(action["matched_habits"])
                self.assertIn("Catalogue text match",action["reason"])
        transport=next(action for action in actions if action["action_id"]=="TR01")
        self.assertIn("Main commute: Petrol / diesel car",transport["matched_habits"])
        self.assertIn("Commute: 16 km/day on 5 days/week",transport["matched_habits"])

    def test_ineligible_actions_are_filtered(self):
        profile=self._profile(public_transport_available=False,diet="Vegan")
        actions=recommend(profile,top_n=30)
        action_ids={action["action_id"] for action in actions}
        self.assertNotIn("TR01",action_ids)
        self.assertNotIn("FO01",action_ids)


class FootprintInputUnitTests(unittest.TestCase):
    def test_negative_nonfinite_and_unknown_food_inputs_are_rejected(self):
        valid={"petrol_l_month":0,"diesel_l_month":0,"electricity_kwh_month":0,"water_l_person_day":0,"food_kg_week":{},"waste_kg_week":{}}
        for field,value in (("petrol_l_month",-1),("electricity_kwh_month",float("inf"))):
            with self.subTest(field=field,value=value):
                inputs={**valid,field:value}
                with self.assertRaises(ValueError): calculate_footprint(inputs)
        with self.assertRaisesRegex(ValueError,"Unknown food factor: made_up"):
            calculate_footprint({**valid,"food_kg_week":{"made_up":1}})

    def test_all_zero_inputs_produce_zero_emissions_but_valid_empty_indicators(self):
        result=calculate_footprint({"petrol_l_month":0,"diesel_l_month":0,"electricity_kwh_month":0,"water_l_person_day":0,"food_kg_week":{},"waste_kg_week":{}})
        self.assertEqual(result["total_kg_co2e"],0)
        self.assertTrue(all(amount==0 for amount in result["category_kg_co2e"].values()))
        self.assertEqual(result["water_litres_year"],0)
        self.assertEqual(result["waste_kg_year"],{})


if __name__=="__main__":
    unittest.main()
