import io
import time
import hashlib
import logging
from typing import Optional, Tuple
import requests
from bs4 import BeautifulSoup
import pdfplumber

logger = logging.getLogger("NU_SCRAPER")

DEFAULT_HEADERS = {
    "User-Agent": "NU-Academic-AI-Crawler/2.0 (+https://nu.ac.bd/ bot; contact: ai-support@nu.ac.bd)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,bn;q=0.8",
}

class BaseScraper:
    def __init__(self, timeout: int = 15, delay: float = 1.0):
        self.timeout = timeout
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)

    def fetch_url(self, url: str) -> Optional[str]:
        """Fetch URL content safely with retries and TLS fallback."""
        for attempt in range(3):
            try:
                time.sleep(self.delay)
                response = self.session.get(url, timeout=self.timeout, verify=False)
                response.raise_for_status()
                # National University servers serve UTF-8. Avoid apparent_encoding guessing MacCyrillic.
                response.encoding = "utf-8"
                return response.text
            except Exception as e:
                logger.warning(f"Error fetching {url} (attempt {attempt + 1}): {e}")
                time.sleep(1.5 * (attempt + 1))
        return None

    def fetch_pdf_text(self, pdf_url: str, max_pages: int = 2) -> Optional[str]:
        """Download and extract text from a PDF file."""
        try:
            time.sleep(self.delay)
            res = self.session.get(pdf_url, timeout=self.timeout + 5, verify=False)
            res.raise_for_status()
            with pdfplumber.open(io.BytesIO(res.content)) as pdf:
                pages_text = []
                for page in pdf.pages[:max_pages]:
                    txt = page.extract_text()
                    if txt:
                        pages_text.append(txt.strip())
                full_text = "\n".join(pages_text).strip()
                return full_text if len(full_text) > 20 else None
        except Exception as e:
            logger.debug(f"Failed to parse PDF from {pdf_url}: {e}")
            return None

    @staticmethod
    def clean_text(text: str) -> str:
        if not text:
            return ""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)

    @staticmethod
    def hash_content(content: str) -> str:
        return hashlib.md5(content.strip().encode("utf-8")).hexdigest()
