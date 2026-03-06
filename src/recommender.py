import logging
import threading
from dataclasses import dataclass

import pandas as pd

from src.config import SETTINGS
from src.data_loader import load_books
from src.embeddings import load_embedding_model
from src.vector_store import get_collection, reset_collection

logger = logging.getLogger(__name__)


@dataclass
class Recommendation:
    title: str
    authors: str
    categories: str
    score: float
    description: str


class BookRecommender:
    def __init__(self) -> None:
        self._initialized = False
        self._init_lock = threading.Lock()
        self._books_df: pd.DataFrame | None = None
        self._collection = None
        self._model = None

    @staticmethod
    def _build_ids(df: pd.DataFrame) -> list[str]:
        ids: list[str] = []
        seen: dict[str, int] = {}

        for idx, raw in enumerate(df["isbn13"].tolist()):
            base = str(raw).strip() if str(raw).strip() else f"row-{idx}"
            if base in seen:
                seen[base] += 1
                value = f"{base}-{seen[base]}"
            else:
                seen[base] = 0
                value = base
            ids.append(value)

        return ids

    def _rebuild_index(self, books: pd.DataFrame) -> None:
        logger.info("Rebuilding vector index for %s books", len(books))
        self._collection = reset_collection()

        texts = books["text"].tolist()
        ids = self._build_ids(books)
        titles = books["title"].tolist()
        authors = books["authors"].tolist()
        categories = books["categories"].tolist()
        descriptions = books["description"].tolist()

        for i in range(0, len(texts), SETTINGS.batch_size):
            batch_docs = texts[i : i + SETTINGS.batch_size]
            batch_ids = ids[i : i + SETTINGS.batch_size]
            batch_titles = titles[i : i + SETTINGS.batch_size]
            batch_authors = authors[i : i + SETTINGS.batch_size]
            batch_categories = categories[i : i + SETTINGS.batch_size]
            batch_descriptions = descriptions[i : i + SETTINGS.batch_size]
            batch_embeddings = self._model.encode(batch_docs, show_progress_bar=False).tolist()

            self._collection.add(
                ids=batch_ids,
                embeddings=batch_embeddings,
                documents=batch_docs,
                metadatas=[
                    {
                        "title": str(t),
                        "authors": str(a),
                        "categories": str(c),
                        "description": str(d)[:600],
                    }
                    for t, a, c, d in zip(
                        batch_titles,
                        batch_authors,
                        batch_categories,
                        batch_descriptions,
                    )
                ],
            )

    def initialize(self, force_reindex: bool = False) -> None:
        if self._initialized and not force_reindex:
            return

        with self._init_lock:
            if self._initialized and not force_reindex:
                return

            books = load_books(SETTINGS.data_path)
            self._model = load_embedding_model()
            self._collection = get_collection()

            current_count = self._collection.count()
            needs_reindex = force_reindex or current_count != len(books)
            if needs_reindex:
                self._rebuild_index(books)
            else:
                logger.info("Using existing vector index (%s records)", current_count)

            self._books_df = books
            self._initialized = True

    @staticmethod
    def _distance_to_score(distance: float) -> float:
        # Chroma distance: lower is better. Convert to bounded relevance score.
        return round(1.0 / (1.0 + max(distance, 0.0)), 4)

    def recommend_books(self, query: str, n_results: int | None = None) -> list[Recommendation]:
        if not self._initialized:
            self.initialize()

        cleaned = (query or "").strip()
        if not cleaned:
            raise ValueError("Please enter a search theme.")

        available = max(1, int(self._collection.count()))
        requested = n_results or SETTINGS.default_results
        n = max(1, min(int(requested), SETTINGS.top_k_max, available))

        query_embedding = self._model.encode(cleaned, show_progress_bar=False).tolist()
        results = self._collection.query(query_embeddings=[query_embedding], n_results=n)

        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        output: list[Recommendation] = []
        for meta, distance in zip(metadatas, distances):
            record = meta or {}
            output.append(
                Recommendation(
                    title=str(record.get("title", "Unknown Title")),
                    authors=str(record.get("authors", "Unknown Author")),
                    categories=str(record.get("categories", "Uncategorized")),
                    description=str(record.get("description", "No description available.")),
                    score=self._distance_to_score(float(distance)),
                )
            )

        return output


recommender_service = BookRecommender()
