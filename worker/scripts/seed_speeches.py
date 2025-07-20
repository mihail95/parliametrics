from models import Speaker, SpeakerPartyAffiliation, Party, Speech
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from db import SessionLocal
from rapidfuzz import process, fuzz
from typing import List, Tuple, Optional
from datetime import datetime
from datetime import date
from collections import defaultdict
from collections import deque
import requests
import re
import sys
import unicodedata
import traceback
import time

class SlidingAffiliationCache:
    def __init__(self, max_age=4):
        self._store = {}
        self._history = deque(maxlen=max_age)

    def add(self, norm_speaker, affiliation):
        self._store[norm_speaker] = affiliation
        self._history.append(norm_speaker)
        # Retain only recent speakers
        recent = set(self._history)
        self._store = {k: v for k, v in self._store.items() if k in recent}

    def get(self, norm_speaker):
        return self._store.get(norm_speaker)

    def __contains__(self, norm_speaker):
        return norm_speaker in self._store
    
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

        speaker_affiliation_cache = SlidingAffiliationCache(max_age=4)

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
                        steno_text, re.M
                    )

                    last_successful_speech = None
                    for raw_speaker, annotation, content, *_ in speeches:
                        try:
                            content_clean = re.sub(r"<br\s*/?>", "\n", content, flags=re.IGNORECASE)
                            content_clean = re.sub(r"\n+", "\n", content_clean).strip()

                            if is_likely_not_speaker(raw_speaker):
                                print(f"⚠️ Skipping invalid speaker line: {raw_speaker}")
                                if last_successful_speech:
                                    last_successful_speech.speech_content += "\n" + content_clean
                                    db.flush()
                                continue

                            norm_speaker = normalize(raw_speaker)
                            from_tribune = not annotation or "от място" not in annotation
                            is_continuation = False
                            speaker = None
                            affiliation = None

                            # --- Party resolution ---
                            party = None
                            if annotation:
                                match = re.search(r"^\(([^(),]+)", annotation)
                                if match:
                                    raw_party = normalize(match.group(1))
                                    party = party_lookup.get(raw_party) or abbrev_lookup.get(raw_party)

                                    if not party:
                                        fuzzy = fuzzy_match(raw_party, party_names)
                                        if fuzzy:
                                            party = party_lookup.get(fuzzy) or abbrev_lookup.get(fuzzy)
                                        if not party:
                                            best = max(party_names, key=lambda n: fuzz.partial_ratio(raw_party, n), default=None)
                                            if best and fuzz.partial_ratio(raw_party, best) >= 80:
                                                party = party_lookup.get(best) or abbrev_lookup.get(best)

                            # --- Speaker resolution ---
                            candidates = speaker_lookup.get(norm_speaker)
                            if not candidates:
                                match = fuzzy_match(norm_speaker, speaker_names)
                                candidates = speaker_lookup.get(match) if match else None

                            if candidates:
                                if len(candidates) == 1:
                                    speaker = candidates[0][0]
                                elif party:
                                    exact = [c for c in candidates if c[1] == party.party_id and (c[2] is None or c[2] <= speech_date) and (c[3] is None or speech_date <= c[3])]
                                    if len(exact) == 1:
                                        speaker = exact[0][0]
                                    else:
                                        valid = [c for c in candidates if (c[2] is None or c[2] <= speech_date) and (c[3] is None or speech_date <= c[3])]
                                        if len(valid) == 1:
                                            speaker = valid[0][0]
                                        else:
                                            speaker = sorted(candidates, key=lambda c: c[2] or date.min, reverse=True)[0][0]

                            # --- Affiliation logic ---
                            if not annotation and norm_speaker in speaker_affiliation_cache:
                                affiliation = speaker_affiliation_cache.get(norm_speaker)
                                is_continuation = True

                            if not affiliation and speaker and party:
                                affiliation = next((a for a in affiliations if a.speaker_speaker_id == speaker.speaker_id and a.party_party_id == party.party_id), None)

                            if not affiliation:
                                special_roles = [
                                    ("председател", 1, 1),
                                    ("министър", 2, 2),
                                    ("докладчик", 3, 3),
                                ]
                                for keyword, sid, pid in special_roles:
                                    if fuzz.partial_ratio(keyword, norm_speaker) >= 85:
                                        affiliation = next((a for a in affiliations if a.speaker_speaker_id == sid and a.party_party_id == pid), None)
                                        if affiliation:
                                            break

                            if not affiliation and speaker:
                                affs = [a for a in affiliations if a.speaker_speaker_id == speaker.speaker_id]
                                if affs:
                                    affiliation = sorted(affs, key=lambda a: a.start_date or date.min, reverse=True)[0]

                            if not affiliation:
                                normalized_name = raw_speaker.strip().title()
                                speaker = db.query(Speaker).filter_by(speaker_name=normalized_name).first()
                                speaker = db.query(Speaker).filter_by(speaker_name=normalized_name).first()
                                if not speaker:
                                    speaker = Speaker(
                                        speaker_name=normalized_name,
                                        first_name="", middle_name="", last_name=""
                                    )
                                speaker = db.merge(speaker)  # ✅ This ensures it's safely attached
                                db.flush()

                                fallback_party = next((p for p in parties if p.party_id == 9999), None)
                                if not fallback_party:
                                    fallback_party = Party(party_id=9999, party_name="ВЪНШЕН", party_abbreviation="")
                                    db.add(fallback_party)
                                    db.flush()
                                    parties.append(fallback_party)
                                    party_lookup[normalize(fallback_party.party_name)] = fallback_party
                                    abbrev_lookup[normalize(fallback_party.party_abbreviation)] = fallback_party
                                    party_names += [normalize(fallback_party.party_name), normalize(fallback_party.party_abbreviation)]

                                affiliation = db.query(SpeakerPartyAffiliation).filter_by(
                                    speaker_speaker_id=speaker.speaker_id,
                                    party_party_id=fallback_party.party_id
                                ).first()
                                if not affiliation:
                                    speaker = db.merge(speaker)
                                    fallback_party = db.merge(fallback_party)
                                    affiliation = SpeakerPartyAffiliation(
                                        speaker=speaker, party=fallback_party, start_date=None, end_date=None
                                    )
                                    db.add(affiliation)
                                    db.flush()
                                    affiliations.append(affiliation)

                            if not affiliation:
                                raise ValueError(f"No affiliation found for '{raw_speaker}' on {speech_date}")

                            speaker_affiliation_cache.add(norm_speaker, affiliation)

                            existing = db.query(Speech).filter_by(
                                datestamp=speech_date,
                                affiliation_id=affiliation.affiliation_id,
                                speech_content=content_clean
                            ).first()
                            if existing:
                                continue
                            
                            affiliation = db.merge(affiliation)
                            new_speech = Speech(
                                speech_content=content_clean,
                                from_tribune=from_tribune,
                                datestamp=speech_date,
                                is_continuation=is_continuation,
                                processed=False,
                                affiliation=affiliation
                            )
                            db.add(new_speech)
                            db.flush()
                            last_successful_speech = new_speech

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