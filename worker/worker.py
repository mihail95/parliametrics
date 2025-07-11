from db import SessionLocal
from models import Speaker

db = SessionLocal()

speakers = db.query(Speaker).all()
print(f"✅ Found {len(speakers)} speakers in the DB.")
for speaker in speakers:
    print(f"- {speaker.speaker_name}")

db.close()