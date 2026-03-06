import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _get_bool(name: str, default: str) -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: str) -> int:
    value = os.getenv(name, default).strip()
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be an integer, got: {value}") from exc


@dataclass(frozen=True)
class Settings:
    data_path: str = os.getenv("BOOKS_DATA_PATH", "data/books.csv")
    chroma_path: str = os.getenv("CHROMA_PATH", "vector_db/chroma_db")
    collection_name: str = os.getenv("CHROMA_COLLECTION", "books")
    embedding_model_name: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    embedding_cache_dir: str = os.getenv("EMBEDDING_CACHE_DIR", "")
    batch_size: int = _get_int("BATCH_SIZE", "512")
    default_results: int = _get_int("DEFAULT_RESULTS", "5")
    top_k_max: int = _get_int("TOP_K_MAX", "10")

    app_host: str = os.getenv("APP_HOST", "127.0.0.1")
    app_port: int = _get_int("APP_PORT", "7860")
    app_share: bool = _get_bool("APP_SHARE", "false")
    app_debug: bool = _get_bool("APP_DEBUG", "false")

    def __post_init__(self) -> None:
        if self.batch_size <= 0:
            raise ValueError("BATCH_SIZE must be > 0")
        if self.default_results <= 0:
            raise ValueError("DEFAULT_RESULTS must be > 0")
        if self.top_k_max <= 0:
            raise ValueError("TOP_K_MAX must be > 0")
        if self.default_results > self.top_k_max:
            raise ValueError("DEFAULT_RESULTS must be <= TOP_K_MAX")
        if not (1 <= self.app_port <= 65535):
            raise ValueError("APP_PORT must be between 1 and 65535")
        if not self.collection_name.strip():
            raise ValueError("CHROMA_COLLECTION must not be empty")
        if not self.embedding_model_name.strip():
            raise ValueError("EMBEDDING_MODEL must not be empty")


SETTINGS = Settings()
