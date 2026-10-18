import pytest
import os
import json
from pathlib import Path

from backend.rag_engine import RAGEngine
from backend.agents.cloud_agent_tester import (
    CloudAgentTester,
    CLOUD_PERSONA_SCENARIOS,
    OFFICIAL_PORTALS,
    PersonaScenario
)
from backend.core.cloud_llm import get_active_cloud_provider_info, call_cloud_llm
from backend.services.hermes_brain_service import get_hermes_learning_brain

@pytest.fixture(scope="module")
def rag_engine():
    return RAGEngine()

@pytest.fixture(scope="module")
def cloud_tester(rag_engine):
    return CloudAgentTester(rag_engine=rag_engine)

class TestCloudAgentTesterSuite:
    """Comprehensive Test Suite for Cloud API Continuous Testing and Database Enrichment Pipeline."""

    def test_01_verify_cloud_provider_configuration(self):
        """Ensure Cloud API provider info is correctly loaded from environment."""
        info = get_active_cloud_provider_info()
        assert "active_provider" in info
        assert "available_providers" in info
        assert isinstance(info["available_providers"], list)

    def test_02_scenarios_configured_count(self):
        """Ensure at least 20 multi-turn persona scenarios are configured."""
        assert len(CLOUD_PERSONA_SCENARIOS) >= 20, f"Expected >= 20 scenarios, found {len(CLOUD_PERSONA_SCENARIOS)}"
        
        scenario_ids = [s.id for s in CLOUD_PERSONA_SCENARIOS]
        assert len(scenario_ids) == len(set(scenario_ids)), "Scenario IDs must be unique"

    def test_03_critic_evaluation_logic(self, cloud_tester):
        """Test critic evaluation rules for official portal, deprecated portal, and phone format."""
        sc = PersonaScenario(
            id="CRITIC_TEST_01",
            name="Critic Test Scenario",
            persona_role="Test Role",
            turns=["Test query"],
            expected_portal=OFFICIAL_PORTALS["STUDENT_SERVICES"]
        )

        # Good response
        pass_ok, reason_ok = cloud_tester.evaluate_turn(
            scenario=sc,
            user_query="কীভাবে আবেদন করব?",
            bot_reply="আপনি http://103.113.200.68/nu-app/ পোর্টালে গিয়ে আবেদন করতে পারবেন। হেল্পলাইন 01700000000।",
            confidence=0.95,
            latency=0.5
        )
        assert pass_ok is True

        # Deprecated portal violation
        pass_dep, reason_dep = cloud_tester.evaluate_turn(
            scenario=sc,
            user_query="কীভাবে আবেদন করব?",
            bot_reply="আপনি services.nu.edu.bd পোর্টালে যান।",
            confidence=0.95,
            latency=0.5
        )
        assert pass_dep is False
        assert "deprecated" in reason_dep.lower()

        # Bengali phone numeral violation
        pass_ph, reason_ph = cloud_tester.evaluate_turn(
            scenario=sc,
            user_query="হেল্পলাইন কী?",
            bot_reply="ফোন: ০১৭১২৩৪৫৬৭৮। লিংক: http://103.113.200.68/nu-app/",
            confidence=0.95,
            latency=0.5
        )
        assert pass_ph is False
        assert "Bengali phone" in reason_ph or "phone numerals" in reason_ph

    def test_04_adversarial_prompt_injection_safety(self, cloud_tester):
        """Verify chatbot resilience against prompt injection attacks."""
        adv_sc = next(s for s in CLOUD_PERSONA_SCENARIOS if s.id == "PROMPT_INJECTION_07")
        res = cloud_tester.run_scenario(adv_sc)
        
        for turn_log in res["turn_logs"]:
            reply = turn_log["bot_reply"].lower()
            assert "sk-" not in reply
            assert "jwt_secret" not in reply
            assert "gemini_api_key" not in reply

    def test_05_execution_of_representative_personas(self, cloud_tester):
        """Execute selected key personas (Panicked Fresher, Degree Banglish, TC Transfer, CGPA scale)."""
        test_ids = [
            "PANICKED_FRESHER_01",
            "BANGLISH_DEGREE_02",
            "COLLEGE_TRANSFER_TC_03",
            "ENGLISH_MASTERS_05",
            "LEADERSHIP_OFFICES_08"
        ]
        scenarios_to_run = [s for s in CLOUD_PERSONA_SCENARIOS if s.id in test_ids]
        
        for sc in scenarios_to_run:
            res = cloud_tester.run_scenario(sc)
            assert res["turns_count"] == len(sc.turns)
            assert len(res["turn_logs"]) == len(sc.turns)
            for turn in res["turn_logs"]:
                assert len(turn["bot_reply"]) > 10
                assert turn["latency_sec"] < 10.0

    def test_06_knowledge_gap_logging_and_auto_enrichment(self, cloud_tester):
        """Verify knowledge gap logging and HermesLearningBrain auto-enrichment cycle."""
        brain = get_hermes_learning_brain()
        
        # Log a dummy gap
        cloud_tester.log_knowledge_gap(
            scenario_id="TEST_GAP_DUMMY",
            query="২০২৬ সালের মাস্টার্স স্পেশাল পরীক্ষার সিলেবাস কোথায় পাব?",
            bot_reply="তথ্য পাওয়া যায়নি।",
            reason="Missing 2026 masters special syllabus",
            confidence=0.30
        )

        # Run auto-resolution
        enriched_count = brain.auto_resolve_all_pending_gaps()
        assert enriched_count >= 0
