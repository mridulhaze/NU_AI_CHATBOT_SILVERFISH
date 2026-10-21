import re
import logging
import urllib.parse
import itertools
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

def _slice_table_html(html: str, target_rows: int = 100) -> str:
    """
    Slices large HTML containing thousands of table rows to only the first `target_rows` </tr> occurrences.
    Prevents BeautifulSoup from stalling for 30+ seconds building AST for 12,000+ historical rows.
    """
    if not html or len(html) < 200000:
        return html
    matches = list(itertools.islice(re.finditer(r'</tr\s*>', html, re.IGNORECASE), target_rows))
    if matches and len(matches) >= target_rows:
        cutoff = matches[-1].end()
        return html[:cutoff] + "</tbody></table></body></html>"
    return html

def _extract_row_cells(cols) -> Optional[Tuple[str, str]]:
    """
    Extracts (title, date) from a table row's <td> elements, handling:
    - 3-column layouts: [Title, Post Date, Download]
    - 4-column layouts: [Sl, Title, Publish Date, Download]
    - Inverted layouts: [Date, Title, Link]
    - Filters out header rows and serial numbers
    """
    if not cols or len(cols) < 2:
        return None
    cell_texts = [c.get_text(strip=True) for c in cols]
    
    # Filter header rows
    row_text_lower = " ".join(cell_texts).lower()
    if any(h in row_text_lower for h in ["post date", "publish date", "download"]) and any(c.lower() in ["sl", "sl.", "title", "post date", "publish date", "ক্রমিক", "বিবরণ"] for c in cell_texts[:2]):
        return None
    
    # If first column is serial number (e.g. 1, 2, or 'Sl')
    if len(cell_texts) >= 3 and (cell_texts[0].isdigit() or cell_texts[0].lower() in ["sl", "sl.", "নং"]):
        title_cand, date_cand = cell_texts[1], cell_texts[2]
    else:
        title_cand, date_cand = cell_texts[0], cell_texts[1]

    months = ["january","february","march","april","may","june","july","august","september","october","november","december"]
    if any(m in title_cand.lower() for m in months) and not any(m in date_cand.lower() for m in months):
        title_cand, date_cand = date_cand, title_cand

    if not title_cand or title_cand.lower() in ["title", "post date", "download", "sl", "sl.", "serial", "ক্রমিক", "বিবরণ"]:
        return None
    return title_cand, date_cand

class NoticesScraper(BaseScraper):
    def scrape_notices(self, max_rows_per_board: int = 150) -> Tuple[List[Document], int, int]:
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

            target_rows = rows[:max_rows_per_board] if max_rows_per_board else rows

            for row in target_rows:
                cols = row.find_all("td")
                extracted = _extract_row_cells(cols)
                if not extracted:
                    continue
                title_col, date_col = extracted

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

    def scrape_recent_notices(self, max_rows: int = 80) -> Tuple[List[Document], int, int, List[dict]]:
        """
        High-speed, prioritized scraper for freshest notices and announcements from:
        1. https://www.nu.ac.bd/recent-news-notice.php (primary live notice board)
        2. https://www.nu.ac.bd/ (homepage live announcements & events fallback/supplement)
        3. https://www.nu.ac.bd/examination-notice.php (exam notices)
        4. https://www.nu.ac.bd/admission-notice.php (admission notices)

        Returns: (documents, pages_scraped, new_or_updated_items, latest_notices)
        """
        sql_store = get_sql_store()
        documents = []
        pages_scraped = 0
        new_items_count = 0
        all_recent_items = []
        errors = []

        # 1. Scrape Primary Board: recent-news-notice.php
        primary_url = "https://www.nu.ac.bd/recent-news-notice.php"
        primary_fetched = False
        try:
            html = self.fetch_url(primary_url)
            if html:
                primary_fetched = True
                pages_scraped += 1
                parse_html = _slice_table_html(html, max_rows + 20)
                soup = BeautifulSoup(parse_html, "html.parser")
                rows = soup.find_all("tr")
                board_items = []

                for row in rows[:max_rows]:
                    cols = row.find_all("td")
                    extracted = _extract_row_cells(cols)
                    if not extracted:
                        continue
                    title_col, date_col = extracted

                    a_tag = row.find("a")
                    href = a_tag.get("href") if a_tag else ""
                    full_url = urllib.parse.urljoin("https://www.nu.ac.bd/", href) if href else primary_url
                    pdf_url = full_url if full_url.lower().endswith(".pdf") else None

                    raw_text = f"Title: {title_col}\nDate: {date_col}\nCategory: Recent Notice\nLink: {full_url}"

                    is_updated = sql_store.upsert_notice(
                        title=title_col,
                        url=full_url,
                        pdf_url=pdf_url,
                        category="Recent Notice",
                        published_date=date_col,
                        raw_text=raw_text
                    )
                    if is_updated:
                        new_items_count += 1

                    item_data = {
                        "title": title_col,
                        "date": date_col,
                        "url": full_url,
                        "pdf_url": pdf_url,
                        "raw_text": raw_text
                    }
                    board_items.append(item_data)
                    all_recent_items.append(item_data)

                if board_items:
                    summary = "# National University Recent News & Notice Board (nu.ac.bd/recent-news-notice.php)\n\n"
                    for item in board_items[:30]:
                        summary += f"- **[{item['date']}] {item['title']}**\n  Official Link: {item['url']}\n\n"
                    
                    documents.append(Document(
                        page_content=summary,
                        metadata={"source": primary_url, "category": "Recent Notice", "type": "recent_notice_board"}
                    ))
        except Exception as e:
            err = f"Error scraping {primary_url}: {e}"
            logger.error(err)
            errors.append(err)

        # 2. Scrape Homepage (https://www.nu.ac.bd/) urgent notices & announcements
        home_url = "https://www.nu.ac.bd/"
        try:
            home_html = self.fetch_url(home_url)
            if home_html:
                pages_scraped += 1
                soup = BeautifulSoup(home_html, "html.parser")
                home_items = []
                from backend.services.notice_service import parse_notice_date

                # Target official urgent notice box and announcement tickers
                urgent_boxes = soup.find_all(lambda tag: tag.name in ['div', 'ul', 'marquee'] and any(k in str(tag.get('class', '')).lower() or k in str(tag.get('id', '')).lower() for k in ['urgent', 'notice', 'ticker', 'marquee']))
                for box in urgent_boxes:
                    for a in box.find_all("a", href=True):
                        raw_txt = a.get_text(" ", strip=True)
                        href = a["href"].strip()
                        if not raw_txt or len(raw_txt) < 10:
                            continue
                        full_url = urllib.parse.urljoin(home_url, href)
                        pdf_url = full_url if full_url.lower().endswith(".pdf") else None

                        # Extract date from text if 'প্রকাশকালঃ' is present
                        date_str = ""
                        title_clean = raw_txt
                        m_date = re.search(r'প্রকাশকাল\s*[:ঃ]\s*([০-৯a-zA-Z\s,]+)', raw_txt)
                        if m_date:
                            date_str = m_date.group(1).strip()
                            title_clean = re.sub(r'প্রকাশকাল\s*[:ঃ]\s*([০-৯a-zA-Z\s,]+)', '', raw_txt).strip(' \t\n\r"\'')

                        dt = parse_notice_date(date_str, title_clean, full_url)
                        if not date_str:
                            date_str = dt.strftime("%B %d, %Y")
                        iso_str = dt.strftime("%Y-%m-%d")

                        raw_text = f"Title: {title_clean}\nDate: {date_str}\nCategory: Urgent Notice\nLink: {full_url}"
                        is_updated = sql_store.upsert_notice(
                            title=title_clean,
                            url=full_url,
                            pdf_url=pdf_url,
                            category="Urgent Notice",
                            published_date=date_str,
                            raw_text=raw_text,
                            date_iso=iso_str
                        )
                        if is_updated:
                            new_items_count += 1
                        home_items.append({"title": title_clean, "date": date_str, "url": full_url, "pdf_url": pdf_url})
                        all_recent_items.append({"title": title_clean, "date": date_str, "url": full_url, "pdf_url": pdf_url})

                if home_items and not primary_fetched:
                    # Homepage acted as primary fallback
                    summary = "# National University Homepage Urgent Notices & Announcements (nu.ac.bd)\n\n"
                    for item in home_items[:25]:
                        summary += f"- **[{item['date']}] {item['title']}**\n  Official Link: {item['url']}\n\n"
                    documents.append(Document(
                        page_content=summary,
                        metadata={"source": home_url, "category": "Urgent Notice", "type": "homepage_urgent"}
                    ))
        except Exception as e:
            logger.warning(f"Error scraping homepage {home_url}: {e}")

        # 3. Quick scrape of Examination & Admission boards (top 20 each)
        for url, category in [
            ("https://www.nu.ac.bd/examination-notice.php", "Exam Notice"),
            ("https://www.nu.ac.bd/admission-notice.php", "Admission Notice")
        ]:
            try:
                html = self.fetch_url(url)
                if not html:
                    continue
                pages_scraped += 1
                parse_html = _slice_table_html(html, 40)
                soup = BeautifulSoup(parse_html, "html.parser")
                rows = soup.find_all("tr")
                sub_items = []
                for row in rows[:25]:
                    cols = row.find_all("td")
                    extracted = _extract_row_cells(cols)
                    if not extracted:
                        continue
                    title_col, date_col = extracted

                    a_tag = row.find("a")
                    href = a_tag.get("href") if a_tag else ""
                    full_url = urllib.parse.urljoin("https://www.nu.ac.bd/", href) if href else url
                    pdf_url = full_url if full_url.lower().endswith(".pdf") else None
                    raw_text = f"Title: {title_col}\nDate: {date_col}\nCategory: {category}\nLink: {full_url}"

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
                    sub_items.append({"title": title_col, "date": date_col, "url": full_url})
                    all_recent_items.append({"title": title_col, "date": date_col, "url": full_url})

                if sub_items:
                    summary = f"# National University {category} Board\n\n"
                    for item in sub_items[:15]:
                        summary += f"- **[{item['date']}] {item['title']}**\n  Official Link: {item['url']}\n\n"
                    documents.append(Document(
                        page_content=summary,
                        metadata={"source": url, "category": category, "type": "sub_board"}
                    ))
            except Exception as e:
                logger.warning(f"Error scraping {url}: {e}")

        # Fallback for offline / network failure: retrieve existing top notices from database
        if not all_recent_items:
            logger.info("Live crawl produced 0 items (offline or network error). Falling back to SQLite recent notices.")
            db_notices = sql_store.get_recent_notices(limit=20)
            for n in db_notices:
                all_recent_items.append({
                    "title": n.get("title", ""),
                    "date": n.get("published_date", ""),
                    "url": n.get("url", ""),
                    "pdf_url": n.get("pdf_url")
                })
            if db_notices:
                summary = "# National University Recent Notices (Offline / Cached Knowledge Base)\n\n"
                for item in all_recent_items[:15]:
                    summary += f"- **[{item['date']}] {item['title']}**\n  Official Link: {item['url']}\n\n"
                documents.append(Document(
                    page_content=summary,
                    metadata={"source": primary_url, "category": "Recent Notice", "type": "cached_fallback"}
                ))

        # Deduplicate and sort all_recent_items chronologically descending (newest first)
        seen_urls = set()
        unique_recent_items = []
        for item in all_recent_items:
            u = item.get("url", "")
            if u and u not in seen_urls:
                seen_urls.add(u)
                unique_recent_items.append(item)
            elif not u:
                unique_recent_items.append(item)

        from backend.services.notice_service import parse_notice_date
        unique_recent_items.sort(
            key=lambda x: parse_notice_date(x.get("date", ""), x.get("title", ""), x.get("url", "")),
            reverse=True
        )
        all_recent_items = unique_recent_items

        logger.info(f"scrape_recent_notices finished. Pages: {pages_scraped}, New items: {new_items_count}, Total collected: {len(all_recent_items)}")
        return documents, pages_scraped, new_items_count, all_recent_items
