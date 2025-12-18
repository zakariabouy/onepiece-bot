"""
Import chapter summaries from chapters.csv into the SQLite database.
This converts CSV data to the format expected by the RAG system.
"""
import sqlite3
import csv
from pathlib import Path

DB_PATH = "onepiece.db"
CHAPTERS_CSV = Path("data/chapters.csv")


def get_arc_from_chapter(chapter_num: int) -> str:
    """Map chapter numbers to story arcs for better retrieval filtering."""
    arcs = [
        (1, 7, "Romance Dawn"),
        (8, 21, "Orange Town"),
        (22, 41, "Syrup Village"),
        (42, 68, "Baratie"),
        (69, 95, "Arlong Park"),
        (96, 100, "Loguetown"),
        (101, 105, "Reverse Mountain"),
        (106, 114, "Whisky Peak"),
        (115, 129, "Little Garden"),
        (130, 154, "Drum Island"),
        (155, 217, "Arabasta"),
        (218, 228, "Jaya"),
        (229, 302, "Skypiea"),
        (303, 321, "Long Ring Long Land"),
        (322, 374, "Water 7"),
        (375, 430, "Enies Lobby"),
        (431, 441, "Post-Enies Lobby"),
        (442, 489, "Thriller Bark"),
        (490, 513, "Sabaody Archipelago"),
        (514, 524, "Amazon Lily"),
        (525, 549, "Impel Down"),
        (550, 580, "Marineford"),
        (581, 597, "Post-War"),
        (598, 602, "Return to Sabaody"),
        (603, 653, "Fish-Man Island"),
        (654, 699, "Punk Hazard"),
        (700, 801, "Dressrosa"),
        (802, 824, "Zou"),
        (825, 902, "Whole Cake Island"),
        (903, 908, "Reverie"),
        (909, 1057, "Wano"),
        (1058, 1089, "Egghead"),
        (1090, 9999, "Elbaph"),
    ]
    for start, end, arc_name in arcs:
        if start <= chapter_num <= end:
            return arc_name
    return "Unknown"


def import_chapters(db_path: str = DB_PATH, csv_path: Path = CHAPTERS_CSV) -> None:
    """Import chapters from CSV into the notes table."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Chapters CSV not found: {csv_path}")

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Ensure table exists
    c.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id    TEXT PRIMARY KEY,
            title TEXT,
            arc   TEXT,
            text  TEXT
        )
    """)

    imported = 0
    skipped = 0

    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            chapter_num = row.get("chapter_number", "").strip()
            if not chapter_num or not chapter_num.isdigit():
                skipped += 1
                continue

            chapter_int = int(chapter_num)
            summary = (row.get("in_depth_summary") or "").strip()
            cover = (row.get("cover_page") or "").strip()

            # Skip chapters with no content
            if not summary and not cover:
                skipped += 1
                continue

            # Build text combining cover and summary
            text_parts = []
            if cover:
                text_parts.append(f"Cover: {cover}")
            if summary:
                text_parts.append(summary)
            text = "\n\n".join(text_parts)

            note_id = f"chapter_{chapter_num}"
            title = f"Chapter {chapter_num}"
            arc = get_arc_from_chapter(chapter_int)

            c.execute(
                "INSERT OR REPLACE INTO notes (id, title, arc, text) VALUES (?, ?, ?, ?)",
                (note_id, title, arc, text),
            )
            imported += 1

    conn.commit()
    conn.close()

    print(f"✓ Imported {imported} chapters into {db_path}")
    print(f"  Skipped {skipped} invalid/empty rows")


if __name__ == "__main__":
    import_chapters()
