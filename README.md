---
title: SemanticShelf
emoji: 📚
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 4.36.1
python_version: 3.10
app_file: app.py
pinned: false
---

# SemanticShelf

AI semantic book recommendation engine built with Sentence Transformers, ChromaDB, and Gradio.

## Features

- Semantic retrieval from natural-language intent
- Deterministic indexing with persistent local vector storage
- Environment-driven configuration with startup validation
- Professional, full-viewport UI with responsive result cards
- Modular `src/` architecture for maintenance and deployment

## Project Structure

```text
BookRecommender/
+-- data/
|   +-- books.csv
+-- src/
|   +-- __init__.py
|   +-- config.py
|   +-- data_loader.py
|   +-- embeddings.py
|   +-- logging_utils.py
|   +-- recommender.py
|   +-- vector_store.py
+-- vector_db/
|   +-- chroma_db/             # generated at runtime
+-- .env.example
+-- .gitignore
+-- app.py
+-- requirements.txt
+-- README.md
+-- Technical_Doc.md
```

## Local Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create runtime config:

```bash
cp .env.example .env
```

4. Run the app:

```bash
python app.py
```

Default URL: `http://127.0.0.1:7860`

## Hugging Face Spaces (Gradio)

1. Create a Space and choose Gradio as the SDK.
2. Upload these items:
	- `app.py`
	- `requirements.txt`
	- `README.md`
	- `data/books.csv`
	- `src/`
3. Add secrets for the environment variables you use (see below).
4. First startup will download the model and rebuild the vector index.

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

- First run may download the embedding model and build the vector index.
- Persist `vector_db/chroma_db` in production to avoid cold-start reindexing.
- Set `APP_HOST=0.0.0.0` when deploying in containers.
- See `Technical_Doc.md` for architecture and deployment details.


