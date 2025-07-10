from db import SessionLocal, init_db
from models import Party, Speaker, Speech, SpeakerPartyAffiliation
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

init_db()
db = SessionLocal()

try:
    party = Party(party_name="ГЕРБ", party_abbreviation="GERB")

    speaker = Speaker(speaker_name="Бойко Борисов")

    affiliation = SpeakerPartyAffiliation(
        speaker=speaker, party=party,
        start_date=datetime(2006, 1, 1)
    )

    speech = Speech(
        speech_content="Уважаеми господин председател...",
        affiliation=affiliation
    )

    db.add_all([party, speaker, speech])
    db.commit()
    print("✅ Seeded sample data.")
except Exception as e:
    db.rollback()
    print(f"❌ Transaction failed: {e}")
finally:
    db.close()