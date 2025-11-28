import requests
import json
import time
from pathlib import Path
from bs4 import BeautifulSoup  # pip install beautifulsoup4

API_URL = "https://onepiece.fandom.com/api.php"
OUT_PATH = Path("data/wiki_notes.jsonl")

# You can extend this list with as many pages as you want
PAGES = [
    {"id": "luffy_wiki", "title": "Monkey D. Luffy", "page": "Monkey_D._Luffy", "arc": "East Blue"},
    {"id": "zoro_wiki", "title": "Roronoa Zoro", "page": "Roronoa_Zoro", "arc": "East Blue"},
    {"id": "nami_wiki", "title": "Nami", "page": "Nami", "arc": "East Blue"},
    {"id": "sanji_wiki", "title": "Sanji", "page": "Sanji", "arc": "East Blue"},
    {"id": "chopper_wiki", "title": "Tony Tony Chopper", "page": "Tony_Tony_Chopper", "arc": "Drum Island"},
    {"id": "robin_wiki", "title": "Nico Robin", "page": "Nico_Robin", "arc": "Alabasta"},
    {"id": "franky_wiki", "title": "Franky", "page": "Franky", "arc": "Water_7"},
    {"id": "brook_wiki", "title": "Brook", "page": "Brook", "arc": "Thriller_Bark"},
    {"id": "jinbe_wiki", "title": "Jinbe", "page": "Jinbe", "arc": "Fish-Man Island"},
    # concepts / places
    {"id": "devil_fruits_wiki", "title": "Devil Fruit", "page": "Devil_Fruit", "arc": "General Lore"},
    {"id": "haki_wiki", "title": "Haki", "page": "Haki", "arc": "General Lore"},
    {"id": "grand_line_wiki", "title": "Grand Line", "page": "Grand_Line", "arc": "General Lore"},
    {"id": "marineford_wiki", "title": "Marineford", "page": "Marineford", "arc": "Marineford"},
    {"id": "wano_wiki", "title": "Wano Country", "page": "Wano_Country", "arc": "Wano"},
]


def fetch_plaintext_from_parse(page_title: str) -> str:
    """
    Fetch the HTML of a wiki page via action=parse, then strip it to plain text.
    This is more robust than prop=extracts on Fandom wikis.
    """
    params = {
        "action": "parse",
        "page": page_title,
        "prop": "text",
        "format": "json",
        "redirects": 1,   # follow redirects (e.g. if Sanji redirects to Vinsmoke_Sanji)
        "formatversion": 2,
        "origin": "*",    # helps with some CORS setups; harmless for us
    }

    headers = {
        "User-Agent": "OnePiece-RAG-Bot/1.0 (educational, non-commercial)"
    }

    resp = requests.get(API_URL, params=params, headers=headers, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    parse = data.get("parse")
    if not parse:
        # Debug info in case of issues
        print(f"  -> No 'parse' in response for page {page_title}: {data}")
        return ""

    html = ""
    # formatversion=2 gives a dict with 'text' as a string OR {'text': '<html>'}
    t = parse.get("text")
    if isinstance(t, str):
        html = t
    elif isinstance(t, dict):
        html = t.get("*", "") or t.get("text", "")
    else:
        html = ""

    if not html:
        print(f"  -> Empty HTML for page {page_title}")
        return ""

    # Strip HTML with BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")

    # Remove some non-content elements if needed (navbars, etc.)
    for el in soup.select("table, .infobox, .navbox, script, style"):
        el.decompose()

    text = soup.get_text("\n")
    # Clean up multiple newlines / spaces
    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    clean_text = "\n".join(lines)

    return clean_text.strip()


def main():
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUT_PATH.open("w", encoding="utf-8") as f:
        for meta in PAGES:
            page = meta["page"]
            print(f"Fetching {page} ...")
            try:
                text = fetch_plaintext_from_parse(page)
            except Exception as e:
                print(f"  -> Error fetching {page}: {e}")
                text = ""

            # Optional: debug length so you see it’s not empty anymore
            print(f"  -> Retrieved {len(text)} characters")

            obj = {
                "id": meta["id"],
                "title": meta["title"],
                "type": "wiki",
                "arc": meta.get("arc", "General Lore"),
                "source": "onepiece.fandom.com",
                "source_page": page,
                "text": text,
            }

            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

            # Be nice to the server
            time.sleep(1)

    print(f"Saved {len(PAGES)} pages to {OUT_PATH}")


if __name__ == "__main__":
    main()