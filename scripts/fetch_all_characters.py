# scripts/fetch_all_characters.py — Fetch ALL One Piece characters from Wiki
"""
Scrapes the complete character list from One Piece Wiki and downloads images.
Run: python scripts/fetch_all_characters.py
"""

import os
import requests
import time
import re
import sqlite3
from bs4 import BeautifulSoup

IMAGE_DIR = "data/characters"
DB_PATH = "onepiece.db"
os.makedirs(IMAGE_DIR, exist_ok=True)

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0'}

def get_safe_filename(name: str) -> str:
    """Convert character name to safe filename."""
    return re.sub(r'[^\w\-]', '_', name.lower()).strip('_') + ".jpg"

def fetch_all_character_names(limit: int = 200) -> list:
    """Fetch character names from the wiki's character list page."""
    url = "https://onepiece.fandom.com/wiki/List_of_Canon_Characters"
    print(f"Fetching character list from {url}...")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        characters = []
        
        # Find all character links in the tables
        # The page has tables with character names
        tables = soup.find_all('table', class_='wikitable')
        
        for table in tables:
            links = table.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                name = link.get_text().strip()
                
                # Filter valid character links
                if (href.startswith('/wiki/') and 
                    not ':' in href and  # Skip categories, files, etc.
                    len(name) > 1 and
                    name not in ['Edit', 'View', '?'] and
                    not name.startswith('[') and
                    'Chapter' not in name and
                    'Episode' not in name):
                    
                    # Clean up the name
                    name = re.sub(r'\[.*?\]', '', name).strip()
                    if name and name not in characters:
                        characters.append(name)
        
        # Also try to get from any lists on the page
        if len(characters) < 50:
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link.get('href', '')
                name = link.get_text().strip()
                
                if (href.startswith('/wiki/') and 
                    not ':' in href and
                    len(name) > 2 and
                    name not in ['Edit', 'View', 'Source'] and
                    not any(x in name for x in ['Chapter', 'Episode', 'Arc', 'Saga', 'Category'])):
                    
                    name = re.sub(r'\[.*?\]', '', name).strip()
                    if name and name not in characters and len(name) < 50:
                        characters.append(name)
        
        print(f"Found {len(characters)} character names")
        
        # Return limited list (most important characters first)
        return characters[:limit]
        
    except Exception as e:
        print(f"Error fetching character list: {e}")
        return []

def fetch_character_image(name: str) -> tuple[bool, str | None]:
    """
    Fetch character image with improved detection.
    Returns (success, image_path)
    """
    url_name = name.replace(' ', '_')
    url = f"https://onepiece.fandom.com/wiki/{url_name}"
    
    filename = get_safe_filename(name)
    filepath = os.path.join(IMAGE_DIR, filename)
    
    # Skip if already exists
    if os.path.exists(filepath):
        return True, filepath
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code == 404:
            return False, None
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        img_url = None
        
        # Method 1: Try portable-infobox (new wiki style)
        infobox = soup.find('aside', class_='portable-infobox')
        if infobox:
            # Try different image classes
            for img_class in ['pi-image-thumbnail', 'pi-image']:
                img_tag = infobox.find('img', class_=img_class)
                if img_tag:
                    img_url = img_tag.get('data-src') or img_tag.get('src')
                    break
            
            # Fallback: any img in infobox
            if not img_url:
                img_tag = infobox.find('img')
                if img_tag:
                    img_url = img_tag.get('data-src') or img_tag.get('src')
        
        # Method 2: Try old-style infobox
        if not img_url:
            infobox_old = soup.find('table', class_='infobox')
            if infobox_old:
                img_tag = infobox_old.find('img')
                if img_tag:
                    img_url = img_tag.get('data-src') or img_tag.get('src')
        
        # Method 3: Look for figure with image
        if not img_url:
            figure = soup.find('figure', class_='pi-item')
            if figure:
                img_tag = figure.find('img')
                if img_tag:
                    img_url = img_tag.get('data-src') or img_tag.get('src')
        
        # Method 4: First image in article that looks like a portrait
        if not img_url:
            content = soup.find('div', class_='mw-parser-output')
            if content:
                for img_tag in content.find_all('img')[:5]:
                    src = img_tag.get('data-src') or img_tag.get('src') or ''
                    # Skip icons, logos, flags, etc.
                    if any(skip in src.lower() for skip in ['icon', 'logo', 'flag', 'symbol', 'button', 'sprite']):
                        continue
                    # Check if it's reasonably sized
                    width = img_tag.get('width', '0')
                    if width.isdigit() and int(width) >= 100:
                        img_url = src
                        break
        
        if not img_url:
            return False, None
        
        # Clean up URL
        img_url = re.sub(r'/revision/.*$', '', img_url)
        img_url = re.sub(r'/scale-to-width-down/\d+', '', img_url)
        if img_url.startswith('//'):
            img_url = 'https:' + img_url
        elif not img_url.startswith('http'):
            return False, None
        
        # Download image
        img_response = requests.get(img_url, headers=HEADERS, timeout=15)
        img_response.raise_for_status()
        
        # Verify it's actually an image
        content_type = img_response.headers.get('content-type', '')
        if 'image' not in content_type:
            return False, None
        
        # Check minimum size (skip tiny icons)
        if len(img_response.content) < 5000:  # Less than 5KB is probably an icon
            return False, None
        
        with open(filepath, 'wb') as f:
            f.write(img_response.content)
        
        return True, filepath
        
    except Exception as e:
        return False, None

def save_character_to_db(name: str, image_path: str | None):
    """Save character to database with image path."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create image mapping table if not exists
    c.execute("""
        CREATE TABLE IF NOT EXISTS character_images (
            name TEXT PRIMARY KEY,
            image_path TEXT,
            normalized_name TEXT
        )
    """)
    
    # Normalized name for matching
    normalized = name.lower().strip()
    
    c.execute(
        "INSERT OR REPLACE INTO character_images (name, image_path, normalized_name) VALUES (?, ?, ?)",
        (name, image_path, normalized)
    )
    
    conn.commit()
    conn.close()

def main():
    print("=" * 60)
    print("One Piece Character Image Downloader (Full Version)")
    print("=" * 60)
    
    # Priority characters to ensure we get (main cast + popular)
    priority_characters = [
        "Monkey D. Luffy", "Roronoa Zoro", "Nami", "Usopp", "Sanji",
        "Tony Tony Chopper", "Nico Robin", "Franky", "Brook", "Jinbe",
        "Shanks", "Portgas D. Ace", "Sabo", "Boa Hancock", "Trafalgar Law",
        "Donquixote Doflamingo", "Kaido", "Big Mom", "Blackbeard",
        "Monkey D. Garp", "Silvers Rayleigh", "Enel", "Crocodile", "Buggy",
        "Dracule Mihawk", "Yamato", "Kozuki Oden", "Whitebeard",
        "Gol D. Roger", "Eustass Kid", "Jewelry Bonney", "Smoker", "Koby",
        "Carrot", "Nefertari Vivi", "Akainu", "Aokiji", "Kizaru", "Fujitora",
        "Monkey D. Dragon", "Bartholomew Kuma", "Gecko Moria", "Rob Lucci",
        "Katakuri", "King", "Queen", "Marco", "Ace", "Law", "Kid",
        "Arlong", "Kuro", "Don Krieg", "Wapol", "Bellamy", "Foxy",
        "Caesar Clown", "Hody Jones", "Magellan", "Emporio Ivankov",
        "Perona", "Monet", "Sugar", "Corazon", "Senor Pink",
    ]
    
    # Fetch additional characters from wiki
    wiki_characters = fetch_all_character_names(limit=150)
    
    # Combine lists (priority first, then wiki)
    all_characters = priority_characters.copy()
    for char in wiki_characters:
        if char not in all_characters:
            all_characters.append(char)
    
    print(f"\nProcessing {len(all_characters)} characters...")
    print("=" * 60)
    
    success = 0
    failed = []
    
    for i, name in enumerate(all_characters, 1):
        print(f"[{i}/{len(all_characters)}] {name}...", end=" ", flush=True)
        
        got_image, image_path = fetch_character_image(name)
        
        if got_image:
            print("✓")
            success += 1
            save_character_to_db(name, image_path)
        else:
            print("✗")
            failed.append(name)
            save_character_to_db(name, None)  # Save without image
        
        time.sleep(0.5)  # Be nice to the server
    
    print(f"\n{'=' * 60}")
    print(f"✓ Downloaded {success}/{len(all_characters)} character images")
    print(f"Images saved in: {IMAGE_DIR}/")
    
    if failed and len(failed) <= 20:
        print(f"\nFailed characters: {', '.join(failed[:20])}")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
