"""
Autonomous 24/7 Knowledge Enrichment & Analysis Orchestrator
Continuously executes data analysis, QA synthesis, vector ingestion, and changelog logging in the background.
"""

import time
import asyncio
import logging
import threading
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from .scraped_data_analyzer import get_scraped_data_analyzer
from .knowledge_enricher import get_knowledge_enricher
from .knowledge_provenance import get_knowledge_provenance
from backend.services.hermes_brain_service import get_hermes_brain

logger = logging.getLogger("NU_AUTONOMOUS_24X7_WORKER")

class Autonomous24x7Worker:
    def __init__(self, interval_seconds: int = 600):
        self.interval_seconds = interval_seconds
        self.analyzer = get_scraped_data_analyzer()
        self.enricher = get_knowledge_enricher()
        self.provenance = get_knowledge_provenance()
        self.hermes_brain = get_hermes_brain()
        self.is_running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.last_cycle_time: Optional[str] = None
        self.total_cycles = 0
        self.total_pages_processed = 0
        self.total_qa_synthesized = 0
        self.total_gaps_resolved = 0

    def start_24x7_worker(self):
        """Starts the 24/7 background worker thread if not already running."""
        if self.is_running:
            logger.info("24/7 Autonomous Worker is already running.")
            return

        self.is_running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._worker_loop, daemon=True, name="NU_24x7_Knowledge_Worker")
        self._thread.start()
        logger.info(f"🚀 24/7 Autonomous Knowledge Enrichment Agent started (interval: {self.interval_seconds}s).")

    def stop_24x7_worker(self):
        """Stops the 24/7 background worker."""
        if not self.is_running:
            return
        self.is_running = False
        self._stop_event.set()
        logger.info("⏹️ 24/7 Autonomous Knowledge Enrichment Agent stopped.")

    def _worker_loop(self):
        """Main daemon worker loop."""
        # Initial run on startup
        try:
            self.run_enrichment_cycle()
        except Exception as e:
            logger.error(f"Error in initial 24/7 enrichment cycle: {e}")

        while not self._stop_event.is_set():
            # Wait for next interval
            if self._stop_event.wait(self.interval_seconds):
                break

            try:
                self.run_enrichment_cycle()
            except Exception as e:
                logger.error(f"Error in 24/7 enrichment loop: {e}")

    def run_enrichment_cycle(self, batch_size: int = 10) -> Dict[str, Any]:
        """
        Executes a single end-to-end analysis & enrichment cycle over un-analyzed scraped pages.
        """
        start_t = time.time()
        now_iso = datetime.now(timezone.utc).isoformat()
        logger.info(f"🔄 Starting 24/7 Knowledge Enrichment Cycle at {now_iso} (Batch Size: {batch_size})...")

        unanalyzed = self.analyzer.get_unanalyzed_pages(limit=batch_size)
        if not unanalyzed:
            logger.info("✓ No unanalyzed scraped pages found. Knowledge base is up to date.")
            self.last_cycle_time = now_iso
            return {
                "status": "idle",
                "message": "No new pages to enrich.",
                "processed": 0,
                "timestamp": now_iso
            }

        processed_count = 0
        qa_count = 0

        for page in unanalyzed:
            try:
                page_id = page["id"]
                url = page["url"]
                logger.info(f"Analyzing page #{page_id}: {url}")

                # Step 1: Analyze & Synthesize
                analysis = self.analyzer.analyze_page(page)

                # Step 2: Ingest & Enrich Multi-tier Knowledge
                self.enricher.enrich_knowledge(analysis)

                # Step 3: Record Provenance & Changelog
                self.provenance.record_update(analysis)

                # Step 4: Mark page as enriched in SQLite
                self.analyzer.mark_page_enriched(page_id)

                processed_count += 1
                qa_count += len(analysis.get("qa_pairs", []))

            except Exception as e:
                logger.error(f"Error processing page #{page.get('id')}: {e}", exc_info=True)

        # Step 5: Process any pending knowledge gaps via Hermes Learning Brain
        gaps_resolved = 0
        try:
            brain_res = self.hermes_brain.run_interactive_learning_cycle(limit_gaps=5)
            gaps_resolved = brain_res.get("resolved_gaps_count", 0)
            self.total_gaps_resolved += gaps_resolved
        except Exception as e:
            logger.warning(f"Hermes Brain gap resolution warning during 24/7 cycle: {e}")

        self.last_cycle_time = now_iso
        self.total_cycles += 1
        self.total_pages_processed += processed_count
        self.total_qa_synthesized += qa_count
        duration_s = time.time() - start_t

        logger.info(f"✅ 24/7 Knowledge Cycle Finished in {duration_s:.2f}s: Enriched {processed_count} pages, {qa_count} QA pairs, {gaps_resolved} gaps resolved.")

        return {
            "status": "success",
            "pages_processed": processed_count,
            "qa_synthesized": qa_count,
            "gaps_resolved": gaps_resolved,
            "duration_seconds": round(duration_s, 2),
            "timestamp": now_iso
        }

    def get_status(self) -> Dict[str, Any]:
        """Returns the current 24/7 worker telemetry and state."""
        return {
            "is_running": self.is_running,
            "interval_seconds": self.interval_seconds,
            "last_cycle_time": self.last_cycle_time or "Never",
            "total_cycles": self.total_cycles,
            "total_pages_processed": self.total_pages_processed,
            "total_qa_synthesized": self.total_qa_synthesized,
            "total_gaps_resolved": self.total_gaps_resolved,
            "status_display": "🟢 24/7 Active & Running" if self.is_running else "⚪ Idle"
        }

_autonomous_24x7_worker_instance: Optional[Autonomous24x7Worker] = None

def get_24x7_worker() -> Autonomous24x7Worker:
    global _autonomous_24x7_worker_instance
    if _autonomous_24x7_worker_instance is None:
        _autonomous_24x7_worker_instance = Autonomous24x7Worker(interval_seconds=600)  # Runs every 10 minutes
    return _autonomous_24x7_worker_instance
