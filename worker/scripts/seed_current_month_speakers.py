from models import Speaker, SpeakerPartyAffiliation, Party
from sqlalchemy.exc import SQLAlchemyError
from db import SessionLocal
import requests
from datetime import datetime
from datetime import date

def seed_speakers_and_affiliations():
    headers = {
        "User-Agent": "Parliametrics/0.1 (mihail.chifligarov@ruhr-uni-bochum.de)"
    }
    db = SessionLocal()
    try:
        parties = db.query(Party).all()
        for party in parties:
            if party.party_id == 0:
                continue
            party_api_id = party.party_api_id
            current_year = date.today().year
            current_month = date.today().month
            
            url = f"https://www.parliament.bg/api/v1/coll-list-mp/bg/{party_api_id}/2?date={current_year}-{'{:02d}'.format(current_month)}-01"
            res = requests.get(url, headers=headers)
            if not res.ok:
                print(f"❌ Failed to fetch party {party.party_name}")
                continue
            data = res.json().get("colListMP", [])
            for mp in data:
                # Extract and clean speaker name parts
                first_name = mp["A_ns_MPL_Name1"].strip().title()
                middle_name = mp["A_ns_MPL_Name2"].strip().title()
                last_name = mp["A_ns_MPL_Name3"].strip().title()
                speaker_name = f"{first_name} {last_name}"

                start_date = datetime.strptime(mp["A_ns_MSP_date_F"], "%Y-%m-%d").date()
                end_date_str = mp.get("A_ns_MSP_date_T")
                end_date = (
                    datetime.strptime(end_date_str, "%Y-%m-%d").date()
                    if end_date_str and end_date_str != "9999-12-31"
                    else None
                )

                # Lookup speaker by full name
                speaker = db.query(Speaker).filter_by(
                    first_name=first_name,
                    middle_name=middle_name,
                    last_name=last_name
                ).first()

                if not speaker:
                    speaker = Speaker(
                        first_name=first_name,
                        middle_name=middle_name,
                        last_name=last_name,
                        speaker_name=speaker_name
                    )
                    db.add(speaker)
                    db.flush()

                # Check if affiliation already exists
                exists = db.query(SpeakerPartyAffiliation).filter_by(
                    speaker_speaker_id=speaker.speaker_id,
                    party_party_id=party.party_id
                ).first()

                if not exists:
                    affiliation = SpeakerPartyAffiliation(
                        speaker=speaker,
                        party=party,
                        start_date=start_date,
                        end_date=end_date
                    )
                    db.add(affiliation)
                    db.flush()
                    print(f"✅ Added: {speaker.full_name} → {party.party_name}")
                else:
                    print(f"⚠️ Already exists: {speaker.full_name} → {party.party_name}")

        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        print("❌ Error:", e)
    finally:
        db.close()

if __name__ == "__main__":
    seed_speakers_and_affiliations()
