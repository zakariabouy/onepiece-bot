# scripts/add_devil_fruits.py — Add Devil Fruit data to database
"""
Adds comprehensive Devil Fruit information to the database.
Run: python scripts/add_devil_fruits.py
"""

import sqlite3

DB_PATH = "onepiece.db"

DEVIL_FRUITS = [
    # Paramecia
    {
        "name": "Gomu Gomu no Mi (Hito Hito no Mi, Model: Nika)",
        "type": "Mythical Zoan",
        "user": "Monkey D. Luffy",
        "ability": "Originally thought to be a Paramecia that grants rubber powers, it was revealed to be the Hito Hito no Mi, Model: Nika - a Mythical Zoan that allows the user to transform into the legendary Sun God Nika. Grants rubber-like body properties, incredible freedom in combat, Gear transformations (2nd, 3rd, 4th, 5th), and the awakened form Gear 5 which grants cartoon-like reality manipulation powers."
    },
    {
        "name": "Bara Bara no Mi",
        "type": "Paramecia",
        "user": "Buggy",
        "ability": "Allows the user to split their body into separate pieces and control them remotely. The user becomes immune to slashing attacks. Buggy can levitate his body parts but his feet must remain grounded."
    },
    {
        "name": "Mera Mera no Mi",
        "type": "Logia",
        "user": "Sabo (formerly Portgas D. Ace)",
        "ability": "Allows the user to create, control, and transform into fire. One of the most powerful Logia fruits. The user can generate massive firestorms and is immune to most physical attacks. Previously wielded by Ace before his death at Marineford."
    },
    {
        "name": "Yami Yami no Mi",
        "type": "Logia",
        "user": "Marshall D. Teach (Blackbeard)",
        "ability": "Allows the user to create and control darkness. Unique among Logia as it doesn't grant intangibility - instead it absorbs all attacks. Can nullify other Devil Fruit powers through physical contact and has gravity-like pulling abilities."
    },
    {
        "name": "Gura Gura no Mi",
        "type": "Paramecia",
        "user": "Marshall D. Teach (formerly Edward Newgate/Whitebeard)",
        "ability": "Allows the user to create powerful shockwaves and earthquakes. Known as the strongest Paramecia, capable of destroying the world. Can create tsunamis and tilt entire islands. Blackbeard somehow obtained it after Whitebeard's death."
    },
    {
        "name": "Ope Ope no Mi",
        "type": "Paramecia",
        "user": "Trafalgar D. Water Law",
        "ability": "Creates a spherical 'Room' where the user has complete control. Can perform impossible surgeries, teleport objects, switch minds/personalities, and even grant eternal youth (at the cost of the user's life). Called the 'Ultimate Devil Fruit'."
    },
    {
        "name": "Hana Hana no Mi",
        "type": "Paramecia",
        "user": "Nico Robin",
        "ability": "Allows the user to sprout duplicate body parts (mainly arms) on any surface within range. Robin can create giant limbs, wings for flight, and even full-body clones. Damage to sprouted parts transfers to the user."
    },
    {
        "name": "Suna Suna no Mi",
        "type": "Logia",
        "user": "Crocodile",
        "ability": "Allows the user to create, control, and transform into sand. Can dehydrate anything on contact, create sandstorms, and turn ground into quicksand. Weakness is water - when wet, the user becomes solid."
    },
    {
        "name": "Hie Hie no Mi",
        "type": "Logia",
        "user": "Kuzan (Aokiji)",
        "ability": "Allows the user to create, control, and transform into ice. Can freeze entire oceans, create ice weapons, and freeze opponents solid. One of the most powerful Logia fruits wielded by former Admiral Aokiji."
    },
    {
        "name": "Magu Magu no Mi",
        "type": "Logia",
        "user": "Sakazuki (Akainu)",
        "ability": "Allows the user to create, control, and transform into magma. Has the highest offensive power among Devil Fruits. Can vaporize ice, burn through anything, and even permanently scar Luffy's chest. Fleet Admiral Akainu's power."
    },
    {
        "name": "Pika Pika no Mi",
        "type": "Logia",
        "user": "Borsalino (Kizaru)",
        "ability": "Allows the user to create, control, and transform into light. Grants the user movement at light speed, laser attacks, and light-based weapons. Admiral Kizaru's nigh-unstoppable power."
    },
    {
        "name": "Uo Uo no Mi, Model: Seiryu",
        "type": "Mythical Zoan",
        "user": "Kaido",
        "ability": "Allows transformation into an Azure Dragon from Eastern mythology. Grants flight via flame clouds, devastating fire breath (Bolo Breath), wind scythes, lightning, and immense durability. Considered the strongest creature's fruit."
    },
    {
        "name": "Tori Tori no Mi, Model: Phoenix",
        "type": "Mythical Zoan",
        "user": "Marco",
        "ability": "Allows transformation into a phoenix. Grants flight, blue regenerative flames that can heal any wound, and the ability to heal others. Marco served as Whitebeard's first division commander."
    },
    {
        "name": "Nikyu Nikyu no Mi",
        "type": "Paramecia",
        "user": "Bartholomew Kuma",
        "ability": "Creates paw pads that can repel anything - physical attacks, air (creating shockwaves), pain/fatigue, and even people across vast distances. Kuma could send people flying for days to specific locations."
    },
    {
        "name": "Doku Doku no Mi",
        "type": "Paramecia",
        "user": "Magellan",
        "ability": "Allows the user to create and control various types of poison. Can create poison hydras, venomous gas, and the ultimate poison 'Venom Demon'. Impel Down's chief warden Magellan nearly killed Luffy with it."
    },
    {
        "name": "Mochi Mochi no Mi",
        "type": "Special Paramecia",
        "user": "Charlotte Katakuri",
        "ability": "Allows the user to create, control, and transform into mochi (sticky rice). A Special Paramecia that grants Logia-like properties. Combined with advanced Observation Haki, Katakuri was nearly unbeatable."
    },
    {
        "name": "Soru Soru no Mi",
        "type": "Paramecia",
        "user": "Charlotte Linlin (Big Mom)",
        "ability": "Allows manipulation of souls. Can extract lifespan from those who fear the user, place souls into objects to create Homies, and even manipulate weather through special Homies like Zeus, Prometheus, and Hera."
    },
    {
        "name": "Ito Ito no Mi",
        "type": "Paramecia",
        "user": "Donquixote Doflamingo",
        "ability": "Allows the user to create and control strings. Can manipulate people like puppets, create sharp cutting threads, fly using cloud attachment, and the awakened form can turn surroundings into strings."
    },
    {
        "name": "Goro Goro no Mi",
        "type": "Logia",
        "user": "Enel",
        "ability": "Allows the user to create, control, and transform into lightning. Grants 200 million volts of electricity, lightning speed travel, and the ability to restart one's own heart. Enel combined it with Observation Haki to 'hear' across Skypiea."
    },
    {
        "name": "Zushi Zushi no Mi",
        "type": "Paramecia",
        "user": "Fujitora (Issho)",
        "ability": "Allows the user to manipulate gravitational forces. Can increase gravity to crush opponents, levitate objects and people, and even summon meteorites from space. Admiral Fujitora's devastating power."
    },
]

def main():
    print("=" * 50)
    print("Adding Devil Fruits to Database")
    print("=" * 50)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    added = 0
    for fruit in DEVIL_FRUITS:
        fruit_id = f"devilfruit_{fruit['name'].lower().replace(' ', '_').replace(',', '').replace(':', '')[:50]}"
        
        # Build text
        text = f"{fruit['name']} is a {fruit['type']} Devil Fruit eaten by {fruit['user']}. {fruit['ability']}"
        
        # Check if exists
        existing = c.execute("SELECT id FROM notes WHERE id = ?", (fruit_id,)).fetchone()
        if existing:
            print(f"  Skipping {fruit['name'][:30]}... (exists)")
            continue
        
        c.execute(
            "INSERT INTO notes (id, title, arc, text) VALUES (?, ?, ?, ?)",
            (fruit_id, fruit['name'], "Devil Fruit", text)
        )
        added += 1
        print(f"  ✓ Added: {fruit['name'][:40]}...")
    
    conn.commit()
    conn.close()
    
    print(f"\n✓ Added {added} Devil Fruits!")
    print("\n⚠️  Delete embeddings_cache.npz to rebuild index!")

if __name__ == "__main__":
    main()
