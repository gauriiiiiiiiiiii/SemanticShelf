import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.config import Settings as ChromaSettings

from src.config import SETTINGS


_CLIENT_SETTINGS = ChromaSettings(anonymized_telemetry=False)


def _create_client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(path=SETTINGS.chroma_path, settings=_CLIENT_SETTINGS)


def get_collection() -> Collection:
    client = _create_client()
    return client.get_or_create_collection(name=SETTINGS.collection_name)


def reset_collection() -> Collection:
    client = _create_client()
    try:
        client.delete_collection(name=SETTINGS.collection_name)
    except Exception:
        pass
    return client.create_collection(name=SETTINGS.collection_name)
