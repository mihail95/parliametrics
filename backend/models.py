from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship, declarative_base
import datetime

Base = declarative_base()

class Speaker(Base):
    __tablename__ = 'speakers'

    id = Column(Integer, primary_key=True)
    name = Column(String)

    affiliations = relationship("SpeakerPartyAffiliation", back_populates="speaker")
    speeches = relationship("Speech", back_populates="speaker")

class Party(Base):
    __tablename__ = 'parties'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    abbreviation = Column(String)

    affiliations = relationship("SpeakerPartyAffiliation", back_populates="party")

class SpeakerPartyAffiliation(Base):
    __tablename__ = 'affiliations'
    __table_args__ = (
        UniqueConstraint('speaker_id', 'party_id', name='uq_speaker_party'),
    )

    id = Column(Integer, primary_key=True)
    speaker_id = Column(Integer, ForeignKey("speakers.id"))
    party_id = Column(Integer, ForeignKey("parties.id"))
    start_date = Column(DateTime)
    end_date = Column(DateTime, nullable=True)

    speaker = relationship("Speaker", back_populates="affiliations")
    party = relationship("Party", back_populates="affiliations")
    speeches = relationship("Speech", back_populates="affiliation")

class Speech(Base):
    __tablename__ = 'speeches'

    id = Column(Integer, primary_key=True)
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    speaker_id = Column(Integer, ForeignKey("speakers.id"))
    affiliation_id = Column(Integer, ForeignKey("affiliations.id"))

    speaker = relationship("Speaker", back_populates="speeches")
    affiliation = relationship("SpeakerPartyAffiliation", back_populates="speeches")
