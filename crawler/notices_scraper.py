import logging
import urllib.parse
from bs4 import BeautifulSoup
from typing import List, Tuple
from langchain_core.documents import Document

from .base_scraper import BaseScraper
from db.sql_store import get_sql_store

logger = logging.getLogger("NU_NOTICES_SCRAPER")

TARGET_BOARDS = [
    ("https://www.nu.ac.bd/recent-news-notice.php", "General Notice"),
    ("https://www.nu.ac.bd/examination-notice.php", "Exam Notice"),
    ("https://www.nu.ac.bd/admission-notice.php", "Admission Notice")
]

class NoticesScraper(BaseScraper):
    def scrape_notices(self) -> Tuple[List[Document], int, int]:
        """
        Scrapes notices from target boards.
        Returns: (documents, pages_scraped, new_or_updated_items)
        """
        sql_store = get_sql_store()
        documents = []
        pages_scraped = 0
        new_items_count = 0

        for url, category in TARGET_BOARDS:
            html = self.fetch_url(url)
            if not html:
                logger.warning(f"Could not fetch notice board: {url}")
                continue

            pages_scraped += 1
            soup = BeautifulSoup(html, "html.parser")
            rows = soup.find_all("tr")
            board_notices = []

            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 2:
                    col0 = cols[0].get_text(strip=True)
                    col1 = cols[1].get_text(strip=True)
                    months = ["january","february","march","april","may","june","july","august","september","october","november","december"]
                    if any(m in col1.lower() for m in months) or (len(col1) <= 25 and any(c.isdigit() for c in col1)):
                        title_col = col0
                        date_col = col1
                    elif any(m in col0.lower() for m in months) or (len(col0) <= 25 and any(c.isdigit() for c in col0)):
                        title_col = col1
                        date_col = col0
                    else:
                        title_col = col0
                        date_col = col1
                    
                    a_tag = row.find("a")
                    href = a_tag.get("href") if a_tag else ""
                    full_url = urllib.parse.urljoin("https://www.nu.ac.bd/", href) if href else url
                    pdf_url = full_url if full_url.lower().endswith(".pdf") else None

                    raw_text = f"Title: {title_col}\nDate: {date_col}\nCategory: {category}\nLink: {full_url}"
                    
                    # If this is a PDF and one of the top 3 recent notices, try extracting snippet text
                    if pdf_url and len(board_notices) < 3:
                        pdf_text = self.fetch_pdf_text(pdf_url, max_pages=2)
                        if pdf_text:
                            raw_text += f"\n\nPDF Summary Content:\n{pdf_text[:1200]}"

                    is_updated = sql_store.upsert_notice(
                        title=title_col,
                        url=full_url,
                        pdf_url=pdf_url,
                        category=category,
                        published_date=date_col,
                        raw_text=raw_text
                    )
                    if is_updated:
                        new_items_count += 1

                    board_notices.append({
                        "title": title_col,
                        "date": date_col,
                        "url": full_url,
                        "pdf_url": pdf_url,
                        "raw_text": raw_text
                    })

            # Create consolidated document for RAG
            if board_notices:
                summary = f"# National University Official Notice Board: {category}\n\n"
                for item in board_notices[:25]:
                    summary += f"- **[{item['date']}] {item['title']}**\n  Official Link: {item['url']}\n\n"
                
                doc = Document(
                    page_content=summary,
                    metadata={"source": url, "category": category, "type": "notice_board"}
                )
                documents.append(doc)

        logger.info(f"Notice scraping completed. Pages: {pages_scraped}, New items: {new_items_count}")
        return documents, pages_scraped, new_items_count
