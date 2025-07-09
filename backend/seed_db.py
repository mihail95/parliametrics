from db import SessionLocal, init_db
from models import Party, Speaker, Speech, SpeakerPartyAffiliation
from datetime import datetime

init_db()
db = SessionLocal()

party = Party(name="ГЕРБ", abbreviation="GERB")

speaker = Speaker(name="Бойко Борисов")

affiliation = SpeakerPartyAffiliation(
    speaker=speaker, party=party,
    start_date=datetime(2006, 1, 1)
)

speech = Speech(
    content="Уважаеми господин председател...",
    speaker=speaker,
    affiliation=affiliation
)

db.add_all([party, speaker, speech])
db.commit()
db.close()

print("✅ Seeded sample data.")