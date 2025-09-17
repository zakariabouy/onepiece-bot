import sqlite3

# Create DB
conn = sqlite3.connect("onepiece.db")
c = conn.cursor()

# Create table
c.execute("""
CREATE TABLE IF NOT EXISTS notes (
    id TEXT PRIMARY KEY,
    title TEXT,
    arc TEXT,
    text TEXT
)
""")

# Seed some data (you can add more later)
notes = [
    ("zoro_intro", "Roronoa Zoro", "East Blue", "Zoro is the first crewmate to join Luffy. He is a swordsman aiming to become the world’s greatest, wielding three swords in his unique fighting style."),
    ("nami_intro", "Nami", "East Blue", "Nami is the Straw Hats’ navigator. She values maps and treasure, with a dream to draw a complete map of the world."),
    ("ace", "Portgas D. Ace", "Marineford", "Ace is Luffy’s sworn brother and a commander in Whitebeard’s crew. He ate the Mera Mera no Mi, gaining fire-based powers."),
]
c.executemany("INSERT OR REPLACE INTO notes VALUES (?,?,?,?)", notes)

conn.commit()
conn.close()
print("Database initialized: onepiece.db")
