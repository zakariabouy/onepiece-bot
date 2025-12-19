# scripts/fetch_character_images.py — Download character images from One Piece Wiki
"""
Downloads character portrait images and saves them locally.
Run: python scripts/fetch_character_images.py
"""

import os
import requests
import time
import re
from bs4 import BeautifulSoup

IMAGE_DIR = "data/characters"
os.makedirs(IMAGE_DIR, exist_ok=True)

# Characters to fetch images for
CHARACTERS = [
    "Monkey D. Luffy", "Roronoa Zoro", "Nami", "Usopp", "Sanji",
    "Tony Tony Chopper", "Nico Robin", "Franky", "Brook", "Jinbe",
    "Shanks", "Portgas D. Ace", "Sabo", "Boa Hancock", "Trafalgar D. Water Law",
    "Donquixote Doflamingo", "Kaido", "Charlotte Linlin", "Marshall D. Teach",
    "Monkey D. Garp", "Silvers Rayleigh", "Enel", "Crocodile", "Buggy",
    "Dracule Mihawk", "Yamato", "Kozuki Oden", "Edward Newgate",
    "Gol D. Roger", "Eustass Kid", "Jewelry Bonney", "Smoker", "Koby",
    "Carrot", "Vivi", "Akainu", "Aokiji", "Kizaru",
]

def get_safe_filename(name: str) -> str:
    """Convert character name to safe filename."""
    return re.sub(r'[^\w\-]', '_', name.lower()).strip('_') + ".jpg"

def fetch_character_image(name: str) -> bool:
    """Fetch character image from One Piece Wiki."""
    url_name = name.replace(' ', '_')
    url = f"https://onepiece.fandom.com/wiki/{url_name}"
    
    filename = get_safe_filename(name)
    filepath = os.path.join(IMAGE_DIR, filename)
    
    # Skip if already exists
    if os.path.exists(filepath):
        print(f"  ✓ Already have {name}")
        return True
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try to find the main character image in the infobox
        infobox = soup.find('aside', class_='portable-infobox')
        if infobox:
            img_tag = infobox.find('img', class_='pi-image-thumbnail')
            if not img_tag:
                img_tag = infobox.find('img')
        else:
            # Fallback: find first large image
            img_tag = soup.find('img', {'width': lambda x: x and int(x) > 200 if x and x.isdigit() else False})
        
        if not img_tag:
            print(f"  ✗ No image found for {name}")
            return False
        
        # Get image URL
        img_url = img_tag.get('src') or img_tag.get('data-src')
        if not img_url:
            print(f"  ✗ No image URL for {name}")
            return False
        
        # Clean up URL (remove scaling parameters)
        img_url = re.sub(r'/revision/.*$', '', img_url)
        if not img_url.startswith('http'):
            img_url = 'https:' + img_url if img_url.startswith('//') else img_url
        
        # Download image
        img_response = requests.get(img_url, headers=headers, timeout=15)
        img_response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            f.write(img_response.content)
        
        print(f"  ✓ Downloaded {name} ({len(img_response.content)//1024}KB)")
        return True
        
    except Exception as e:
        print(f"  ✗ Error for {name}: {e}")
        return False

def main():
    print("=" * 50)
    print("One Piece Character Image Downloader")
    print(f"Saving to: {IMAGE_DIR}/")
    print("=" * 50)
    
    success = 0
    for i, name in enumerate(CHARACTERS, 1):
        print(f"[{i}/{len(CHARACTERS)}] {name}...")
        if fetch_character_image(name):
            success += 1
        time.sleep(1)  # Be nice to the server
    
    print(f"\n{'=' * 50}")
    print(f"Downloaded {success}/{len(CHARACTERS)} character images")
    print(f"Images saved in: {IMAGE_DIR}/")
    print("=" * 50)

if __name__ == "__main__":
    main()
