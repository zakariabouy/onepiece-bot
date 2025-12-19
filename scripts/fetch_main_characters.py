# scripts/fetch_main_characters.py — Download main character images with correct URLs
"""
Downloads images for main characters that may have failed with auto-detection.
Uses specific wiki URLs for each character.
"""

import os
import requests
import time
import re
from bs4 import BeautifulSoup

IMAGE_DIR = "data/characters"
os.makedirs(IMAGE_DIR, exist_ok=True)

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0'}

# Characters with their correct wiki URLs (some have different page names)
MAIN_CHARACTERS = {
    # Straw Hats
    "Tony Tony Chopper": "Tony_Tony_Chopper",
    "Brook": "Brook",
    
    # Yonko/Emperors
    "Shanks": "Shanks",
    "Kaido": "Kaidou",  # Different spelling on wiki
    "Big Mom": "Charlotte_Linlin",
    "Blackbeard": "Marshall_D._Teach",
    "Whitebeard": "Edward_Newgate",
    
    # Important characters
    "Portgas D. Ace": "Portgas_D._Ace",
    "Trafalgar Law": "Trafalgar_D._Water_Law",
    "Crocodile": "Crocodile_(Warlord)",  # Disambiguation
    "Dracule Mihawk": "Dracule_Mihawk",
    "Kozuki Oden": "Kozuki_Oden",
    "Monkey D. Dragon": "Monkey_D._Dragon",
    "Marco": "Marco",
    "Katakuri": "Charlotte_Katakuri",
    
    # Admirals
    "Akainu": "Sakazuki",
    "Aokiji": "Kuzan",
    "Kizaru": "Borsalino",
    "Fujitora": "Issho",
    
    # Warlords
    "Bartholomew Kuma": "Bartholomew_Kuma",
    "Gecko Moria": "Gecko_Moria",
    
    # CP9/Cipher Pol
    "Rob Lucci": "Rob_Lucci",
    
    # Beast Pirates
    "King": "King_(Lunarian)",  # Disambiguation
    
    # Others
    "Arlong": "Arlong",
    "Caesar Clown": "Caesar_Clown",
    "Magellan": "Magellan",
    "Perona": "Perona",
    "Corazon": "Donquixote_Rosinante",
}

def get_safe_filename(name: str) -> str:
    return re.sub(r'[^\w\-]', '_', name.lower()).strip('_') + ".jpg"

def download_image(name: str, wiki_page: str) -> bool:
    """Download character image."""
    filename = get_safe_filename(name)
    filepath = os.path.join(IMAGE_DIR, filename)
    
    if os.path.exists(filepath):
        print(f"  ✓ Already have {name}")
        return True
    
    url = f"https://onepiece.fandom.com/wiki/{wiki_page}"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        img_url = None
        
        # Try infobox
        infobox = soup.find('aside', class_='portable-infobox')
        if infobox:
            img_tag = infobox.find('img')
            if img_tag:
                img_url = img_tag.get('data-src') or img_tag.get('src')
        
        # Try figure
        if not img_url:
            figure = soup.find('figure', class_='pi-item')
            if figure:
                img_tag = figure.find('img')
                if img_tag:
                    img_url = img_tag.get('data-src') or img_tag.get('src')
        
        # Try finding any image with "Infobox" in the src
        if not img_url:
            for img in soup.find_all('img'):
                src = img.get('data-src') or img.get('src') or ''
                if 'Infobox' in src or name.split()[0] in src:
                    img_url = src
                    break
        
        if not img_url:
            print(f"  ✗ No image for {name}")
            return False
        
        # Clean URL
        img_url = re.sub(r'/revision/.*$', '', img_url)
        img_url = re.sub(r'/scale-to-width-down/\d+', '', img_url)
        if img_url.startswith('//'):
            img_url = 'https:' + img_url
        
        # Download
        img_response = requests.get(img_url, headers=HEADERS, timeout=15)
        img_response.raise_for_status()
        
        if len(img_response.content) < 3000:
            print(f"  ✗ Image too small for {name}")
            return False
        
        with open(filepath, 'wb') as f:
            f.write(img_response.content)
        
        print(f"  ✓ Downloaded {name} ({len(img_response.content)//1024}KB)")
        return True
        
    except Exception as e:
        print(f"  ✗ Error for {name}: {e}")
        return False

def main():
    print("=" * 50)
    print("Downloading Main Character Images")
    print("=" * 50)
    
    success = 0
    for name, wiki_page in MAIN_CHARACTERS.items():
        print(f"{name}...", end=" ", flush=True)
        if download_image(name, wiki_page):
            success += 1
        time.sleep(0.5)
    
    print(f"\n{'=' * 50}")
    print(f"Downloaded {success}/{len(MAIN_CHARACTERS)} images")
    print("=" * 50)

if __name__ == "__main__":
    main()
