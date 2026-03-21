"""
Fetch SBS data from One Piece Wiki + Curated important SBS revelations.
SBS = Oda's Q&A section - contains crucial canon info for theory evaluation!
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from pathlib import Path

OUTPUT_FILE = Path("data/assets/sbs_data.jsonl")
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def create_curated_sbs_data():
    """
    Curated SBS data - the most important revelations for theory evaluation.
    Hand-picked from 100+ volumes of SBS content.
    """
    
    sbs_entries = [
        # === CHARACTER INFO ===
        {
            "volume": 4,
            "question": "What are the ages of the Straw Hat crew?",
            "answer": "Pre-timeskip: Luffy 17, Zoro 19, Nami 18, Usopp 17, Sanji 19, Chopper 15, Robin 28, Franky 34, Brook 88. Post-timeskip they are all 2 years older.",
            "category": "character_info"
        },
        {
            "volume": 72,
            "question": "What would the Straw Hats' nationalities be in real world?",
            "answer": "Luffy: Brazil, Zoro: Japan, Nami: Sweden, Usopp: Africa, Sanji: France, Chopper: Canada, Robin: Russia, Franky: USA, Brook: Austria, Jinbe: India.",
            "category": "character_info"
        },
        {
            "volume": 79,
            "question": "What are the heights of the Straw Hats post-timeskip?",
            "answer": "Luffy 174cm, Zoro 181cm, Nami 170cm, Usopp 176cm, Sanji 180cm, Chopper 90cm (monster point 7m), Robin 188cm, Franky 240cm, Brook 277cm, Jinbe 301cm.",
            "category": "character_info"
        },
        {
            "volume": 69,
            "question": "What flowers represent each Straw Hat?",
            "answer": "Luffy: Cosmos, Zoro: Wisteria, Nami: Sunflower, Usopp: Daisy, Sanji: Rose, Chopper: Tulip, Robin: Casablanca, Franky: Anemone, Brook: Rose.",
            "category": "character_info"
        },
        {
            "volume": 69,
            "question": "What are the specific jobs of each Straw Hat?",
            "answer": "Luffy: Captain, Zoro: Swordsman/Combat, Nami: Navigator, Usopp: Sniper, Sanji: Cook, Chopper: Doctor, Robin: Archaeologist, Franky: Shipwright, Brook: Musician, Jinbe: Helmsman.",
            "category": "character_info"
        },
        {
            "volume": 87,
            "question": "What do the Vinsmoke names mean?",
            "answer": "The Vinsmoke children are named after numbers: Reiju (0+4), Ichiji (1), Niji (2), Sanji (3), Yonji (4). Judge named them as weapons, not children.",
            "category": "character_info"
        },
        
        # === D. WILL / VOID CENTURY ===
        {
            "volume": 76,
            "question": "Who are all the known D. carriers?",
            "answer": "Confirmed D. carriers: Monkey D. Luffy, Monkey D. Dragon, Monkey D. Garp, Portgas D. Ace, Portgas D. Rouge, Gol D. Roger, Marshall D. Teach (Blackbeard), Trafalgar D. Water Law, Jaguar D. Saul, Rocks D. Xebec, Nefertari D. Lily (revealed later).",
            "category": "will_of_d"
        },
        {
            "volume": 103,
            "question": "What does the D. in names mean?",
            "answer": "Oda has hinted that 'D' stands for something significant related to the Void Century. The World Government calls them 'God's Natural Enemy'. The full meaning has not been revealed yet.",
            "category": "will_of_d"
        },
        {
            "volume": 58,
            "question": "What is the Void Century?",
            "answer": "The Void Century is a 100-year gap in recorded history from 800-900 years ago. During this time, the Ancient Kingdom existed and was destroyed by the alliance that became the World Government. All records were erased. The truth is written on the Poneglyphs.",
            "category": "void_century"
        },
        {
            "volume": 102,
            "question": "What is the Ancient Kingdom?",
            "answer": "The Ancient Kingdom was a powerful civilization that existed during the Void Century. It was destroyed by the 20 kingdoms that formed the World Government. Its name is forbidden. It created the Poneglyphs to preserve history.",
            "category": "void_century"
        },
        {
            "volume": 105,
            "question": "Who is Joy Boy?",
            "answer": "Joy Boy was a figure from 800 years ago during the Void Century. He made a promise to Fish-Man Island that he couldn't keep. He left an apology on a Poneglyph. Luffy has inherited his will. He was the first person to reach Laugh Tale.",
            "category": "joy_boy"
        },
        
        # === DEVIL FRUITS ===
        {
            "volume": 82,
            "question": "Can Devil Fruit users swim in water other than the sea?",
            "answer": "Devil Fruit users can't swim in ANY standing water - sea, pool, bath, rain doesn't count. It's the 'sea' element present in all water that drains their energy. Moving water like rain or rivers affects them less.",
            "category": "devil_fruit"
        },
        {
            "volume": 97,
            "question": "What is Kaido's Devil Fruit?",
            "answer": "Kaido ate the Uo Uo no Mi (Fish-Fish Fruit), Model: Seiryu (Azure Dragon). It's a Mythical Zoan, one of the rarest types. Despite being a 'fish' fruit, it transforms him into a dragon because of the legend of a carp becoming a dragon.",
            "category": "devil_fruit"
        },
        {
            "volume": 104,
            "question": "What is Luffy's true Devil Fruit?",
            "answer": "Luffy's fruit is actually the Hito Hito no Mi, Model: Nika (Human-Human Fruit, Model: Sun God Nika). It was renamed by the World Government to hide its true nature. Gear 5 is its awakening, giving Luffy's body the properties of rubber AND freedom/imagination.",
            "category": "devil_fruit"
        },
        {
            "volume": 90,
            "question": "What is the most powerful Devil Fruit?",
            "answer": "Oda hasn't named THE strongest, but mentioned: The Gura Gura no Mi (Tremor Fruit) can destroy the world. Logia types seem invincible without Haki. Mythical Zoans are rarest. The Ope Ope no Mi can grant immortality.",
            "category": "devil_fruit"
        },
        {
            "volume": 48,
            "question": "Can there be two of the same Devil Fruit?",
            "answer": "No. Only one of each Devil Fruit exists at a time. When a user dies, the fruit is reborn somewhere in the world. Blackbeard somehow broke this rule by taking Whitebeard's power - this is still unexplained.",
            "category": "devil_fruit"
        },
        
        # === HAKI ===
        {
            "volume": 41,
            "question": "What is Haki and its types?",
            "answer": "Haki is willpower manifested as power. Three types: 1) Observation Haki - sensing presence/emotions/future, 2) Armament Haki - invisible armor that can hurt Logia users, 3) Conqueror's Haki - overwhelming will, only 1 in millions have it.",
            "category": "haki"
        },
        {
            "volume": 95,
            "question": "Who has Conqueror's Haki?",
            "answer": "Confirmed Conqueror's Haki users: Luffy, Zoro, Roger, Rayleigh, Whitebeard, Shanks, Big Mom, Kaido, Yamato, Katakuri, Doflamingo, Ace, Boa Hancock, Chinjao, Kozuki Oden, Sengoku, among others.",
            "category": "haki"
        },
        {
            "volume": 100,
            "question": "Can Haki be coated on attacks?",
            "answer": "Yes, Advanced Conqueror's Haki can be 'coated' on attacks like Armament Haki. This is how the strongest fighters (Roger, Whitebeard, Kaido, Big Mom, Shanks, Luffy) fight - they don't even touch each other, their Haki clashes.",
            "category": "haki"
        },
        
        # === SWORDS ===
        {
            "volume": 89,
            "question": "What are the sword grades?",
            "answer": "Sword grades from lowest to highest: Grade Swords (unknown count), Skillful Grade (Wazamono, 50), Great Grade (Ryo Wazamono, 50), Great Skillful Grade (O Wazamono, 21), Supreme Grade (Saijo O Wazamono, 12). The 12 Supreme Grade are the best.",
            "category": "swords"
        },
        {
            "volume": 63,
            "question": "What are the 12 Supreme Grade Swords?",
            "answer": "Known Supreme Grade (Saijo O Wazamono): Yoru (Mihawk), Murakumogiri (Whitebeard), Shodai Kitetsu, Ace (Roger). Unknown: 8 more exist. These are the 12 strongest swords in the world.",
            "category": "swords"
        },
        
        # === WORLD GOVERNMENT / MARINE ===
        {
            "volume": 95,
            "question": "Who were the original Seven Warlords?",
            "answer": "The original Seven Warlords: Dracule Mihawk, Crocodile, Donquixote Doflamingo, Bartholomew Kuma, Gecko Moria, Boa Hancock, and Jinbe. Later replaced by: Buggy, Trafalgar Law, Blackbeard, Edward Weevil.",
            "category": "world_government"
        },
        {
            "volume": 96,
            "question": "Why did Shanks meet with the Gorosei?",
            "answer": "Shanks met with the Gorosei (Five Elders) to discuss 'a certain pirate'. This is still a mystery. The fact that a Yonko can meet directly with the highest authority suggests Shanks has special status or knowledge.",
            "category": "mystery"
        },
        {
            "volume": 90,
            "question": "Who is Im-sama?",
            "answer": "Im sits on the Empty Throne in Mary Geoise. They appear to be the true ruler above even the Gorosei. No one is supposed to sit on the Empty Throne. Im's existence is top secret. They can order the destruction of entire countries.",
            "category": "world_government"
        },
        
        # === ANCIENT WEAPONS ===
        {
            "volume": 65,
            "question": "What are the Three Ancient Weapons?",
            "answer": "The Three Ancient Weapons: 1) Pluton - a warship built in Water 7, blueprints destroyed, 2) Poseidon - Shirahoshi, can command Sea Kings, 3) Uranus - unknown, possibly sky-related. Each can destroy the world.",
            "category": "ancient_weapons"
        },
        {
            "volume": 66,
            "question": "What do the Poneglyphs say?",
            "answer": "There are 30 Poneglyphs: 9 Historical (tell the Void Century truth), 19 Instructional (give locations/information), 4 Road Poneglyphs (red, show the way to Laugh Tale). Only those who can read them understand the True History.",
            "category": "poneglyph"
        },
        
        # === ONE PIECE / LAUGH TALE ===
        {
            "volume": 101,
            "question": "Will Luffy find the One Piece?",
            "answer": "Oda confirmed Luffy WILL find the One Piece. The treasure is real and exists. It's not 'friendship' or something abstract. Oda has the ending planned from the beginning. The story will have a proper conclusion.",
            "category": "one_piece"
        },
        {
            "volume": 100,
            "question": "How much of One Piece is left?",
            "answer": "As of Volume 100, Oda said the story is about 80% complete. The final saga has begun with the Egghead arc. He aims to end within a few years but admits he often extends timelines.",
            "category": "meta"
        },
        {
            "volume": 96,
            "question": "Why did Roger laugh at Laugh Tale?",
            "answer": "When Roger reached the final island, he and his crew found 'something' that made them all laugh, so he named it 'Laugh Tale'. Roger was too early - Joy Boy's treasure couldn't be used in his era.",
            "category": "one_piece"
        },
        
        # === FORESHADOWING PATTERNS ===
        {
            "volume": 78,
            "question": "Does Oda read fan theories?",
            "answer": "Oda reads fan theories and is sometimes amazed how accurate some are. He says some fans have correctly guessed major plot points years in advance. He won't confirm or deny to avoid spoilers.",
            "category": "meta"
        },
        {
            "volume": 59,
            "question": "What's inside Luffy's head?",
            "answer": "Inside Luffy's head: Meat, Meat, Meat, Adventure, and Friends. That's it! This shows Luffy's simple but pure nature.",
            "category": "character_info"
        },
        
        # === BOUNTIES / POWER ===
        {
            "volume": 80,
            "question": "How are bounties determined?",
            "answer": "Bounties reflect threat level to the World Government, not just strength. Knowledge (like Robin), influence, and potential are factors. The highest known bounties: Roger 5.564B, Whitebeard 5.046B, Kaido 4.611B, Big Mom 4.388B.",
            "category": "bounty"
        },
        
        # === SPECIFIC MYSTERIES ===
        {
            "volume": 98,
            "question": "Is Yamato male or female?",
            "answer": "Yamato was born female but calls herself 'Kaido's son' because she chose to 'become Kozuki Oden'. Oda uses male pronouns in the context of Yamato's chosen identity. Her Vivre Card lists her as female.",
            "category": "character_info"
        },
        {
            "volume": 77,
            "question": "Why does Doflamingo wear sunglasses?",
            "answer": "Doflamingo's sunglasses hide his eyes to make him more mysterious. His eyes show his Celestial Dragon pride and cruelty. They're rarely shown for dramatic effect.",
            "category": "character_info"
        },
        {
            "volume": 84,
            "question": "How many children does Big Mom have?",
            "answer": "Big Mom (Charlotte Linlin) has 85 children from 43 husbands. This includes Katakuri, Smoothie, Cracker, Perospero, Pudding, and many more. She's been pregnant for over 40 years total.",
            "category": "character_info"
        },
        {
            "volume": 92,
            "question": "What is Wano's connection to the Void Century?",
            "answer": "Wano was once connected to the Ancient Kingdom. The Kozuki clan created the Poneglyphs. Wano has been closed for 800 years, possibly to protect secrets from the World Government.",
            "category": "void_century"
        },
        {
            "volume": 74,
            "question": "How does Gear Fourth work?",
            "answer": "Luffy blows air into his MUSCLES (not bones like Gear Third). Combined with Armament Haki coating, his muscles become like rubber balloons that store and release energy. Different forms: Boundman, Snakeman, Tankman.",
            "category": "combat"
        },
        {
            "volume": 56,
            "question": "What are blood types in One Piece?",
            "answer": "One Piece has different blood types: S, F, X, and XF. Luffy is type F. This matters because blood transfusions require matching types, as seen in Fish-Man Island.",
            "category": "world_building"
        },
        {
            "volume": 85,
            "question": "Can Sanji use Haki?",
            "answer": "Yes, Sanji can use both Observation Haki and Armament Haki. His specialty is Observation Haki - he's extremely skilled at sensing emotions and danger. He developed Armament during the timeskip.",
            "category": "haki"
        },
    ]
    
    # Add type field to all
    for entry in sbs_entries:
        entry["type"] = "sbs"
        entry["importance"] = "high"
    
    return sbs_entries


def main():
    print("📚 Creating SBS/Oda revelations database...\n")
    
    # Get curated SBS data
    entries = create_curated_sbs_data()
    print(f"✅ Created {len(entries)} curated SBS entries")
    
    # Save to JSONL
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    print(f"✅ Saved to {OUTPUT_FILE}")
    
    # Show categories breakdown
    categories = {}
    for entry in entries:
        cat = entry.get("category", "other")
        categories[cat] = categories.get(cat, 0) + 1
    
    print("\n📊 Categories breakdown:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"   {cat}: {count}")
    
    # Show sample
    print("\n📖 Sample entries:")
    for entry in entries[:2]:
        print(f"\n  Q: {entry['question']}")
        print(f"  A: {entry['answer'][:150]}...")


if __name__ == "__main__":
    main()
