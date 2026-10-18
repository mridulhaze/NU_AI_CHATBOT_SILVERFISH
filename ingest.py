"""
Comprehensive Knowledge Ingestion & Vector Pipeline for National University Bangladesh (nu.ac.bd)
Handles:
1. Live scraping of notices, admissions, examination routines, syllabi, and official directories.
2. Structured tabular data extraction (fees, dates, codes, grading criteria).
3. Online PDF notice downloading & text extraction with hash-based deduplication.
4. Curated National University baseline knowledge seed with verified official portal URLs:
   - Student Services (TC, Certificate, Marksheet, Transcript, Correction): http://103.113.200.68/nu-app/
   - Admission Portal: http://app11.nu.edu.bd/
   - EMS Portal: http://ems.nu.ac.bd/
   - Results: https://results.nu.ac.bd/
5. English digit phone normalization and resilient embedding into Chroma vector store.
"""

import os
import io
import time
import json
import hashlib
import argparse
import logging
import urllib3
import requests
from bs4 import BeautifulSoup
import pdfplumber
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Suppress InsecureRequestWarning for unverified SSL chains
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Modern LangChain imports
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("NU_INGEST_PIPELINE")

# 1. Load environment variables
ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

API_KEY = os.getenv("GEMINI_API_KEY", "")
DB_DIR = str(Path(__file__).resolve().parent / "nu_vector_db")
DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
CACHE_FILE = DATA_DIR / "ingest_hash_cache.json"

# Strict Official Portals
OFFICIAL_PORTALS = {
    "STUDENT_SERVICES": "http://103.113.200.68/nu-app/",
    "ADMISSION": "http://app11.nu.edu.bd/",
    "EMS": "http://ems.nu.ac.bd/",
    "RESULTS": "https://results.nu.ac.bd/",
    "MAIN": "https://www.nu.ac.bd/"
}

BN_TO_EN_DIGITS = {
    '০': '0', '১': '1', '২': '2', '৩': '3', '৪': '4',
    '৫': '5', '৬': '6', '৭': '7', '৮': '8', '৯': '9'
}

def convert_bn_to_en_digits(text: str) -> str:
    """Converts Bengali numerals (০-৯) to standard English numerals (0-9)."""
    if not text:
        return ""
    return "".join(BN_TO_EN_DIGITS.get(ch, ch) for ch in str(text))

def load_hash_cache() -> Dict[str, str]:
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_hash_cache(cache: Dict[str, str]):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Could not save hash cache: {e}")

def compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def scrape_nu_notices(url: str, category_name: str) -> List[Dict[str, Any]]:
    """Extract structured notice rows and tabular info from NU notice pages."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    notices = []
    try:
        response = requests.get(url, headers=headers, timeout=(3, 6), verify=False)
        response.raise_for_status()
        response.encoding = response.apparent_encoding or "utf-8"
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Look for table rows containing notices
        rows = soup.find_all("tr")
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 2:
                row_text = " | ".join([c.get_text(strip=True) for c in cols if c.get_text(strip=True)])
                link = row.find("a")
                href = link.get("href") if link else None
                if href and not href.startswith("http"):
                    href = f"https://www.nu.ac.bd/{href.lstrip('/')}"
                if row_text:
                    notices.append({
                        "category": category_name,
                        "text": convert_bn_to_en_digits(row_text),
                        "url": href or url,
                        "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
    except Exception as e:
        logger.warning(f"Skipping notice page {url} (Error: {e})")
    return notices

def extract_tables_from_url(url: str) -> List[str]:
    """Extract structured HTML tables (e.g. fee schedules, routine dates) into markdown tables."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    extracted_tables = []
    try:
        resp = requests.get(url, headers=headers, timeout=(3, 6), verify=False)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
        tables = soup.find_all("table")
        for idx, table in enumerate(tables):
            rows = table.find_all("tr")
            if len(rows) < 2:
                continue
            table_md = []
            for r_idx, row in enumerate(rows):
                cells = [c.get_text(strip=True).replace("\n", " ") for c in row.find_all(["th", "td"])]
                if cells:
                    table_md.append("| " + " | ".join(cells) + " |")
                    if r_idx == 0:
                        table_md.append("| " + " | ".join(["---"] * len(cells)) + " |")
            if len(table_md) > 2:
                extracted_tables.append("\n".join(table_md))
    except Exception as e:
        logger.debug(f"No extra tables extracted from {url}: {e}")
    return extracted_tables

def scrape_nu_webpage_clean(url: str) -> str:
    """Extract concise, clean text from an NU HTML page."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=(3, 6), verify=False)
        response.raise_for_status()
        response.encoding = response.apparent_encoding or "utf-8"
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove junk tags
        for tag in soup(["script", "style", "select", "option", "nav", "footer", "header", "noscript", "svg", "iframe"]):
            tag.decompose()
            
        lines = []
        for elem in soup.find_all(["h1", "h2", "h3", "h4", "p", "li", "span"]):
            text = elem.get_text(strip=True)
            if len(text) > 10 and text not in lines:
                lines.append(convert_bn_to_en_digits(text))
                
        return "\n".join(lines[:120]) # Cap to most relevant content
    except Exception as e:
        logger.warning(f"Skipping {url} (Error: {e})")
        return ""

def extract_pdf_text_from_url(pdf_url: str) -> str:
    """Download and extract raw text from online PDF notices."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        response = requests.get(pdf_url, headers=headers, timeout=(4, 8), verify=False)
        response.raise_for_status()
        with pdfplumber.open(io.BytesIO(response.content)) as pdf:
            pages_text = [page.extract_text() or "" for page in pdf.pages[:5]] # Read first 5 pages
            text = "\n".join(pages_text)
        return convert_bn_to_en_digits(text.strip())
    except Exception as e:
        logger.warning(f"Error reading PDF {pdf_url}: {e}")
        return ""

def get_official_seed_documents() -> List[Document]:
    """Master National University Knowledge Base with strictly verified official URLs and guidelines."""
    seed_nu_info = """
# National University of Bangladesh (জাতীয় বিশ্ববিদ্যালয়) - Official Master Knowledge Base

## Overview & Official Portals
- Established: 1992 by an Act of Parliament of Bangladesh.
- Type: Apex affiliating university for tertiary higher education across all 64 districts in Bangladesh.
- Main Campus: Board Bazar, Gazipur-1704, Dhaka Division, Bangladesh.
- Official Website: https://www.nu.ac.bd
- Official Student Services Portal (TC, Certificate, Marksheet, Transcript, Correction): http://103.113.200.68/nu-app/
- Official Admissions Portal (Honours, Degree, Masters, Professional): http://app11.nu.edu.bd/
- Official Form Fill-up & EMS Portal: http://ems.nu.ac.bd/
- Results & Result Archive Portals:
  * https://results.nu.ac.bd/ (Primary Result Archive)
  * http://www.nu.ac.bd/results/ (Alternative Result Server)

## Key Leadership & Administration
- Vice-Chancellor (উপাচার্য): Professor Dr. ASM Amanullah (প্রফেসর ড. এ এস এম আমানুল্লাহ). Email: vc@nu.ac.bd, dramanullah@hotmail.com.
- Pro-Vice-Chancellors (উপ-উপাচার্য): Prof. Md. Lutfor Rahaman and Professor Dr. Mohammad Ali Zinnah.
- Treasurer (কোষাধ্যক্ষ / ট্রেজারার): Professor Dr. Md. Nazmul Hossain / Prof. Dr. A. T. M. Zafrul Azam.
- Registrar (রেজিস্ট্রার): Molla Mahfuz Al-Hossain (মোল্লা মাহফুজ আল-হোসেন).

## Important Departments & Office Portals
- Registrar Office (রেজিস্ট্রার দপ্তর): https://www.nu.ac.bd/Registrar-office.php
- Controller of Examination (পরীক্ষা নিয়ন্ত্রক দপ্তর): https://www.nu.ac.bd/exam-controller-office.php
- ICT Department (আইসিটি দপ্তর): https://www.nu.ac.bd/ict-department.php
- Vice-Chancellor Office (উপাচার্য দপ্তর): https://www.nu.ac.bd/vice-chancellor-office.php
- Pro-Vice-Chancellor Office (উপ-উপাচার্য দপ্তর): https://www.nu.ac.bd/Pro-Vice-Chancellor-Office.php
- Treasurer Office (ট্রেজারার দপ্তর): https://www.nu.ac.bd/Treasurer-office.php
- Public Relations (জনসংযোগ ও তথ্য দপ্তর): https://www.nu.ac.bd/public-relations.php
- Finance & Accounts (অর্থ ও হিসাব দপ্তর): https://www.nu.ac.bd/finance-account.php
- Library Department (গ্রন্থাগার দপ্তর): https://www.nu.ac.bd/library-department.php

## Student Services (TC, Certificate, Transcript, Correction)
- **Official Portal**: http://103.113.200.68/nu-app/
- **Transfer Certificate (TC / কলেজ পরিবর্তন)**:
  * Application must be submitted through http://103.113.200.68/nu-app/.
  * Both current college (releasing) and destination college (receiving) must approve online.
  * Fee must be paid via Sonali Seba.
- **Original & Provisional Certificates (মূল ও সাময়িক সনদপত্র)**:
  * Application via http://103.113.200.68/nu-app/.
  * Required attachments: Admit card, registration card, marksheet copy.
  * Fees paid via Sonali Seba pay-slip.
- **Academic Transcripts & Marksheet Verification**:
  * Apply on http://103.113.200.68/nu-app/ with registration and roll number.
- **Document & Name Correction (নাম ও তথ্য সংশোধন)**:
  * Application submitted online on http://103.113.200.68/nu-app/ with SSC/HSC certificate copies.

## Admission System & Merit Lists
- **Official Admission Portal**: http://app11.nu.edu.bd/
- Admission is 100% merit-based calculated from SSC GPA (40%) + HSC GPA (60%). No separate written admission test for regular honours.
- Merit Steps: 1st Merit List -> 2nd Merit List & Subject Migration -> 1st Release Slip -> 2nd Release Slip.
- Release Slip: Candidates unselected in merit lists or who cancelled previous admission can apply to 3 to 5 eligible colleges on http://app11.nu.edu.bd/.

## Examination, Form Fill-Up & EMS System
- **Official EMS Portal**: http://ems.nu.ac.bd/
- Students complete online form fill-up via http://ems.nu.ac.bd/, print the confirmation copy, submit it to their college authority, and pay the board/college fees via Sonali Seba or college cash desk.
- In case of EMS password lockout, contact the college admin or submit a support token to the ICT Cell.

## Results & Rescrutiny (খাতা পুনর্নিরীক্ষণ)
- **Online Result Checking**: Visit https://results.nu.ac.bd/ or http://www.nu.ac.bd/results/
- **SMS Result Checking Format (Send to 16222)**:
  * Honours 1st Year: `NU H1 Roll_Number` -> send to 16222
  * Honours 2nd Year: `NU H2 Roll_Number` -> send to 16222
  * Honours 3rd Year: `NU H3 Roll_Number` -> send to 16222
  * Honours 4th Year: `NU H4 Roll_Number` -> send to 16222
  * Degree Pass: `NU DEG Roll_Number` -> send to 16222
  * Masters Final: `NU MF Roll_Number` -> send to 16222
  * Masters Preliminary: `NU MP Roll_Number` -> send to 16222
- **Answer Script Re-scrutiny (খাতা চ্যালেঞ্জ)**:
  * Apply online within 30 days after result publication via http://103.113.200.68/nu-app/ or https://www.nu.ac.bd/.
  * Fee paid via Sonali Seba slip. Results published within 30-45 days.

## Grading System & CGPA Scale
- 80% to 100%: A+ (Grade Point: 4.00)
- 75% to <80%: A (Grade Point: 3.75)
- 70% to <75%: A- (Grade Point: 3.50)
- 65% to <70%: B+ (Grade Point: 3.25)
- 60% to <65%: B (Grade Point: 3.00)
- 55% to <60%: B- (Grade Point: 2.75)
- 50% to <55%: C+ (Grade Point: 2.50)
- 45% to <50%: C (Grade Point: 2.25)
- 40% to <45%: D (Grade Point: 2.00)
- Below 40%: F (Grade Point: 0.00)
- Minimum passing CGPA for graduation: 2.00

## Lost Documents & Duplicate Registration Card
- **Procedure for Lost Registration Card / Admit Card**:
  1. File a General Diary (GD) with the local Police Station stating loss of document.
  2. Apply online via Student ERP Portal: http://103.113.200.68/nu-app/
  3. Upload copy of Police GD and college verification certificate.
  4. Generate and pay Sonali Seba fee slip.
  5. The duplicate card is forwarded to the student's college or available for download.

## Subject Migration & College Transfer Rules
- **Subject Migration in Admission**:
  * If selected in 1st Merit List, candidate can opt for auto-migration to higher-preferred subjects upon paying initial admission fee on http://app11.nu.edu.bd/.
  * If satisfied with current subject, student must stop migration by toggling migration off in the admission dashboard.
- **College Transfer (TC)**:
  * Permitted in 2nd or 3rd year for valid reasons (parent transfer, change of residence, marriage).
  * Requires clearance/approval from current college principal and accepting college principal via http://103.113.200.68/nu-app/.

## Improvement Examination (মানোন্নয়ন পরীক্ষা) Rules
- Students securing 'C', 'D', or 'F' grade in any course can appear in the improvement exam with the immediate next regular batch.
- Improvement exam form fill-up is completed through http://ems.nu.ac.bd/.
- The higher grade between original and improvement exam is counted in the final CGPA.

## University Governance & Working Hours
- **Chancellor (আচার্য)**: The Honorable President of the People's Republic of Bangladesh.
- **Vice-Chancellor (উপাচার্য)**: Professor Dr. ASM Amanullah.
- **Headquarters Location**: Board Bazar, Gazipur-1704.
- **Official Office Working Hours**: Sunday through Thursday, 09:00 AM to 05:00 PM (Weekly Holidays: Friday & Saturday).
- **Physical Visits**: Most services (Certificates, TC, Corrections) are 100% online via http://103.113.200.68/nu-app/ and students do NOT need to visit Gazipur campus physically.
"""
    return [
        Document(
            page_content=seed_nu_info,
            metadata={
                "source": "nu_master_knowledge_base",
                "type": "seed_data",
                "title": "National University Official Master Guide",
                "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        )
    ]

def build_knowledge_base(crawl_live: bool = True, force_rebuild: bool = False) -> int:
    """Builds and updates the vector knowledge base with deduplication."""
    cache = load_hash_cache()
    documents: List[Document] = []

    # 1. Add Master Seed
    logger.info("1. Loading curated National University master knowledge base...")
    documents.extend(get_official_seed_documents())

    # 2. Live Crawling if requested
    if crawl_live:
        logger.info("2. Scraping National University portals (Notices, Admissions, Routines)...")
        target_pages = [
            ("https://www.nu.ac.bd/recent-news-notice.php", "General & Recent Notices"),
            ("https://www.nu.ac.bd/examination-notice.php", "Examination & Routine Notices"),
            ("https://www.nu.ac.bd/admission-notice.php", "Admission Notices"),
            ("https://www.nu.ac.bd/all-department.php", "University Departments & Faculties")
        ]

        all_pdf_links = []
        for page_url, category in target_pages:
            notices = scrape_nu_notices(page_url, category)
            logger.info(f"  - Scraped {len(notices)} notices from {category}")
            
            top_notices = notices[:25]
            if top_notices:
                notice_summary = f"# National University Notices - {category} ({time.strftime('%Y-%m-%d')})\n"
                for n in top_notices:
                    notice_summary += f"- {n['text']} (Link: {n['url']})\n"
                    if n["url"].endswith(".pdf") and len(all_pdf_links) < 5:
                        all_pdf_links.append(n["url"])
                
                content_hash = compute_hash(notice_summary)
                if force_rebuild or cache.get(page_url) != content_hash:
                    documents.append(Document(
                        page_content=notice_summary,
                        metadata={"source": page_url, "category": category, "type": "live_notices", "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}
                    ))
                    cache[page_url] = content_hash

        # Extract PDF contents
        logger.info("3. Extracting online PDF circulars...")
        for pdf_url in all_pdf_links:
            pdf_hash_key = f"pdf:{pdf_url}"
            if not force_rebuild and pdf_hash_key in cache:
                continue
            pdf_text = extract_pdf_text_from_url(pdf_url)
            if pdf_text and len(pdf_text) > 40:
                logger.info(f"  - Extracted {len(pdf_text)} chars from {pdf_url}")
                documents.append(Document(
                    page_content=f"# National University Official Circular (PDF)\nSource: {pdf_url}\n\n{pdf_text}",
                    metadata={"source": pdf_url, "type": "pdf_circular", "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}
                ))
                cache[pdf_hash_key] = compute_hash(pdf_text)

    # 4. Text Chunking
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators=["\n\n", "\n", "। ", ". ", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    logger.info(f"Created {len(chunks)} chunks for vector embedding.")

    # 5. Embeddings and Vector DB Insertion
    from db.vector_store import ResilientEmbeddings
    embeddings = ResilientEmbeddings(api_key=API_KEY.strip() if API_KEY else None)

    if force_rebuild and os.path.exists(DB_DIR):
        logger.info(f"Force rebuilding: Removing old DB at {DB_DIR}...")
        import shutil
        shutil.rmtree(DB_DIR, ignore_errors=True)

    vector_store = Chroma(
        persist_directory=DB_DIR,
        embedding_function=embeddings
    )
    
    batch_size = 25
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(chunks) + batch_size - 1) // batch_size
        logger.info(f"Embedding batch {batch_num}/{total_batches} ({len(batch)} chunks)...")
        try:
            vector_store.add_documents(documents=batch)
        except Exception as err:
            logger.warning(f"Error adding batch {batch_num}: {err}")

    save_hash_cache(cache)
    logger.info(f"SUCCESS: Ingested {len(chunks)} chunks into Chroma vector store at '{DB_DIR}'.")
    return len(chunks)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="National University Knowledge Base Ingestion Pipeline")
    parser.add_argument("--seed-only", action="store_true", help="Only embed curated seed data without live crawling")
    parser.add_argument("--force-rebuild", action="store_true", help="Delete and rebuild entire vector database")
    args = parser.parse_args()

    build_knowledge_base(crawl_live=not args.seed_only, force_rebuild=args.force_rebuild)