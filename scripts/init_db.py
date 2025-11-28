import sqlite3
import json
from pathlib import Path

DB_PATH = "onepiece.db"
NOTES_PATH = Path("data/wiki_notes.jsonl")


def build_text_from_obj(obj: dict) -> str:
    """
    Build the 'text' field used for embeddings / RAG
    from a structured note object.

    Priority:
    - If 'text' field exists and is non-empty, use it directly.
    - Else, concatenate: summary, personality, abilities, dream, extra_notes.
    """
    raw_text = (obj.get("text") or "").strip()
    if raw_text:
        return raw_text

    parts = []
    for key in ["summary", "personality", "abilities", "dream", "extra_notes"]:
        val = (obj.get(key) or "").strip()
        if val:
            parts.append(val)

    return " ".join(parts).strip()


def load_notes_from_jsonl(path: Path) -> list[tuple[str, str, str, str]]:
    """
    Read data/notes.jsonl and return a list of (id, title, arc, text)
    ready to insert into the SQLite table.
    """
    if not path.exists():
        raise FileNotFoundError(f"Notes file not found: {path}")

    notes_rows: list[tuple[str, str, str, str]] = []

    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"JSON error in {path} at line {line_no}: {e}") from e

            note_id = obj.get("id")
            title = obj.get("title")
            arc = obj.get("arc", "General Lore")

            if not note_id or not title:
                raise ValueError(
                    f"Missing 'id' or 'title' in {path} at line {line_no}: {obj}"
                )

            text = build_text_from_obj(obj)
            if not text:
                # Fallback: if still empty, at least store the title
                text = title

            notes_rows.append((note_id, title, arc, text))

    return notes_rows


def init_db(db_path: str = DB_PATH, notes_path: Path = NOTES_PATH) -> None:
    # Connect / create DB
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Create table
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS notes (
            id    TEXT PRIMARY KEY,
            title TEXT,
            arc   TEXT,
            text  TEXT
        )
        """
    )

    # Load data from JSONL
    notes_rows = load_notes_from_jsonl(notes_path)

    # Insert or replace notes
    c.executemany(
        "INSERT OR REPLACE INTO notes (id, title, arc, text) VALUES (?, ?, ?, ?)",
        notes_rows,
    )
    conn.commit()
    conn.close()

    print(f"Database initialized: {db_path}")
    print(f"Loaded {len(notes_rows)} notes from {notes_path}")


if __name__ == "__main__":
    init_db()

