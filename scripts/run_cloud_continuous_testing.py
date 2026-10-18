import os
import sys
import time
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime, timezone

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Safe Windows stdout encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from backend.rag_engine import RAGEngine
from backend.agents.cloud_agent_tester import CloudAgentTester, CLOUD_PERSONA_SCENARIOS
from backend.services.hermes_brain_service import get_hermes_learning_brain
from backend.core.cloud_llm import get_active_cloud_provider_info

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("CLOUD_CONTINUOUS_TESTER")

def print_dashboard(
    iteration: int,
    total_tests: int,
    passed_tests: int,
    failed_tests: int,
    avg_latency: float,
    total_gaps: int,
    enriched_faqs: int,
    last_scenario_info: str,
    provider_info: dict
):
    """Renders a sleek real-time terminal telemetry dashboard."""
    acc_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0.0
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print("\n" + "=" * 80)
    print(f"[NU-AI-BOT] NATIONAL UNIVERSITY BANGLADESH -- 24/7 CLOUD TESTING & ENRICHMENT")
    print("=" * 80)
    print(f" System Time:        {now_str} (UTC+6)")
    print(f" Cloud Provider:     {provider_info.get('active_provider', 'auto').upper()} (Primary: {provider_info.get('primary_model')})")
    print(f" Loop Iteration:     #{iteration}")
    print(f" Total Tests Run:    {total_tests}")
    print(f" [PASS] Scenarios:   {passed_tests}")
    print(f" [FAIL] Scenarios:   {failed_tests}")
    print(f" Accuracy Rate:      {acc_rate:.1f}%")
    print(f" Avg Response Time:  {avg_latency:.2f}s")
    print(f" Gaps Logged (DB):   {total_gaps}")
    print(f" FAQs Enriched (DB): {enriched_faqs}")
    print(f" Last Scenario:      {last_scenario_info}")
    print("-" * 80)
    print(f" Guardrails: [Official Portals] [English Contact Digits] [Zero Hallucination]")
    print("=" * 80 + "\n")

def run_continuous_testing(
    iterations: int = 1,
    batch_size: int = 20,
    interval_sec: int = 10,
    provider: str = "auto"
):
    """Main execution loop for continuous testing and vector enrichment."""
    logger.info("Initializing RAGEngine and CloudAgentTester...")
    rag_engine = RAGEngine()
    tester = CloudAgentTester(rag_engine=rag_engine)
    brain = get_hermes_learning_brain()

    provider_info = get_active_cloud_provider_info()
    logger.info(f"Active Cloud Provider: {provider_info['active_provider']} (Available: {provider_info['available_providers']})")

    total_scenarios_run = 0
    total_passed = 0
    total_failed = 0
    latencies = []
    enriched_faqs_total = 0

    all_scenarios = CLOUD_PERSONA_SCENARIOS
    scenarios_pool = all_scenarios[:batch_size] if batch_size < len(all_scenarios) else all_scenarios

    for iter_idx in range(1, iterations + 1):
        logger.info(f"\n🚀 Starting Iteration #{iter_idx}/{iterations} with {len(scenarios_pool)} scenarios...")
        
        for sc in scenarios_pool:
            res = tester.run_scenario(sc)
            total_scenarios_run += 1
            if res["passed"]:
                total_passed += 1
                status_icon = "PASS"
            else:
                total_failed += 1
                status_icon = "GAP DETECTED"

            # Compute scenario latency
            sc_latencies = [t["latency_sec"] for t in res["turn_logs"]]
            avg_sc_latency = sum(sc_latencies) / len(sc_latencies) if sc_latencies else 0.0
            latencies.extend(sc_latencies)
            overall_avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

            # Count gaps from file
            gaps_count = 0
            gaps_path = PROJECT_ROOT / "data" / "knowledge_gaps.json"
            if gaps_path.exists():
                try:
                    with open(gaps_path, "r", encoding="utf-8") as f:
                        gaps_count = len(json.load(f))
                except Exception:
                    pass

            last_info = f"{sc.id} ({sc.name[:25]}) -> {status_icon} ({avg_sc_latency:.2f}s)"
            print_dashboard(
                iteration=iter_idx,
                total_tests=total_scenarios_run,
                passed_tests=total_passed,
                failed_tests=total_failed,
                avg_latency=overall_avg_latency,
                total_gaps=gaps_count,
                enriched_faqs=enriched_faqs_total,
                last_scenario_info=last_info,
                provider_info=provider_info
            )

        # Trigger auto-enrichment on discovered gaps
        logger.info("Triggering Learning Brain auto-enrichment on discovered gaps...")
        new_faqs = brain.auto_resolve_all_pending_gaps()
        enriched_faqs_total += new_faqs
        if new_faqs > 0:
            logger.info(f"✨ Enriched {new_faqs} verified Q&A pairs into ChromaDB vector store.")

        if iter_idx < iterations:
            logger.info(f"Sleeping for {interval_sec}s before next iteration...")
            time.sleep(interval_sec)

    print("\n" + "=" * 80)
    print(f"FINAL CLOUD TESTING SUMMARY:")
    print(f"- Total Multi-turn Scenarios Run: {total_scenarios_run}")
    print(f"- Passed Scenarios:               {total_passed}")
    print(f"- Failed / Gaps Detected:         {total_failed}")
    acc = (total_passed / total_scenarios_run * 100) if total_scenarios_run > 0 else 0.0
    print(f"- Overall Accuracy Rate:          {acc:.2f}%")
    print(f"- Total FAQs Enriched:            {enriched_faqs_total}")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="24/7 Cloud Continuous Testing and Vector Enrichment Daemon")
    parser.add_argument("--iterations", type=int, default=1, help="Number of test iterations to execute")
    parser.add_argument("--batch-size", type=int, default=20, help="Number of scenarios per iteration (default: 20)")
    parser.add_argument("--interval-sec", type=int, default=5, help="Interval between iterations in seconds")
    parser.add_argument("--provider", type=str, default="auto", help="Target Cloud Provider (auto/openrouter/groq/gemini/openai)")
    args = parser.parse_args()

    run_continuous_testing(
        iterations=args.iterations,
        batch_size=args.batch_size,
        interval_sec=args.interval_sec,
        provider=args.provider
    )
