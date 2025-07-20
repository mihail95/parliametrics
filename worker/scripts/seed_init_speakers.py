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
        start_year = 2024
        start_month = 11
        today = date.today()

        # Manually add fallback speakers and affiliations
        fallback_roles = [
            {"party_id": 1, "name": "ПРЕДСЕДАТЕЛ"},
            {"party_id": 2, "name": "МИНИСТЪР"},
            {"party_id": 3, "name": "ДОКЛАДЧИК"}
        ]

        for role in fallback_roles:
            party = db.query(Party).filter_by(party_id=role["party_id"]).first()
            if not party:
                print(f"❌ Missing fallback party: {role['name']}")
                continue

            speaker = db.query(Speaker).filter_by(speaker_name=role["name"]).first()
            if not speaker:
                speaker = Speaker(
                    speaker_name=role["name"],
                    first_name="",
                    middle_name="",
                    last_name=""
                )
                db.add(speaker)
                db.flush()
                print(f"➕ Added fallback speaker: {role['name']} (id={speaker.speaker_id})")

            exists = db.query(SpeakerPartyAffiliation).filter_by(
                speaker_speaker_id=speaker.speaker_id,
                party_party_id=party.party_id
            ).first()

            if not exists:
                affiliation = SpeakerPartyAffiliation(
                    speaker=speaker,
                    party=party,
                    start_date=None,
                    end_date=None
                )
                db.add(affiliation)
                db.flush()
                print(f"✅ Fallback affiliation: {role['name']} → {party.party_name}")
            else:
                print(f"⚠️ Fallback affiliation already exists: {role['name']} → {party.party_name}")

        for party in parties:
            if party.party_id in (0, 1):
                continue  # We'll handle them separately below

            party_api_id = party.party_api_id
            if not party_api_id:
                continue  # Skip if somehow missing

            for year in range(start_year, today.year + 1):
                month_start = start_month if year == start_year else 1
                month_end = today.month if year == today.year else 12

                for month in range(month_start, month_end + 1):
                    url = f"https://www.parliament.bg/api/v1/coll-list-mp/bg/{party_api_id}/2?date={year}-{'{:02d}'.format(month)}-01"
                    res = requests.get(url, headers=headers)
                    if not res.ok:
                        print(f"❌ Failed to fetch party {party.party_name} for {year}-{month:02}")
                        continue
                    data = res.json().get("colListMP", [])

                    for mp in data:
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
