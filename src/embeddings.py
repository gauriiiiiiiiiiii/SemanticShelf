import os
from functools import lru_cache

from sentence_transformers import SentenceTransformer

from src.config import SETTINGS

# Prevent tokenizer thread oversubscription in constrained deployments.
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


@lru_cache(maxsize=1)
def load_embedding_model() -> SentenceTransformer:
    model_kwargs = {}
    if SETTINGS.embedding_cache_dir:
        model_kwargs["cache_folder"] = SETTINGS.embedding_cache_dir
    return SentenceTransformer(SETTINGS.embedding_model_name, **model_kwargs)
