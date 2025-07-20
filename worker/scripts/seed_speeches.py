from models import Speaker, SpeakerPartyAffiliation, Party, Speech
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from db import SessionLocal
from typing import List, Tuple, Optional
from datetime import datetime
from datetime import date
from collections import defaultdict
import requests
import re
import sys
import unicodedata
from rapidfuzz import process, fuzz
import traceback
import time

# Lowercased and normalized non-speaker labels (full or prefix-based)
NON_SPEAKER_PREFIXES = [
    "реплика", "реплики", "декларира", "декларация", "първо гласуване на", "второ гласуване на", "трето гласуване на",
    "запазване на", "европа в света", "изказвания", "изказване", "гласуване", "отговори", "въпроси", "физическите лица"
]

def is_likely_not_speaker(name: str) -> bool:
    norm = normalize(name)
    # Skip if it's too short and not a valid role
    if len(norm.split()) == 1 and norm not in {"председател", "министър", "докладчик"}:
        return True
    # Skip if name starts with known invalid prefix
    return any(norm.startswith(prefix) for prefix in NON_SPEAKER_PREFIXES)

def normalize(text: str) -> str:
    return unicodedata.normalize("NFKC", text.strip().lower())

def fuzzy_match(name: str, choices: list[str], score_cutoff: int = 75) -> Optional[str]:
    result = process.extractOne(name, choices, scorer=fuzz.ratio, score_cutoff=score_cutoff)
    return result[0] if result else None
    
def build_disambiguated_speaker_lookup(affiliations):
    speaker_lookup = defaultdict(list)

    def normalize(text):
        return unicodedata.normalize("NFKC", text.strip().lower())

    for aff in affiliations:
        s = aff.speaker
        party_id = aff.party_party_id
        start = aff.start_date
        end = aff.end_date

        names = {
            f"{s.first_name} {s.middle_name}",
            f"{s.first_name} {s.last_name}",
            f"{s.middle_name} {s.last_name}",
            f"{s.first_name} {s.middle_name} {s.last_name}",
            s.speaker_name,
            s.first_name,
            s.middle_name,
            s.last_name,
        }

        for name in names:
            norm = normalize(name)
            if norm:
                speaker_lookup[norm].append((s, party_id, start, end))  # now 4-tuple

    return speaker_lookup


def extract_and_insert_speeches_from_api(
    seatings: dict[int, dict[int, list[dict]]],
    parties: List[Party],
    affiliations: List[SpeakerPartyAffiliation]
):
    db = SessionLocal()
    try:
        speaker_lookup = build_disambiguated_speaker_lookup(affiliations)
        party_lookup = {normalize(p.party_name): p for p in parties}
        abbrev_lookup = {normalize(p.party_abbreviation): p for p in parties}
        speaker_names = list(speaker_lookup.keys())
        party_names = list(party_lookup.keys()) + list(abbrev_lookup.keys())

        # ✅ Cache for last-used affiliation per speaker
        speaker_affiliation_cache: dict[str, SpeakerPartyAffiliation] = {}

        for year_data in seatings.values():
            for month_data in year_data.values():
                for seating in month_data:
                    t_id = seating["t_id"]
                    speech_date = date.fromisoformat(seating["t_date"])
                    url = f"https://www.parliament.bg/api/v1/pl-sten/{t_id}"

                    try:
                        response = requests.get(url, headers={"User-Agent": "Parliametrics/0.1"})
                        response.raise_for_status()
                        steno_text = response.json().get("Pl_Sten_body", "")
                    except Exception as e:
                        print(f"❌ Failed to fetch stenographic record {t_id}: {e}")
                        sys.exit(1)

                    speeches = re.findall(
                        r"^([А-Я\s]+)(\(.*\))*:([\S\s]*?)(?=^([А-Я\s]+)(\(.*\))*:|\Z)",
                        steno_text,
                        re.M
                    )

                    for raw_speaker, annotation, content, *_ in speeches:
                        # Skip invalid lines that look like speaker names but aren't
                        if is_likely_not_speaker(raw_speaker):
                            print(f"⚠️ Skipping invalid speaker line: {raw_speaker}")
                            continue
                        try:
                            content_clean = re.sub(r"<br\s*/?>", "\n", content, flags=re.IGNORECASE).strip()
                            content_clean = re.sub(r"\n+", "\n", content_clean)
                            content_clean = content_clean.strip()
                            norm_speaker = normalize(raw_speaker)
                            from_tribune = True
                            is_continuation = False
                            party = None
                            speaker = None
                            affiliation = None
                            
                            # Try to extract party from annotation
                            if annotation:
                                party_match = re.search(r"^\(([^(),]+)", annotation)
                                if party_match:
                                    raw_party = normalize(party_match.group(1))
                                    party = (
                                        party_lookup.get(raw_party)
                                        or abbrev_lookup.get(raw_party)
                                    )
                                    if not party:
                                        # Try fuzzy full match
                                        fuzzy = fuzzy_match(raw_party, party_names)
                                        if fuzzy:
                                            party = party_lookup.get(fuzzy) or abbrev_lookup.get(fuzzy)

                                        # Try partial fuzzy match if still not found
                                        if not party:
                                            best_score = 0
                                            best_match = None
                                            for name in party_names:
                                                score = fuzz.partial_ratio(raw_party, name)
                                                if score > best_score and score >= 80:  # you can adjust threshold
                                                    best_score = score
                                                    best_match = name
                                            if best_match:
                                                party = party_lookup.get(best_match) or abbrev_lookup.get(best_match)

                                if "от място" in annotation:
                                    from_tribune = False

                            # Speaker resolution
                            candidates = speaker_lookup.get(norm_speaker)
                            if not candidates:
                                match = fuzzy_match(norm_speaker, speaker_names)
                                candidates = speaker_lookup.get(match) if match else None

                            if candidates:
                                if len(candidates) == 1:
                                    speaker = candidates[0][0]
                                elif party:
                                    # 1. Strict match: party and valid date
                                    matches = [
                                        (s, start, end) for (s, pid, start, end) in candidates
                                        if pid == party.party_id and
                                        (start is None or start <= speech_date) and
                                        (end is None or speech_date <= end)
                                    ]
                                    if len(matches) == 1:
                                        speaker = matches[0][0]
                                    else:
                                        # 2. Relaxed: valid date, any party
                                        time_valid = [
                                            (s, start) for (s, _, start, end) in candidates
                                            if (start is None or start <= speech_date) and
                                            (end is None or speech_date <= end)
                                        ]
                                        if len(time_valid) == 1:
                                            speaker = time_valid[0][0]
                                            print(f"⚠️ Party mismatch; using time-valid fallback for '{raw_speaker}' on {speech_date}")
                                        else:
                                            # 3. Fallback: most recent affiliation
                                            sorted_candidates = sorted(
                                                candidates,
                                                key=lambda x: x[2] or date.min,  # sort by start date
                                                reverse=True
                                            )
                                            speaker = sorted_candidates[0][0]
                                            print(f"⚠️ Using latest affiliation fallback for '{raw_speaker}' on {speech_date}'")

                            # 1. If no party is given but speaker is known and cached
                            if not annotation and norm_speaker in speaker_affiliation_cache:
                                affiliation = speaker_affiliation_cache[norm_speaker]
                                is_continuation = True

                            # 2. Regular affiliation match
                            if not affiliation and speaker and party:
                                affiliation = next(
                                    (a for a in affiliations
                                    if a.speaker_speaker_id == speaker.speaker_id and
                                        a.party_party_id == party.party_id),
                                    None
                                )

                            # 3. Fallback for ПРЕДСЕДАТЕЛ
                            if not affiliation and fuzz.partial_ratio("председател", norm_speaker) >= 85:
                                affiliation = next(
                                    (a for a in affiliations
                                    if a.speaker_speaker_id == 1 and a.party_party_id == 1),
                                    None
                                )
                                if affiliation:
                                    print(f"⚠️ Using fallback affiliation for ПРЕДСЕДАТЕЛ on {speech_date}")

                            # 4. Fallback for МИНИСТЪР
                            if not affiliation and fuzz.partial_ratio("министър", norm_speaker) >= 85:
                                affiliation = next(
                                    (a for a in affiliations
                                    if a.speaker_speaker_id == 2 and a.party_party_id == 2),
                                    None
                                )
                                if affiliation:
                                    print(f"⚠️ Using fallback affiliation for МИНИСТЪР on {speech_date}")

                            # 5. Fallback for ДОКЛАДЧИК
                            if not affiliation and fuzz.partial_ratio("докладчик", norm_speaker) >= 85:
                                affiliation = next(
                                    (a for a in affiliations
                                    if a.speaker_speaker_id == 3 and a.party_party_id == 3),
                                    None
                                )
                                if affiliation:
                                    print(f"⚠️ Using fallback affiliation for ДОКЛАДЧИК on {speech_date}")

                            # 6. FINAL fallback: use speaker’s most recent affiliation (if available)
                            if not affiliation and speaker:
                                affs = [
                                    a for a in affiliations
                                    if a.speaker_speaker_id == speaker.speaker_id
                                ]
                                if affs:
                                    affiliation = sorted(
                                        affs,
                                        key=lambda a: a.start_date or date.min,
                                        reverse=True
                                    )[0]
                                    party_name = next((p.party_name for p in parties if p.party_id == affiliation.party_party_id), f"ID={affiliation.party_party_id}")
                                    print(f"⚠️ Using latest affiliation fallback for '{raw_speaker}' → {party_name} on {speech_date}")
                            
                            # 7. Fallback for unknown/external speakers
                            if not affiliation and not speaker:
                                # Insert new Speaker (if not found)
                                speaker = Speaker(
                                    speaker_name=raw_speaker.strip().title(),
                                    first_name="",
                                    middle_name="",
                                    last_name=""
                                )
                                db.add(speaker)
                                db.flush()

                                # Check if "ВЪНШЕН" party is in local list
                                fallback_party = next((p for p in parties if p.party_id == 9999), None)
                                if not fallback_party:
                                    fallback_party = Party(
                                        party_id=9999,
                                        party_name="ВЪНШЕН",
                                        party_abbreviation="",
                                        party_api_id=None
                                    )
                                    db.add(fallback_party)
                                    db.flush()
                                    parties.append(fallback_party)  # Update list for future lookups
                                    party_lookup[normalize(fallback_party.party_name)] = fallback_party
                                    abbrev_lookup[normalize(fallback_party.party_abbreviation)] = fallback_party
                                    party_names.append(normalize(fallback_party.party_name))
                                    party_names.append(normalize(fallback_party.party_abbreviation))

                                affiliation = SpeakerPartyAffiliation(
                                    speaker=speaker,
                                    party=fallback_party,
                                    start_date=None,
                                    end_date=None
                                )
                                db.add(affiliation)
                                db.flush()
                                affiliations.append(affiliation)  # Update list for future matching

                                print(f"⚠️ Assigned external fallback affiliation to '{raw_speaker}' on {speech_date}")

                            # If still not found, raise error
                            if not affiliation:
                                raise ValueError(
                                    f"No affiliation for speaker='{raw_speaker}' and party='{annotation}'"
                                )

                            # ✅ Cache this speaker's affiliation for future fallback
                            if speaker and affiliation:
                                speaker_affiliation_cache[norm_speaker] = affiliation

                            # Deduplication
                            existing = db.query(Speech).filter_by(
                                datestamp=speech_date,
                                affiliation_id=affiliation.affiliation_id,
                                speech_content=content_clean
                            ).first()
                            if existing:
                                print(f"⚠️ Skipping duplicate: {raw_speaker} on {speech_date}")
                                continue

                            db.add(Speech(
                                speech_content=content_clean,
                                from_tribune=from_tribune,
                                datestamp=speech_date,
                                is_continuation=is_continuation,
                                processed=False,
                                affiliation=affiliation
                            ))
                            db.flush()

                        except Exception as e:
                            db.rollback()
                            print(f"❌ Error inserting speech on {speech_date}: {e}")
                            traceback.print_exc()
                            sys.exit(1)

        db.commit()
        print("✅ All speeches inserted.")

    except SQLAlchemyError as e:
        db.rollback()
        print("❌ Database error:", e)
        sys.exit(1)
    finally:
        db.close()



def get_infos_from_parliament_db() -> Tuple[
    List[Party],
    List[SpeakerPartyAffiliation],
    Optional[date]
]:
    db = SessionLocal()
    try:
        parties = db.query(Party).all()
        affiliations = db.query(SpeakerPartyAffiliation).options(
            joinedload(SpeakerPartyAffiliation.speaker)
        ).all()
        last_seating_date = db.query(func.max(Speech.datestamp)).scalar()
        return parties, affiliations, last_seating_date
    except SQLAlchemyError as e:
        db.rollback()
        raise e
    finally:
        db.close() 

def get_new_seatings_from_parliament_api(last_seating_date: Optional[date]) -> dict:
    session = requests.Session()
    HEADERS = {
        "User-Agent": "Parliametrics/0.1 (mihail.chifligarov@ruhr-uni-bochum.de)"
    }
    BASE_URL = 'https://www.parliament.bg/api/v1/archive-period/bg/Pl_StenV'  # year/month/0/0

    today = date.today()
    relevant_monthly_seatings = defaultdict(dict)

    if last_seating_date is None:
        print("⚠️ No speeches in DB. Using fallback date: 2025-01-01")
        last_seating_date = date(2025, 1, 1)

    for year in range(last_seating_date.year, today.year + 1):
        start_month = last_seating_date.month if year == last_seating_date.year else 1
        end_month = today.month if year == today.year else 12

        for month in range(start_month, end_month + 1):
            url = f"{BASE_URL}/{year}/{month}/0/0"
            try:
                response = session.get(url, headers=HEADERS)
                response.raise_for_status()
                all_seatings = response.json()
            except (requests.RequestException, ValueError) as e:
                raise RuntimeError(f"❌ Failed to fetch data for {year}-{month:02}: {e}")

            filtered_seatings = sorted(
                (s for s in all_seatings if date.fromisoformat(s['t_date']) > last_seating_date),
                key=lambda s: s["t_date"]
            )
            if filtered_seatings:
                relevant_monthly_seatings[year][month] = filtered_seatings

    return relevant_monthly_seatings
    
if __name__ == "__main__":
    parties = affiliations = last_seating_date = None
    
    try:
        parties, affiliations, last_seating_date = get_infos_from_parliament_db()
    except SQLAlchemyError as e:
        print("❌ Error in fetching data:", e)
        sys.exit(1)
    
    new_seatings = None
    try:
        new_seatings = get_new_seatings_from_parliament_api(last_seating_date)
    except Exception as e:
        print("❌ Error in fetching latest seatings data:", e)
        sys.exit(1)
    
    if new_seatings and parties and affiliations:
        extract_and_insert_speeches_from_api(new_seatings, parties, affiliations)