from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from db import get_db
from models import Speech, Speaker, Party, SpeakerPartyAffiliation
from schemas import SpeechOut, FilterOptionsOut

router = APIRouter()

@router.get("/speeches", response_model=List[SpeechOut])
def get_speeches(
    db: Session = Depends(get_db),
    speaker_ids: Optional[List[int]] = Query(None),
    party_ids: Optional[List[int]] = Query(None),
    from_tribune: Optional[bool] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    skip: int = 0,
    limit: int = 20
):
    query = db.query(
        Speech.speech_id,
        Speech.speech_content,
        Speech.datestamp,
        Speech.from_tribune,
        Speaker.speaker_name,
        Party.party_name,
        Party.party_abbreviation
    ).join(SpeakerPartyAffiliation, Speech.affiliation_id == SpeakerPartyAffiliation.affiliation_id
    ).join(Speaker, SpeakerPartyAffiliation.speaker_speaker_id == Speaker.speaker_id
    ).join(Party, SpeakerPartyAffiliation.party_party_id == Party.party_id)

    if speaker_ids:
        query = query.filter(Speaker.speaker_id.in_(speaker_ids))
    if party_ids:
        query = query.filter(Party.party_id.in_(party_ids))
    if from_tribune is not None:
        query = query.filter(Speech.from_tribune == from_tribune)
    if date_from:
        query = query.filter(Speech.datestamp >= date_from)
    if date_to:
        query = query.filter(Speech.datestamp <= date_to)

    return query.order_by(Speech.datestamp.desc()).offset(skip).limit(limit).all()


@router.get("/speeches/filters", response_model=FilterOptionsOut)
def get_filter_options(db: Session = Depends(get_db)):
    speakers = db.query(Speaker.speaker_id, Speaker.speaker_name, Speaker.middle_name).order_by(Speaker.speaker_name).distinct().all()
    parties = db.query(Party.party_id, Party.party_name, Party.party_abbreviation).order_by(Party.party_name).all()
    dates = db.query(Speech.datestamp).order_by(Speech.datestamp).distinct().all()

    return {
        "speakers": [{"id": s.speaker_id, "name": s.speaker_name, "middle_name": getattr(s, "middle_name", None)} for s in speakers],
        "parties": [{"id": p.party_id, "name": p.party_name, "abbr": p.party_abbreviation} for p in parties],
        "from_tribune_options": [True, False],
        "dates": [d.datestamp for d in dates]
    }
