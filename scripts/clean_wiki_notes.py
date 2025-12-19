"""
Clean noisy wiki data by removing navigation, references, and irrelevant text.
Creates a cleaned version of wiki_notes.jsonl.
"""
import json
import re
from pathlib import Path

INPUT_PATH = Path("data/wiki_notes.jsonl")
OUTPUT_PATH = Path("data/wiki_notes_clean.jsonl")


def clean_wiki_text(text: str) -> str:
    """Remove wiki noise from text."""
    if not text:
        return ""

    # Remove reference markers like [1], [2], etc.
    text = re.sub(r'\[\d+\]', '', text)
    
    # Remove wiki navigation sections
    noise_patterns = [
        r'^\s*Contents\s*$',
        r'^\s*\d+\s+\w+.*$',  # Table of contents entries like "1 Appearance"
        r'Site Navigation\s*\[\s*\]',
        r'References\s*\[\s*\]',
        r'Quick Answers.*?Provided by:.*?(?=\n\n|\Z)',
        r'\[\s*v\s*·\s*e\s*\]',
        r'Introduction\s*•\s*Gallery\s*•.*?Misc\.',
        r'Statistics\s*Japanese Name:.*?Portrayal',
        r'Portrayal\s*Japanese Voice.*?(?=For |$)',
        r'Devil Fruit\s*Japanese Name:.*?Type:\s*\w+',
        r'External links\s*\[\s*\].*',
    ]
    
    for pattern in noise_patterns:
        text = re.sub(pattern, '', text, flags=re.MULTILINE | re.DOTALL | re.IGNORECASE)

    # Remove repeated navigation headers
    nav_headers = [
        'Introduction', 'Gallery', 'Personality', 'Relationships', 
        'Abilities and Powers', 'History', 'Misc.', 'Non-Canon',
        'Before the Timeskip', 'After the Timeskip', 'Crew', 'Family',
        'Pirates', 'Emperors and Groups', 'World Government', 'Citizens',
        'East Blue', 'Paradise', 'Summit War', 'New World', 'Whole Cake',
        'Wano', 'Final', 'Past and Before the Timeskip', 'During and After the Timeskip'
    ]
    
    # Remove lines that are just navigation headers
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        # Skip if line is just a nav header or very short
        if stripped in nav_headers or stripped == '[\n]' or stripped == '[]':
            continue
        # Skip empty brackets
        if re.match(r'^\s*\[\s*\]\s*$', stripped):
            continue
        cleaned_lines.append(line)
    
    text = '\n'.join(cleaned_lines)
    
    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    
    return text.strip()


def extract_key_info(obj: dict) -> str:
    """Extract the most relevant information from a wiki entry."""
    text = obj.get("text", "")
    title = obj.get("title", "")
    
    # Clean the text first
    cleaned = clean_wiki_text(text)
    
    # Try to extract meaningful sections
    sections = []
    
    # Look for the main description (usually after the character name heading)
    main_desc_match = re.search(
        rf'{re.escape(title)}.*?is (?:the|a|an).*?(?=\n\n|\nContents|\Z)',
        cleaned,
        re.DOTALL | re.IGNORECASE
    )
    if main_desc_match:
        sections.append(main_desc_match.group(0).strip())
    
    # If we couldn't extract meaningful content, take first 2000 chars of cleaned text
    if not sections:
        # Take up to first 2000 characters as fallback
        sections.append(cleaned[:2000] if len(cleaned) > 2000 else cleaned)
    
    return '\n\n'.join(sections)


def clean_wiki_notes():
    """Process and clean wiki_notes.jsonl."""
    if not INPUT_PATH.exists():
        print(f"Input file not found: {INPUT_PATH}")
        return

    cleaned_notes = []
    
    with INPUT_PATH.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"JSON error at line {line_no}: {e}")
                continue
            
            # Clean the text
            cleaned_text = extract_key_info(obj)
            
            # Create cleaned entry
            cleaned_obj = {
                "id": obj.get("id"),
                "title": obj.get("title"),
                "arc": obj.get("arc", "General Lore"),
                "text": cleaned_text
            }
            
            cleaned_notes.append(cleaned_obj)
            print(f"Cleaned: {obj.get('title')} ({len(cleaned_text)} chars)")

    # Write cleaned notes
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        for note in cleaned_notes:
            f.write(json.dumps(note, ensure_ascii=False) + "\n")

    print(f"\n✓ Cleaned {len(cleaned_notes)} wiki notes")
    print(f"  Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    clean_wiki_notes()
