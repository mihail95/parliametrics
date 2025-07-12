from pydantic import BaseModel
from datetime import date
from typing import List


class SpeechOut(BaseModel):
    speech_id: int
    speech_content: str
    datestamp: date
    from_tribune: bool
    speaker_name: str
    party_name: str
    party_abbreviation: str

    class Config:
        orm_mode = True


class SpeakerOption(BaseModel):
    id: int
    name: str
    middle_name: str|None

class PartyOption(BaseModel):
    id: int
    name: str
    abbr: str


class FilterOptionsOut(BaseModel):
    speakers: List[SpeakerOption]
    parties: List[PartyOption]
    from_tribune_options: List[bool]
    dates: List[date]
