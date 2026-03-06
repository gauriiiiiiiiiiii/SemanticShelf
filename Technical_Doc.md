# Technical Documentation - SemanticShelf

## 1. System Architecture

The application follows a layered modular architecture:

1. Presentation Layer (`app.py`)
- Gradio Blocks UI accepts user intent and displays ranked recommendations.
- Handles user interaction, UI rendering, and error-safe result messaging.

2. Application/Service Layer (`src/recommender.py`)
- Owns lifecycle of model loading, vector index initialization, and query execution.
- Provides a `BookRecommender` service abstraction and `Recommendation` DTO.

3. Data + Infrastructure Layer
- Dataset source: `data/books.csv`
- Embedding model: Sentence Transformers model from Hugging Face Hub or local cache.
- Vector store: Chroma persistent local collection (`vector_db/chroma_db`).

High-level data path:
- User query -> embedding model -> Chroma similarity search -> ranked metadata -> HTML cards in UI.

## 2. Technology Stack

- Python 3.13+
- Gradio (UI/Web runtime)
- Pandas (dataset ingestion and preprocessing)
- Sentence Transformers (semantic embeddings)
- ChromaDB (persistent vector database)
- python-dotenv (environment-based configuration)

## 3. Folder Structure and Purpose

- `data/`
  - Source dataset files (currently `books.csv`).

- `src/`
  - `config.py`: typed settings + environment validation.
  - `data_loader.py`: CSV load/validation/preprocessing.
  - `embeddings.py`: embedding model loading and in-process cache.
  - `vector_store.py`: Chroma client/collection lifecycle.
  - `recommender.py`: core recommendation service.
  - `logging_utils.py`: centralized logging configuration.
  - `__init__.py`: package marker.

- `vector_db/`
  - Runtime-generated persistent Chroma data directory.

- `.env.example`
  - Canonical environment configuration template.

- `app.py`
  - Application entrypoint and Gradio interface.

- `requirements.txt`
  - Runtime dependency versions.

- `README.md`
  - Quick start and high-level operational notes.

- `Technical_Doc.md`
  - This document.

## 4. Key Modules and Components

### `src/config.py`

Responsibilities:
- Load environment values once via `dotenv`.
- Parse and type-cast bool/int settings safely.
- Validate startup-critical constraints in `Settings.__post_init__`.

Production validation rules include:
- `BATCH_SIZE > 0`
- `DEFAULT_RESULTS > 0`
- `TOP_K_MAX > 0`
- `DEFAULT_RESULTS <= TOP_K_MAX`
- `APP_PORT` in `[1, 65535]`
- Non-empty `CHROMA_COLLECTION` and `EMBEDDING_MODEL`

### `src/data_loader.py`

Responsibilities:
- Read CSV from `BOOKS_DATA_PATH`.
- Ensure required columns exist:
  - `title`, `authors`, `categories`, `description`, `isbn13`
- Create missing optional columns (`subtitle`) as empty string.
- Normalize nulls and whitespace.
- Build combined semantic text field (`text`) for indexing.
- Drop unusable rows (empty title).

### `src/embeddings.py`

Responsibilities:
- Load Sentence Transformer once (LRU cache, maxsize=1).
- Optional model cache directory support via `EMBEDDING_CACHE_DIR`.
- Sets `TOKENIZERS_PARALLELISM=false` to reduce noisy parallelism behavior in constrained environments.

### `src/vector_store.py`

Responsibilities:
- Create Chroma persistent client with telemetry disabled (`anonymized_telemetry=False`).
- Get or create configured collection.
- Reset collection when reindexing is required.

### `src/recommender.py`

Responsibilities:
- Thread-safe lazy initialization via lock.
- Build deterministic unique IDs from `isbn13` with duplicate handling.
- Rebuild index in batches (`BATCH_SIZE`) when needed.
- Convert vector distances to bounded relevance scores.
- Execute semantic search and return structured results.

Operational behavior:
- If collection count mismatches dataset row count, index is rebuilt.
- Query result count is clamped to available records and config bounds.
- Metadata values are normalized to strings before returning.

### `app.py`

Responsibilities:
- Compose and serve Gradio UI.
- Render result cards with escaped content for safety.
- Provide search/submit/clear interactions with loading and empty states.
- Initialize recommender at startup for predictable first request behavior.

UI characteristics:
- Full-viewport hero layout with centered search.
- Consistent typography, spacing, and responsive card grid.
- Clear feedback states for loading, empty, and error cases.

## 5. Data Flow

### A. Startup / Index Lifecycle

1. App starts (`python app.py`).
2. Logging config is initialized.
3. `recommender_service.initialize()` runs.
4. Books dataset is loaded and preprocessed.
5. Embedding model is loaded/cached.
6. Chroma collection is opened.
7. Reindex decision:
- Force reindex requested, or
- Collection count differs from current dataset size.
8. If reindex needed, all book texts are embedded in batches and inserted with metadata.

### B. Query Lifecycle

1. User submits natural-language query from UI.
2. Input is sanitized and validated.
3. Query is embedded using the same model.
4. Chroma nearest-neighbor query returns metadata + distances.
5. Distances are transformed into relevance scores.
6. Result cards are rendered in HTML and displayed.

## 6. APIs and Integrations

External/third-party integrations:
- Hugging Face Hub (model download on first run if model not cached)
- Sentence Transformers model runtime
- Chroma local persistence/query APIs
- Gradio web runtime

Internal APIs:
- `BookRecommender.initialize(force_reindex=False)`
- `BookRecommender.recommend_books(query, n_results=None)`
- `build_app()` in `app.py` returns Gradio Blocks app

## 7. Deployment Setup

### Local Deployment

1. Create virtual env.
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Create `.env` from `.env.example`.
4. Run:
```bash
python app.py
```

### Hugging Face Spaces (Gradio)

1. Create a Space and choose Gradio as the SDK.
2. Upload `app.py`, `requirements.txt`, `README.md`, `data/books.csv`, and `src/`.
3. Add secrets for any required environment variables.
4. First startup will download the model and rebuild the vector index.

### Container/Server Deployment

Recommended runtime settings:
- `APP_HOST=0.0.0.0`
- `APP_DEBUG=false`
- `LOG_LEVEL=INFO`

Persistence recommendations:
- Mount/persist `vector_db/chroma_db` to avoid re-embedding every restart.
- Persist `data/` if the dataset may be updated externally.

Cold-start considerations:
- First startup may download the model and build the index.
- Subsequent startups are faster when model cache and vector DB are persisted.

## 8. Environment Configuration

Variables and purpose:

- `BOOKS_DATA_PATH`
  - Dataset CSV path.

- `CHROMA_PATH`
  - Persistent Chroma directory.

- `CHROMA_COLLECTION`
  - Collection name for embedding records.

- `EMBEDDING_MODEL`
  - Sentence Transformers model identifier.

- `EMBEDDING_CACHE_DIR`
  - Optional local cache path for model artifacts.

- `BATCH_SIZE`
  - Number of records encoded per indexing batch.

- `DEFAULT_RESULTS`
  - Default recommendation count in UI.

- `TOP_K_MAX`
  - Maximum user-selectable result count.

- `APP_HOST`, `APP_PORT`, `APP_SHARE`, `APP_DEBUG`
  - Application server runtime controls.

- `LOG_LEVEL`
  - Application log verbosity.

## 9. Build and Run Instructions

Install and run:

```bash
pip install -r requirements.txt
cp .env.example .env
python app.py
```

Runtime smoke test example:

```bash
python -c "from src.recommender import recommender_service; recommender_service.initialize(); print(len(recommender_service.recommend_books('space opera', 3)))"
```

## 10. Design Decisions

1. Persistent vector storage (Chroma)
- Minimizes repeat startup cost and preserves index between restarts.

2. Semantic retrieval over keyword matching
- Better captures user intent and conceptual similarity.

3. Environment-driven configuration
- Separates deploy-time concerns from source code.

4. Fail-fast config validation
- Prevents subtle runtime errors from invalid environment values.

5. Thread-safe initialization
- Avoids duplicate index/model initialization under concurrent access.

6. Batched indexing
- Improves memory profile and throughput during embedding generation.

7. Defensive UI rendering
- Escapes dynamic content and returns meaningful input/server error states.

8. Telemetry-disabled vector client
- Better default for privacy-sensitive/local deployments.

## 11. Known Operational Notes

- First model load may print upstream library informational output and can be slower due to model download.
- To optimize cold starts in production:
  - Pre-warm by running one initialization job.
  - Persist model cache (`EMBEDDING_CACHE_DIR`) and `vector_db/chroma_db`.
