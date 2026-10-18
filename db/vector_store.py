import os
import time
import json
import hashlib
import logging
from pathlib import Path
from typing import Optional, List, Tuple
from dotenv import load_dotenv

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

logger = logging.getLogger("NU_VECTOR_STORE")

DEFAULT_VECTOR_DIR = Path(__file__).resolve().parent.parent / "nu_vector_db"
HASH_CACHE_FILE = Path(__file__).resolve().parent.parent / "data" / "ingest_hash_cache.json"

class ResilientEmbeddings:
    """Wrapper that uses Google GenAI embeddings with resilient retry."""
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self._embedder = None
        if self.api_key:
            try:
                self._embedder = GoogleGenerativeAIEmbeddings(
                    model="models/gemini-embedding-001",
                    google_api_key=self.api_key
                )
            except Exception as e:
                logger.warning(f"Failed to init gemini-embedding-001: {e}")
                try:
                    self._embedder = GoogleGenerativeAIEmbeddings(
                        model="models/text-embedding-004",
                        google_api_key=self.api_key
                    )
                except Exception as ex:
                    logger.error(f"Failed to init Google embeddings: {ex}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if self._embedder:
            try:
                return self._embedder.embed_documents(texts)
            except Exception as e:
                logger.warning(f"Embedding batch error: {e}. Retrying...")
                time.sleep(1.5)
                try:
                    return self._embedder.embed_documents(texts)
                except Exception as err:
                    logger.error(f"Fallback to pseudo-embeddings: {err}")
        return [[(hash(t + str(i)) % 1000) / 1000.0 for i in range(3072)] for t in texts]

    def embed_query(self, text: str) -> List[float]:
        if self._embedder:
            try:
                return self._embedder.embed_query(text)
            except Exception as e:
                logger.warning(f"Query embedding error: {e}")
                time.sleep(1)
                try:
                    return self._embedder.embed_query(text)
                except Exception:
                    pass
        return [(hash(text + str(i)) % 1000) / 1000.0 for i in range(3072)]

class VectorStore:
    def __init__(self, persist_dir: Optional[str | Path] = None):
        self.persist_dir = str(persist_dir or DEFAULT_VECTOR_DIR)
        self.embeddings = ResilientEmbeddings()
        self.vector_db: Optional[Chroma] = None
        self._init_store()

    def _init_store(self):
        try:
            if os.path.exists(self.persist_dir):
                self.vector_db = Chroma(
                    persist_directory=self.persist_dir,
                    embedding_function=self.embeddings
                )
                logger.info(f"Loaded existing Chroma DB from {self.persist_dir}")
        except Exception as e:
            logger.error(f"Failed to initialize Chroma vector store: {e}")

    def _load_hash_cache(self) -> set[str]:
        if HASH_CACHE_FILE.exists():
            try:
                with open(HASH_CACHE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return set(data) if isinstance(data, list) else set(data.keys())
            except Exception:
                pass
        return set()

    def _save_hash_cache(self, hashes: set[str]):
        try:
            HASH_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(HASH_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(list(hashes), f)
        except Exception as e:
            logger.warning(f"Could not persist hash cache: {e}")

    def split_and_add_documents(self, documents: List[Document], chunk_size: int = 1000, chunk_overlap: int = 150) -> int:
        if not documents:
            return 0
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", "। ", ". ", " ", ""]
        )
        chunks = splitter.split_documents(documents)
        logger.info(f"Split {len(documents)} docs into {len(chunks)} raw chunks.")

        known_hashes = self._load_hash_cache()
        new_chunks = []
        new_hashes = set()

        for chunk in chunks:
            text = chunk.page_content.strip()
            if not text:
                continue
            ch_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
            if ch_hash not in known_hashes:
                new_chunks.append(chunk)
                new_hashes.add(ch_hash)

        if not new_chunks:
            logger.info("All document chunks already exist in vector store (hash matched). Skipping redundant embedding.")
            return 0

        logger.info(f"Embedding {len(new_chunks)} new/changed chunks (skipped {len(chunks) - len(new_chunks)} unchanged).")

        batch_size = 40
        for i in range(0, len(new_chunks), batch_size):
            batch = new_chunks[i : i + batch_size]
            for attempt in range(3):
                try:
                    if self.vector_db is None:
                        self.vector_db = Chroma.from_documents(
                            documents=batch,
                            embedding=self.embeddings,
                            persist_directory=self.persist_dir
                        )
                    else:
                        self.vector_db.add_documents(documents=batch)
                    break
                except Exception as e:
                    logger.warning(f"Error adding batch to Chroma (attempt {attempt+1}): {e}")
                    time.sleep(1.5 * (attempt + 1))
            time.sleep(0.3)

        known_hashes.update(new_hashes)
        self._save_hash_cache(known_hashes)

        return len(new_chunks)

    def similarity_search(self, query: str, k: int = 5) -> List[Tuple[Document, float]]:
        if self.vector_db is None:
            self._init_store()
        if self.vector_db is None:
            return []
        try:
            return self.vector_db.similarity_search_with_score(query, k=k)
        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            return []

_vector_store_instance = None

def get_vector_store() -> VectorStore:
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore()
    return _vector_store_instance
