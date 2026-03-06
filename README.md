# AI Book Recommender

Production-ready semantic recommendation web application built with Sentence Transformers, ChromaDB, and Gradio.

## Features

- Semantic retrieval from natural-language user intent
- Persistent local vector index with deterministic rebuild behavior
- Environment-driven configuration with startup validation
- Clean, responsive, professional UI
- Modular architecture (`src/`) for maintainability and deployment

## Project Structure

```text
BookRecommender/
+-- data/
¦   +-- books.csv
+-- src/
¦   +-- __init__.py
¦   +-- config.py
¦   +-- data_loader.py
¦   +-- embeddings.py
¦   +-- logging_utils.py
¦   +-- recommender.py
¦   +-- vector_store.py
+-- vector_db/
¦   +-- chroma_db/             # generated at runtime
+-- .env.example
+-- .gitignore
+-- app.py
+-- requirements.txt
+-- README.md
+-- Technical_Doc.md
```

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create runtime config:

```bash
cp .env.example .env
```

4. Run app:

```bash
python app.py
```

Default URL: `http://127.0.0.1:7860`

## Environment Variables

- `BOOKS_DATA_PATH` CSV dataset location
- `CHROMA_PATH` local vector database path
- `CHROMA_COLLECTION` collection name
- `EMBEDDING_MODEL` sentence-transformers model id
- `EMBEDDING_CACHE_DIR` optional local model cache directory
- `BATCH_SIZE` indexing batch size
- `DEFAULT_RESULTS` default number of results
- `TOP_K_MAX` max results limit
- `APP_HOST`, `APP_PORT`, `APP_SHARE`, `APP_DEBUG`
- `LOG_LEVEL`

## Production Notes

- On first run, the embedding model may be downloaded and indexed.
- Persist `vector_db/chroma_db` in production to avoid cold-start reindexing.
- Set `APP_HOST=0.0.0.0` when deploying in containers.
- See `Technical_Doc.md` for architecture and deployment details.
