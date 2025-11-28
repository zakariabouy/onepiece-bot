# scripts/import_chapters.py
# Import chapter summaries into the existing onepiece.db notes table

import sqlite3
import csv
from pathlib import Path

DB_PATH = Path("onepiece.db")
CHAPTERS_CSV = Path("data/chapters.csv")  # ← change if your file is elsewhere


def main():
    if not CHAPTERS_CSV.exists():
        raise FileNotFoundError(f"CSV not found: {CHAPTERS_CSV}")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Make sure the notes table exists (same schema as your app expects)
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS notes (
            id   TEXT PRIMARY KEY,
            title TEXT,
            arc   TEXT,
            text  TEXT
        )
        """
    )

    rows_to_insert = []

    with CHAPTERS_CSV.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Adapt these keys if your headers are named a bit differently
            chapter_raw = (row.get("chapter_number") or row.get("chapter") or "").strip()
            cover = (row.get("cover_page") or "").strip()
            summary = (row.get("in_depth_summary") or "").strip()
            error = (row.get("error") or "").strip()

            # Skip rows with errors or missing summary
            if not chapter_raw or not summary or error:
                continue

            # Build an ID like "chapter_0001"
            try:
                chapter_int = int(chapter_raw)
            except ValueError:
                # If it’s something weird like "0.5" just use raw string
                note_id = f"chapter_{chapter_raw}"
            else:
                note_id = f"chapter_{chapter_int:04d}"

            title = f"Chapter {chapter_raw}"

            # Arc: for now we use a generic label; later you can map chapter → saga/arc
            arc = "Chapter Summary"

            # Combine cover + summary into one text field
            parts = []
            if cover:
                parts.append(f"Cover: {cover}")
            parts.append(f"Summary: {summary}")
            text = "\n\n".join(parts)

            rows_to_insert.append((note_id, title, arc, text))

    print(f"Prepared {len(rows_to_insert)} chapter notes to insert.")

    c.executemany(
        "INSERT OR REPLACE INTO notes (id, title, arc, text) VALUES (?,?,?,?)",
        rows_to_insert,
    )
    conn.commit()
    conn.close()
    print(f"Inserted {len(rows_to_insert)} chapter notes into {DB_PATH}")


if __name__ == "__main__":
    main()
