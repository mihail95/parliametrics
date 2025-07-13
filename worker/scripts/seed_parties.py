import requests
from db import SessionLocal, init_db
from models import Party
from sqlalchemy.exc import SQLAlchemyError
from helpers import clean_name

API_URL = "https://www.parliament.bg/api/v1/coll-list/bg/2"

# Optional: manual overrides for abbreviation
known_abbreviations = {
    "ГЕРБ – СДС": "ГЕРБ-СДС",
    "Продължаваме Промяната – Демократична България": "ПП-ДБ",
    "ВЪЗРАЖДАНЕ": "ВЪЗРАЖДАНЕ",
    "Движение за права и свободи – Ново начало – ДПС – Ново начало": "Демокрация, права и свободи – ДПС",
    "БСП – ОБЕДИНЕНА ЛЕВИЦА": "БСП",
    "Има Такъв Народ": "ИТН",
    "Алианс за права и свободи": "АПС",
    "ПП МЕЧ": "МЕЧ",
    "ВЕЛИЧИЕ": "ВЕЛИЧИЕ",
    "Нечленуващи в ПГ": "БезПГ"
}

def seed_parties():
    print("📡 Fetching party list from API...")
    headers = {
        "User-Agent": "Parliametrics/0.1 (mihail.chifligarov@ruhr-uni-bochum.de)"
    }
    res = requests.get(API_URL, headers=headers)
    res.raise_for_status()
    data = res.json()

    init_db()
    db = SessionLocal()
    added = 0
    added_parties = set()

    try:
        for item in data:
            raw_name = item["A_ns_CL_value"]
            party_api_id = item["A_ns_C_id"]

            name = clean_name(raw_name)
            abbreviation = known_abbreviations.get(name, name.split()[-1])

            exists = db.query(Party).filter_by(party_name=name).first()
            recently_added = name in added_parties
            if exists or recently_added:
                print(f"⚠️  Already exists: {name}")
                if exists and party_api_id != exists.party_api_id:
                    exists.party_api_id = party_api_id
                continue

            party = Party(party_name=name, party_abbreviation=abbreviation, party_api_id=party_api_id)
            db.add(party)
            added += 1
            added_parties.add(name)
            print(f"➕ Added: {name} ({abbreviation})")

        db.commit()
        print(f"\n✅ Done. Added {added} new parties.")
    except SQLAlchemyError as e:
        db.rollback()
        print(f"❌ Database error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_parties()