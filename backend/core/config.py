import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

class CoreSettings:
    PROJECT_NAME: str = "National University AI Assistant & MCP Platform"
    VERSION: str = "3.0.0"
    
    # Environment & Paths
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = BASE_DIR / "data"
    STATIC_DIR: Path = BASE_DIR / "static"
    DOCS_DIR: Path = BASE_DIR / "docs"
    SKILLS_DIR: Path = BASE_DIR / "skills"
    
    # Database Configuration (Environment-driven, default to SQLite in data dir)
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'nu_tokens.db'}")
    KNOWLEDGE_DB_PATH: Path = BASE_DIR / "data" / "nu_assistant.db"
    
    # Vector Database Configuration
    VECTOR_DB_TYPE: str = os.getenv("VECTOR_DB_TYPE", "chroma")  # chroma, pgvector, qdrant
    VECTOR_DB_DIR: Path = BASE_DIR / "nu_vector_db"
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.75"))
    
    # AI Engine Keys & Models
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    PRIMARY_MODEL: str = os.getenv("PRIMARY_MODEL", "gemini-2.5-flash")
    FALLBACK_MODELS: list[str] = [
        "gemini-2.5-flash",
        "gemini-1.5-flash",
        "gemini-flash-latest"
    ]
    EMBEDDING_MODEL: str = "models/gemini-embedding-001"
    
    # Cloud AI Providers (OpenRouter, Groq, OpenAI, Gemini)
    CLOUD_API_PROVIDER: str = os.getenv("CLOUD_API_PROVIDER", "auto")  # auto, openrouter, groq, gemini, openai
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "nousresearch/hermes-3-llama-3.1-8b")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # Security & Authentication
    JWT_SECRET: str = os.getenv("JWT_SECRET", "nu-ai-assistant-super-secure-token-2026")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    MCP_AUTH_SECRET: str = os.getenv("MCP_AUTH_SECRET", "mcp-secret-nu-2026")
    CREDENTIAL_ENCRYPTION_KEY: str = os.getenv("CREDENTIAL_ENCRYPTION_KEY", "nu-credential-aes-gcm-master-key-2026")
    
    # Crawler & Background Schedules
    CRAWL_INTERVAL_HOURS: int = int(os.getenv("CRAWL_INTERVAL_HOURS", "4"))
    ENRICH_INTERVAL_HOURS: int = int(os.getenv("ENRICH_INTERVAL_HOURS", "8"))
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))

settings = CoreSettings()
