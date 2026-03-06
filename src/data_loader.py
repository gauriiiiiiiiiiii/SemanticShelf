from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = ["title", "authors", "categories", "description", "isbn13"]
OPTIONAL_COLUMNS = ["subtitle"]


def load_books(path: str = "data/books.csv") -> pd.DataFrame:
    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset not found: {csv_path}")

    books = pd.read_csv(csv_path)
    missing = [col for col in REQUIRED_COLUMNS if col not in books.columns]
    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")

    for col in REQUIRED_COLUMNS + OPTIONAL_COLUMNS:
        if col not in books.columns:
            books[col] = ""
        books[col] = books[col].fillna("").astype(str).str.strip()

    books["text"] = (
        books["title"] + ". "
        + books["authors"] + ". "
        + books["categories"] + ". "
        + books["description"]
    ).str.strip()

    books = books[books["title"] != ""].reset_index(drop=True)
    if books.empty:
        raise ValueError("No valid rows found after preprocessing.")

    return books
