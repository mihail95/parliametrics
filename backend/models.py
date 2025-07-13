from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, Date, UniqueConstraint
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
import datetime

Base = declarative_base()

class Speaker(Base):
    __tablename__ = 'speakers'
    __table_args__ = (
        UniqueConstraint('first_name', 'middle_name', 'last_name', name='uq_full_speaker_name'),
    )

    speaker_id = Column(Integer, primary_key=True)
    speaker_name = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    middle_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)

    affiliations = relationship("SpeakerPartyAffiliation", back_populates="speaker")

    @hybrid_property
    def full_name(self):
        return f"{self.first_name} {self.middle_name} {self.last_name}"

class Party(Base):
    __tablename__ = 'parties'

    party_id = Column(Integer, primary_key=True)
    party_name = Column(String, unique=True)
    party_abbreviation = Column(String)
    party_api_id = Column(String)

    affiliations = relationship("SpeakerPartyAffiliation", back_populates="party")

class SpeakerPartyAffiliation(Base):
    __tablename__ = 'affiliations'
    __table_args__ = (
        UniqueConstraint('speaker_speaker_id', 'party_party_id', name='uq_speaker_party'),
    )

    affiliation_id = Column(Integer, primary_key=True)
    speaker_speaker_id = Column(Integer, ForeignKey("speakers.speaker_id"))
    party_party_id = Column(Integer, ForeignKey("parties.party_id"))
    start_date = Column(Date)
    end_date = Column(Date, nullable=True)

    speaker = relationship("Speaker", back_populates="affiliations")
    party = relationship("Party", back_populates="affiliations")
    speeches = relationship("Speech", back_populates="affiliation")

class Speech(Base):
    __tablename__ = 'speeches'

    speech_id = Column(Integer, primary_key=True)
    speech_content = Column(Text)
    from_tribune = Column(Boolean, default=True)
    datestamp = Column(Date, default=datetime.date.today)
    processed = Column(Boolean, default=False)

    affiliation_id = Column(Integer, ForeignKey("affiliations.affiliation_id"))
    affiliation = relationship("SpeakerPartyAffiliation", back_populates="speeches")
