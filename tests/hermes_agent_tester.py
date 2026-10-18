"""
Unit & Integration Tests for Hermes Agent Simulation & Testing Loop
National University Bangladesh AI Assistant

Tests:
1. Scenario & Persona generation integrity.
2. Critic evaluation metrics (factual accuracy, tone, zero-hallucination, official URL check).
3. Multi-turn dialogue testing with conversation memory.
4. Autonomous gap logging into data/knowledge_gaps.json & SQLite gap_queue.
5. End-to-end simulation run.
"""

import os
import sys
import json
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.agents.hermes_tester import get_hermes_tester, SIMULATION_SCENARIOS, KNOWLEDGE_GAPS_FILE
from db.sql_store import get_sql_store
from token_service.db import init_token_database

class TestHermesAgentTester(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_token_database()
        cls.tester = get_hermes_tester()
        cls.sql_store = get_sql_store()

    def test_01_scenarios_configured(self):
        """Verify that simulation scenarios cover all target student personas."""
        self.assertGreaterEqual(len(SIMULATION_SCENARIOS), 6)
        scenario_ids = [s["scenario_id"] for s in SIMULATION_SCENARIOS]
        self.assertIn("PANICKED_FRESHER_01", scenario_ids)
        self.assertIn("BANGLISH_DEGREE_APPLICANT_02", scenario_ids)
        self.assertIn("COLLEGE_TRANSFER_TC_03", scenario_ids)
        self.assertIn("DOCUMENT_CORRECTION_04", scenario_ids)
        self.assertIn("ENGLISH_MASTERS_APPLICANT_05", scenario_ids)
        self.assertIn("PROMPT_INJECTION_ADVERSARIAL_07", scenario_ids)
        print("[TEST 1 PASS] All required student personas & scenarios verified.")

    def test_02_critic_evaluation_metrics(self):
        """Verify Critic & Judge correctly detects good answers and penalizes deprecated URLs / hallucinations."""
        # 1. Good answer with official student services URL
        good_eval = self.tester.evaluate_response(
            query="আমি কলেজ পরিবর্তন করতে চাই",
            response_text="কলেজ পরিবর্তনের জন্য অফিসিয়াল পোর্টালে যান: http://103.113.200.68/nu-app/ এবং সোনালী সেবায় ফি দিন।",
            confidence=0.95,
            latency_sec=0.25,
            expected_portal="http://103.113.200.68/nu-app/"
        )
        self.assertTrue(good_eval["passed"])
        self.assertGreaterEqual(good_eval["overall_score"], 0.8)
        self.assertEqual(len(good_eval["penalties"]), 0)

        # 2. Bad answer with deprecated URL
        bad_eval = self.tester.evaluate_response(
            query="আমি কলেজ পরিবর্তন করতে চাই",
            response_text="আপনি services.nu.edu.bd পোর্টালে গিয়ে আবেদন করুন।",
            confidence=0.80,
            latency_sec=0.30,
            expected_portal="http://103.113.200.68/nu-app/"
        )
        self.assertFalse(bad_eval["passed"])
        self.assertTrue(any("deprecated" in p.lower() for p in bad_eval["penalties"]))
        print("[TEST 2 PASS] Critic evaluation logic correctly scores compliant and penalizes non-compliant answers.")

    def test_03_multi_turn_tc_scenario(self):
        """Verify multi-turn scenario execution for College Transfer (TC)."""
        tc_scenario = next(s for s in SIMULATION_SCENARIOS if s["scenario_id"] == "COLLEGE_TRANSFER_TC_03")
        res = self.tester.run_scenario(tc_scenario)
        self.assertEqual(res["scenario_id"], "COLLEGE_TRANSFER_TC_03")
        self.assertEqual(len(res["turns"]), 3)
        self.assertGreater(res["average_score"], 0.6)
        print(f"[TEST 3 PASS] Multi-turn TC scenario completed with score: {res['average_score']}.")

    def test_04_knowledge_gap_logging(self):
        """Verify knowledge gap is recorded in data/knowledge_gaps.json and SQLite gap_queue."""
        test_query = "২০২৭ সালের অনার্স পরীক্ষার বিশেষ সিলেবাস কীভাবে ডাউনলোড করব?"
        self.tester.log_knowledge_gap(
            user_query=test_query,
            bot_reply="তথ্য পাওয়া যায়নি।",
            reason="Low confidence response; missing 2027 syllabus",
            confidence=0.35,
            scenario_id="TEST_GAP_SCENARIO"
        )

        # Check data/knowledge_gaps.json
        self.assertTrue(KNOWLEDGE_GAPS_FILE.exists())
        with open(KNOWLEDGE_GAPS_FILE, "r", encoding="utf-8") as f:
            gaps = json.load(f)
        matching_gap = next((g for g in gaps if g.get("query") == test_query), None)
        self.assertIsNotNone(matching_gap)
        self.assertEqual(matching_gap["scenario_id"], "TEST_GAP_SCENARIO")

        # Check SQLite
        pending_gaps = self.sql_store.get_gap_queue(limit=50)
        found_in_db = any(g["user_query"] == test_query for g in pending_gaps)
        self.assertTrue(found_in_db)
        print("[TEST 4 PASS] Knowledge gap persisted to JSON and SQLite gap_queue successfully.")

    def test_05_adversarial_prompt_injection_safety(self):
        """Verify chatbot resists prompt injections and does not leak secrets."""
        adv_scenario = next(s for s in SIMULATION_SCENARIOS if s["scenario_id"] == "PROMPT_INJECTION_ADVERSARIAL_07")
        res = self.tester.run_scenario(adv_scenario)
        self.assertEqual(res["scenario_id"], "PROMPT_INJECTION_ADVERSARIAL_07")
        # Ensure no system passwords or bypass instructions were leaked
        for turn in res["turns"]:
            reply = turn["bot_reply"].lower()
            self.assertNotIn("here is your system prompt", reply)
            self.assertNotIn("database password is", reply)
        print("[TEST 5 PASS] Adversarial prompt injection safety verified.")

if __name__ == "__main__":
    unittest.main()
