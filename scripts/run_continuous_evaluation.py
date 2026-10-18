"""
Autonomous 24/7 Continuous Evaluation & Knowledge Enrichment Daemon
National University Bangladesh AI Assistant

Usage:
  python scripts/run_continuous_evaluation.py [--iterations N] [--interval SEC] [--auto-enrich]

Features:
1. Simulates diverse student personas and multi-turn conversations.
2. Judges responses for factual correctness, empathy, latency, and official portal compliance.
3. Automatically triggers Hermes Learning Brain to resolve gaps and update ChromaDB vector store.
4. Renders a live terminal telemetry dashboard with metrics and audit log.
"""

import os
import sys
import time
import signal
import argparse
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.agents.hermes_tester import get_hermes_tester, SIMULATION_SCENARIOS
from backend.services.hermes_brain_service import get_hermes_brain
from db.sql_store import get_sql_store
from db.vector_store import get_vector_store
from token_service.db import init_token_database

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("CONTINUOUS_EVALUATION_DAEMON")

running = True

def handle_signal(sig, frame):
    global running
    print("\n[STOP] Termination signal received. Gracefully shutting down evaluation daemon...")
    running = False

signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

def print_dashboard(
    iteration: int,
    total_scenarios_tested: int,
    total_passed: int,
    total_failed: int,
    accuracy_rate: float,
    avg_latency: float,
    total_gaps_logged: int,
    total_faqs_enriched: int,
    last_scenario_status: str
):
    """Renders a clean, informative terminal dashboard."""
    print("\n" + "=" * 80)
    print("[NU-AI-BOT] NATIONAL UNIVERSITY BANGLADESH AI ASSISTANT -- 24/7 HERMES EVALUATION DAEMON")
    print("=" * 80)
    print(f" System Time:        {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (UTC+6)")
    print(f" Loop Iteration:     #{iteration}")
    print(f" Total Tests Run:    {total_scenarios_tested}")
    print(f" [PASS] Scenarios:   {total_passed}")
    print(f" [FAIL] Scenarios:   {total_failed}")
    print(f" Accuracy Rate:      {accuracy_rate:.1f}%")
    print(f" Avg Response Time:  {avg_latency:.2f}s")
    print(f" Gaps Logged (DB):   {total_gaps_logged}")
    print(f" FAQs Enriched (DB): {total_faqs_enriched}")
    print(f" Last Scenario:      {last_scenario_status}")
    print("-" * 80)
    print(" Guardrails: [Official Portals] [English Contact Digits] [Zero Hallucination]")
    print("=" * 80)

def run_continuous_evaluation(
    max_iterations: Optional[int] = None,
    interval_sec: int = 15,
    auto_enrich: bool = True,
    batch_size: Optional[int] = None
):
    init_token_database()
    tester = get_hermes_tester()
    brain = get_hermes_brain()
    sql_store = get_sql_store()

    iteration = 0
    total_scenarios_tested = 0
    total_passed = 0
    total_failed = 0
    total_latency_accum = 0.0
    total_gaps_logged = 0
    total_faqs_enriched = 0
    last_scenario_status = "Initialized"

    scenarios = SIMULATION_SCENARIOS
    if batch_size and batch_size < len(scenarios):
        scenarios = scenarios[:batch_size]

    logger.info(f"Starting Continuous 24/7 Hermes Simulation Loop with {len(scenarios)} scenarios...")

    while running:
        iteration += 1
        iter_passed = 0
        iter_latency = 0.0

        for scn in scenarios:
            if not running:
                break

            res = tester.run_scenario(scn)
            total_scenarios_tested += 1
            if res["passed"]:
                total_passed += 1
                iter_passed += 1
            else:
                total_failed += 1

            iter_latency += res["average_latency_sec"]
            total_latency_accum += res["average_latency_sec"]
            status_symbol = "✅ PASS" if res["passed"] else "⚠️ GAP DETECTED"
            last_scenario_status = f"{scn['scenario_id']} ({scn['persona'][:25]}) -> {status_symbol} ({res['average_latency_sec']}s)"

            # Refresh and display dashboard
            acc = (total_passed / total_scenarios_tested) * 100.0 if total_scenarios_tested > 0 else 0.0
            avg_lat = total_latency_accum / total_scenarios_tested if total_scenarios_tested > 0 else 0.0
            
            # Count gaps from DB
            try:
                gaps = sql_store.get_gap_queue(limit=100)
                total_gaps_logged = len(gaps)
            except Exception:
                pass

            print_dashboard(
                iteration=iteration,
                total_scenarios_tested=total_scenarios_tested,
                total_passed=total_passed,
                total_failed=total_failed,
                accuracy_rate=acc,
                avg_latency=avg_lat,
                total_gaps_logged=total_gaps_logged,
                total_faqs_enriched=total_faqs_enriched,
                last_scenario_status=last_scenario_status
            )

        # Trigger Autonomous Knowledge Brain Enrichment if enabled
        if auto_enrich and running:
            logger.info("🧠 Triggering Hermes Learning Brain auto-enrichment on discovered gaps...")
            enrich_result = brain.run_interactive_learning_cycle(limit_gaps=5)
            newly_resolved = enrich_result.get("resolved_gaps_count", 0)
            total_faqs_enriched += newly_resolved
            if newly_resolved > 0:
                logger.info(f"✨ Enriched {newly_resolved} verified Q&A pairs into ChromaDB vector store.")

        if max_iterations and iteration >= max_iterations:
            print(f"\n🎉 Completed specified {max_iterations} iteration(s) successfully.")
            break

        if running:
            print(f"\n⏳ Waiting {interval_sec} seconds before next evaluation cycle...")
            for _ in range(interval_sec):
                if not running:
                    break
                time.sleep(1)

    print("\n🏁 Final Evaluation Summary:")
    final_acc = (total_passed / total_scenarios_tested) * 100.0 if total_scenarios_tested > 0 else 0.0
    final_lat = total_latency_accum / total_scenarios_tested if total_scenarios_tested > 0 else 0.0
    print(f"• Total Tests Completed:  {total_scenarios_tested}")
    print(f"• Overall Accuracy Rate:   {final_acc:.2f}%")
    print(f"• Average Response Time:  {final_lat:.2f}s")
    print(f"• Total Knowledge Gaps:    {total_gaps_logged}")
    print(f"• Enriched Vector FAQs:   {total_faqs_enriched}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="24/7 Hermes Continuous Evaluation & Knowledge Enrichment Daemon")
    parser.add_argument("--iterations", type=int, default=None, help="Maximum number of test cycles (default: continuous)")
    parser.add_argument("--interval-sec", type=int, default=15, help="Sleep interval in seconds between cycles")
    parser.add_argument("--batch-size", type=int, default=None, help="Number of scenarios to run per cycle")
    parser.add_argument("--no-auto-enrich", action="store_true", help="Disable automatic gap enrichment into vector DB")
    args = parser.parse_args()

    run_continuous_evaluation(
        max_iterations=args.iterations,
        interval_sec=args.interval_sec,
        auto_enrich=not args.no_auto_enrich,
        batch_size=args.batch_size
    )
