# scripts/list_notes.py
import sqlite3

DB = "onepiece.db"

def list_notes():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    rows = c.execute("SELECT id, title, arc FROM notes ORDER BY arc, title").fetchall()
    conn.close()

    if not rows:
        print("No notes found.")
        return

    print("Notes in DB:")
    for r in rows:
        print(f"- {r[0]} | {r[1]} ({r[2]})")

if __name__ == "__main__":
    list_notes()
