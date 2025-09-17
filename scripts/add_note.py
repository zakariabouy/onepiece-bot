# scripts/add_note.py
import sqlite3
import sys
import os
import json
from typing import Iterable, Dict, Tuple

DB = "onepiece.db"
TABLE_SQL = """
CREATE TABLE IF NOT EXISTS notes (
    id   TEXT PRIMARY KEY,
    title TEXT,
    arc   TEXT,
    text  TEXT
)
"""

def get_conn():
    conn = sqlite3.connect(DB)
    conn.execute(TABLE_SQL)
    return conn

def upsert_note(conn: sqlite3.Connection, note_id: str, title: str, arc: str, text: str) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO notes (id, title, arc, text) VALUES (?,?,?,?)",
        (note_id, title, arc, text)
    )

def load_jsonl(path: str) -> Iterable[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)

def main(argv: list[str]) -> None:
    """
    Usage:
      # Single insert (quote fields with spaces)
      python scripts/add_note.py <id> "<title>" "<arc>" "<text>"

      # Bulk insert from JSONL (one JSON per line with keys id, title, arc, text)
      python scripts/add_note.py path\\to\\notes.jsonl
    """
    if len(argv) < 2:
        print(main.__doc__)
        return

    conn = get_conn()
    inserted = 0

    try:
        # Bulk mode: one positional arg that is an existing file path
        if len(argv) == 2 and os.path.isfile(argv[1]):
            file_path = argv[1]
            for obj in load_jsonl(file_path):
                upsert_note(conn, obj["id"], obj["title"], obj["arc"], obj["text"])
                inserted += 1
            conn.commit()
            print(f"Inserted/updated {inserted} notes from {file_path}")

        # Single-note mode: 4 args after script name
        elif len(argv) >= 5:
            _, note_id, title, arc, text = argv[:5]
            upsert_note(conn, note_id, title, arc, text)
            conn.commit()
            print(f"Upserted note: {note_id}")

        else:
            print(main.__doc__)

    finally:
        conn.close()

if __name__ == "__main__":
    main(sys.argv)
