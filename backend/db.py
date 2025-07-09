from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from models import Base
import os

DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(DATABASE_URL, echo=True, future=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# For schema creation
def init_db():
    from models import Party, Speaker, Speech, SpeakerPartyAffiliation  # import all models here
    Base.metadata.create_all(bind=engine)