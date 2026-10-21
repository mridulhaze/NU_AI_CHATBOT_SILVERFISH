import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from langchain_core.documents import Document

from db.sql_store import get_sql_store
from db.vector_store import get_vector_store
from .notices_scraper import NoticesScraper
from .admission_scraper import AdmissionScraper
from .results_scraper import ResultsScraper
from .ems_scraper import EMSScraper
from .ict_scraper import ICTScraper

logger = logging.getLogger("NU_SCHEDULER")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

_scheduler: BackgroundScheduler | None = None
_crawler_state = {
    "is_running": False,
    "last_run": None,
    "last_status": "idle",
    "total_pages_scraped": 0,
    "total_chunks_indexed": 0,
    "errors": []
}

def load_static_datasets() -> List[Document]:
    documents = []
    
    # 1. Load Master Knowledge Base JSON
    kb_file = DATA_DIR / "nu_knowledge_base.json"
    if kb_file.exists():
        try:
            with open(kb_file, "r", encoding="utf-8") as f:
                kb_data = json.load(f)
                
            u_info = kb_data.get("university_info", {})
            summary = f"# {u_info.get('name', 'National University')} ({u_info.get('name_bn', '')})\n"
            summary += f"- Established: {u_info.get('established')}\n"
            summary += f"- Location: {u_info.get('headquarters')}\n"
            summary += f"- Official Website: {u_info.get('official_website')}\n"
            summary += f"- Nature: {u_info.get('nature')}\n\n"
            
            for m in kb_data.get("modules", []):
                summary += f"## {m.get('topic')} ({m.get('topic_bn', '')})\n"
                summary += f"{m.get('content')}\n\n"
                
            documents.append(Document(page_content=summary, metadata={"source": "nu_knowledge_base.json", "category": "General"}))
            logger.info("Loaded static master knowledge base.")
        except Exception as e:
            logger.warning(f"Error loading nu_knowledge_base.json: {e}")

    # 2. Load Quick Links Catalog JSON
    links_file = DATA_DIR / "quick_links.json"
    if links_file.exists():
        try:
            with open(links_file, "r", encoding="utf-8") as f:
                links_data = json.load(f)
                
            links_summary = "# National University Official Portals & Quick Links Directory\n\n"
            for cat in links_data:
                links_summary += f"### {cat.get('icon', '')} {cat.get('category')} ({cat.get('category_bn', '')})\n"
                for l in cat.get("links", []):
                    links_summary += f"- **{l.get('title')} ({l.get('title_bn', '')})**: [{l.get('url')}]({l.get('url')}) - {l.get('description')}\n"
                    
            documents.append(Document(page_content=links_summary, metadata={"source": "quick_links.json", "category": "Portals"}))
            logger.info("Loaded static quick links directory.")
        except Exception as e:
            logger.warning(f"Error loading quick_links.json: {e}")
            
    return documents

def run_full_crawl() -> Dict[str, Any]:
    """
    Executes a polite full crawl across notices, admission, results, and ems.
    Inserts into SQLite and updates ChromaDB vector store.
    """
    global _crawler_state
    if _crawler_state["is_running"]:
        return {"status": "busy", "message": "Crawler is already running."}

    _crawler_state["is_running"] = True
    _crawler_state["last_status"] = "running"
    sql_store = get_sql_store()
    vector_store = get_vector_store()
    log_id = sql_store.start_crawl_log("All Sources (Notices, Admission, Results, EMS)")

    all_docs: List[Document] = []
    total_pages = 0
    total_new = 0
    errors = []

    try:
        # 1. Static base docs
        static_docs = load_static_datasets()
        all_docs.extend(static_docs)

        # 2. Notices
        try:
            notices_scraper = NoticesScraper()
            n_docs, n_pages, n_new = notices_scraper.scrape_notices()
            all_docs.extend(n_docs)
            total_pages += n_pages
            total_new += n_new
        except Exception as e:
            err_msg = f"NoticesScraper error: {e}"
            logger.error(err_msg)
            errors.append(err_msg)

        # 3. Admissions
        try:
            admission_scraper = AdmissionScraper()
            a_docs, a_pages, a_new = admission_scraper.scrape_admissions()
            all_docs.extend(a_docs)
            total_pages += a_pages
            total_new += a_new
        except Exception as e:
            err_msg = f"AdmissionScraper error: {e}"
            logger.error(err_msg)
            errors.append(err_msg)

        # 4. Results & Grading Rules
        try:
            results_scraper = ResultsScraper()
            r_docs, r_pages, r_new = results_scraper.scrape_results_metadata()
            all_docs.extend(r_docs)
            total_pages += r_pages
            total_new += r_new
        except Exception as e:
            err_msg = f"ResultsScraper error: {e}"
            logger.error(err_msg)
            errors.append(err_msg)

        # 5. EMS & Form Fill-up
        try:
            ems_scraper = EMSScraper()
            e_docs, e_pages, e_new = ems_scraper.scrape_ems_info()
            all_docs.extend(e_docs)
            total_pages += e_pages
            total_new += e_new
        except Exception as e:
            err_msg = f"EMSScraper error: {e}"
            logger.error(err_msg)
            errors.append(err_msg)

        # 6. ICT Department & Employee Directory
        try:
            ict_scraper = ICTScraper()
            i_docs, i_pages, i_new = ict_scraper.scrape_ict_info()
            all_docs.extend(i_docs)
            total_pages += i_pages
            total_new += i_new
        except Exception as e:
            err_msg = f"ICTScraper error: {e}"
            logger.error(err_msg)
            errors.append(err_msg)

        # 7. All University Offices & Departments (Registrar, Exam Controller, VC, Transport, Finance, etc.)
        try:
            from .departments_scraper import DepartmentsScraper
            dept_scraper = DepartmentsScraper()
            d_docs, d_stats = dept_scraper.scrape()
            all_docs.extend(d_docs)
            total_pages += d_stats.get("departments_scraped", 0)
            total_new += d_stats.get("total_employees_extracted", 0)
        except Exception as e:
            err_msg = f"DepartmentsScraper error: {e}"
            logger.error(err_msg)
            errors.append(err_msg)

        # 8. Homepage Dynamic Links & Category Exploration
        try:
            from .homepage_scraper import HomepageScraper
            hp_scraper = HomepageScraper()
            hp_docs, hp_pages, hp_new = hp_scraper.scrape_homepage_and_categories()
            all_docs.extend(hp_docs)
            total_pages += hp_pages
            total_new += hp_new
        except Exception as e:
            err_msg = f"HomepageScraper error: {e}"
            logger.error(err_msg)
            errors.append(err_msg)

        # 9. Index into Vector Store
        chunks_count = vector_store.split_and_add_documents(all_docs)

        # 10. Autonomous Hermes Learning Brain Cycle
        try:
            from backend.services.hermes_brain_service import get_hermes_brain
            hermes_brain = get_hermes_brain()
            hermes_res = hermes_brain.run_interactive_learning_cycle(limit_gaps=20)
            logger.info(f"Hermes Autonomous Learning Brain processed {hermes_res.get('resolved_gaps_count', 0)} knowledge gaps.")
        except Exception as eh:
            logger.warning(f"Hermes learning brain cycle warning: {eh}")


        status_str = "success" if not errors else "partial"
        sql_store.finish_crawl_log(
            log_id=log_id,
            status=status_str,
            pages_scraped=total_pages,
            new_items=total_new,
            errors="; ".join(errors)
        )

        _crawler_state.update({
            "is_running": False,
            "last_run": datetime.now().isoformat(),
            "last_status": status_str,
            "total_pages_scraped": total_pages,
            "total_chunks_indexed": chunks_count,
            "errors": errors
        })

        return {
            "status": status_str,
            "pages_scraped": total_pages,
            "new_items": total_new,
            "chunks_indexed": chunks_count,
            "errors": errors
        }

    except Exception as e:
        logger.error(f"Critical error during crawl: {e}")
        sql_store.finish_crawl_log(
            log_id=log_id,
            status="failed",
            pages_scraped=total_pages,
            new_items=total_new,
            errors=str(e)
        )
        _crawler_state.update({
            "is_running": False,
            "last_run": datetime.now().isoformat(),
            "last_status": "failed",
            "errors": [str(e)]
        })
        return {"status": "failed", "error": str(e)}

def sync_recent_notices(max_rows: int = 80) -> Dict[str, Any]:
    """
    Executes a fast, high-priority synchronization of recent notices & news from:
    - https://www.nu.ac.bd/recent-news-notice.php
    - https://www.nu.ac.bd/
    - Examination & Admission boards
    Inserts fresh notices into SQLite with date_iso and indexes into ChromaDB.
    Can be run as an hourly cron job or called directly via 'Update Recent' admin button.
    """
    global _crawler_state
    if _crawler_state["is_running"]:
        return {"status": "busy", "message": "Crawler or synchronizer is already running."}

    _crawler_state["is_running"] = True
    _crawler_state["last_status"] = "running_recent_sync"
    sql_store = get_sql_store()
    vector_store = get_vector_store()
    log_id = sql_store.start_crawl_log("Recent Notices & News Sync (Hourly Cron / Immediate)")

    try:
        scraper = NoticesScraper()
        docs, pages_scraped, new_items, recent_items = scraper.scrape_recent_notices(max_rows=max_rows)
        
        chunks_count = 0
        if docs:
            chunks_count = vector_store.split_and_add_documents(docs)

        latest_notice = recent_items[0] if recent_items else None

        sql_store.finish_crawl_log(
            log_id=log_id,
            status="success",
            pages_scraped=pages_scraped,
            new_items=new_items,
            errors=""
        )

        now_iso = datetime.now().isoformat()
        _crawler_state.update({
            "is_running": False,
            "last_run": now_iso,
            "last_status": "success",
            "last_sync_type": "recent_notices",
            "total_pages_scraped": _crawler_state.get("total_pages_scraped", 0) + pages_scraped,
            "total_chunks_indexed": _crawler_state.get("total_chunks_indexed", 0) + chunks_count,
            "latest_notice": latest_notice,
            "errors": []
        })

        return {
            "status": "success",
            "message": "Recent notices and knowledge base updated successfully.",
            "pages_scraped": pages_scraped,
            "new_items": new_items,
            "chunks_indexed": chunks_count,
            "latest_notice": latest_notice,
            "synced_at": now_iso
        }
    except Exception as e:
        logger.error(f"Error during recent notices sync: {e}")
        sql_store.finish_crawl_log(
            log_id=log_id,
            status="failed",
            pages_scraped=0,
            new_items=0,
            errors=str(e)
        )
        _crawler_state.update({
            "is_running": False,
            "last_run": datetime.now().isoformat(),
            "last_status": "failed",
            "errors": [str(e)]
        })
        return {"status": "failed", "error": str(e)}

def start_scheduler(crawl_interval_minutes: int = 60):
    """Start periodic background crawler every 60 minutes (hourly cron)."""
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler()
        # Hourly cron job syncing freshest notices and news from nu.ac.bd
        _scheduler.add_job(
            sync_recent_notices,
            "interval",
            minutes=crawl_interval_minutes,
            id="nu_recent_sync_hourly_job",
            replace_existing=True
        )
        _scheduler.start()
        logger.info(f"Background hourly cron scheduler started (syncing every {crawl_interval_minutes} minutes).")

def stop_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Background crawler scheduler stopped.")

def get_crawler_status() -> Dict[str, Any]:
    return _crawler_state
