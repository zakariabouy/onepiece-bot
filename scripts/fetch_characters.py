# scripts/fetch_characters.py — Fetch One Piece character data
"""
Fetches character profiles from One Piece Wiki and adds them to the database.
Run: python scripts/fetch_characters.py
"""

import sqlite3
import requests
from bs4 import BeautifulSoup
import time
import re

DB_PATH = "onepiece.db"

# Main characters and important figures to fetch
CHARACTERS = [
    # Straw Hat Pirates
    "Monkey D. Luffy", "Roronoa Zoro", "Nami", "Usopp", "Sanji",
    "Tony Tony Chopper", "Nico Robin", "Franky", "Brook", "Jinbe",
    
    # Villains & Antagonists
    "Marshall D. Teach", "Kaido", "Charlotte Linlin", "Donquixote Doflamingo",
    "Crocodile", "Enel", "Rob Lucci", "Arlong", "Buggy",
    
    # Marines
    "Monkey D. Garp", "Akainu", "Aokiji", "Kizaru", "Fujitora",
    "Sengoku", "Smoker", "Koby",
    
    # Revolutionary Army
    "Monkey D. Dragon", "Sabo", "Emporio Ivankov",
    
    # Emperors & Legends
    "Shanks", "Edward Newgate", "Gol D. Roger", "Silvers Rayleigh",
    
    # Warlords
    "Dracule Mihawk", "Boa Hancock", "Bartholomew Kuma", "Trafalgar D. Water Law",
    "Gecko Moria", "Jinbe",
    
    # Supernovas
    "Eustass Kid", "Trafalgar Law", "Jewelry Bonney", "Capone Bege",
    "Basil Hawkins", "X Drake", "Scratchmen Apoo", "Killer", "Urouge",
    
    # Other important characters
    "Vivi", "Ace", "Whitebeard", "Yamato", "Carrot", "Kozuki Oden",
]

def clean_text(text: str) -> str:
    """Clean wiki text."""
    # Remove citations [1], [2], etc.
    text = re.sub(r'\[\d+\]', '', text)
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    # Remove edit links
    text = re.sub(r'\[edit\]', '', text, flags=re.I)
    return text.strip()

def fetch_character_info(name: str) -> dict | None:
    """Fetch character info from One Piece Wiki."""
    # Convert name to wiki URL format
    url_name = name.replace(' ', '_')
    url = f"https://onepiece.fandom.com/wiki/{url_name}"
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Get the main content
        content_div = soup.find('div', class_='mw-parser-output')
        if not content_div:
            return None
        
        # Get first few paragraphs (introduction)
        paragraphs = content_div.find_all('p', recursive=False)
        intro_text = ""
        for p in paragraphs[:4]:  # First 4 paragraphs
            text = p.get_text()
            if len(text) > 50:  # Skip short/empty paragraphs
                intro_text += text + " "
            if len(intro_text) > 1500:  # Limit length
                break
        
        intro_text = clean_text(intro_text)
        
        if len(intro_text) < 100:
            return None
            
        # Try to extract some key info from infobox
        infobox = soup.find('aside', class_='portable-infobox')
        extra_info = ""
        
        if infobox:
            # Try to get bounty, devil fruit, etc.
            data_items = infobox.find_all('div', class_='pi-data')
            for item in data_items:
                label = item.find('h3', class_='pi-data-label')
                value = item.find('div', class_='pi-data-value')
                if label and value:
                    label_text = label.get_text().strip()
                    value_text = clean_text(value.get_text())
                    if label_text.lower() in ['bounty', 'devil fruit', 'epithet', 'affiliation', 'occupation']:
                        extra_info += f"{label_text}: {value_text}. "
        
        full_text = f"{extra_info}{intro_text}".strip()
        
        # Truncate if too long
        if len(full_text) > 2000:
            full_text = full_text[:2000] + "..."
            
        return {
            "name": name,
            "text": full_text,
            "url": url
        }
        
    except Exception as e:
        print(f"  Error fetching {name}: {e}")
        return None

def add_to_database(characters: list):
    """Add characters to SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    added = 0
    for char in characters:
        char_id = f"character_{char['name'].lower().replace(' ', '_').replace('.', '')}"
        
        # Check if already exists
        existing = c.execute("SELECT id FROM notes WHERE id = ?", (char_id,)).fetchone()
        if existing:
            print(f"  Skipping {char['name']} (already exists)")
            continue
        
        c.execute(
            "INSERT OR REPLACE INTO notes (id, title, arc, text) VALUES (?, ?, ?, ?)",
            (char_id, char['name'], "Character Profile", char['text'])
        )
        added += 1
        print(f"  Added: {char['name']}")
    
    conn.commit()
    conn.close()
    return added

def main():
    print("=" * 50)
    print("One Piece Character Fetcher")
    print("=" * 50)
    
    characters_data = []
    
    for i, name in enumerate(CHARACTERS, 1):
        print(f"[{i}/{len(CHARACTERS)}] Fetching {name}...")
        
        data = fetch_character_info(name)
        if data:
            characters_data.append(data)
            print(f"  ✓ Got {len(data['text'])} chars")
        else:
            print(f"  ✗ Failed")
        
        # Be nice to the server
        time.sleep(1)
    
    print(f"\n{'=' * 50}")
    print(f"Successfully fetched {len(characters_data)} characters")
    print(f"{'=' * 50}")
    
    if characters_data:
        print("\nAdding to database...")
        added = add_to_database(characters_data)
        print(f"\n✓ Added {added} new character profiles to database!")
        print("\n⚠️  Remember to delete embeddings_cache.npz to rebuild the index!")

if __name__ == "__main__":
    main()
