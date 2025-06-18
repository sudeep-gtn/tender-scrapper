from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, Text

Base = declarative_base()

class Tender(Base):
    __tablename__ = 'tenders'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(Text)
    pub_date = Column(String)
    submission_deadline = Column(String)
    eligibility = Column(Text)
    contact = Column(String)
    link = Column(String)
    source_url = Column(String)
    country = Column(String)
    issuer = Column(String)


engine = create_engine('sqlite:///tenders.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
