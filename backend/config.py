import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

class Settings:
    PROJECT_NAME: str = "NU AI — Smart Academic Assistant"
    VERSION: str = "2.0.0"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    PRIMARY_MODEL: str = os.getenv("PRIMARY_MODEL", "gemini-3.1-flash-lite")
    FALLBACK_MODELS: list[str] = [
        "gemini-3.5-flash-lite",
        "gemini-3-flash-preview",
        "gemini-flash-latest"
    ]
    EMBEDDING_MODEL: str = "models/gemini-embedding-001"
    
    BASE_DIR: Path = BASE_DIR
    DB_PATH: Path = BASE_DIR / "data" / "nu_assistant.db"
    VECTOR_DB_DIR: Path = BASE_DIR / "nu_vector_db"
    DATA_DIR: Path = BASE_DIR / "data"
    STATIC_DIR: Path = BASE_DIR / "static"
    
    CRAWL_INTERVAL_HOURS: int = int(os.getenv("CRAWL_INTERVAL_HOURS", "1"))
    CRAWL_INTERVAL_MINUTES: int = int(os.getenv("CRAWL_INTERVAL_MINUTES", "60"))
    ENRICH_INTERVAL_HOURS: int = int(os.getenv("ENRICH_INTERVAL_HOURS", "1"))
    
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "45"))

    # Model Hyperparameters & Session Constraints
    TEMPERATURE: float = float(os.getenv("MODEL_TEMPERATURE", "0.7"))
    MAX_OUTPUT_TOKENS: int = int(os.getenv("MAX_OUTPUT_TOKENS", "2048"))
    TOP_P: float = float(os.getenv("MODEL_TOP_P", "0.95"))
    REQUEST_TIMEOUT_SECONDS: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "15"))
    MEMORY_WINDOW_TURNS: int = int(os.getenv("MEMORY_WINDOW_TURNS", "10"))

settings = Settings()

