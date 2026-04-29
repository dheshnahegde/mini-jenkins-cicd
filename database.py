
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
Base = declarative_base()
class JobRecord(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True, index=True)
    repo = Column(String)
    language = Column(String)
    status = Column(String)
    # NEW COLUMNS
    priority = Column(Integer, default=1) # 1, 2, or 3
    file_size = Column(Integer)            # Size in KB
    code_hash = Column(String)            # Unique fingerprint

    # Add this at the very bottom of database.py
DATABASE_URL = "postgresql://user:password@db:5432/jenkins_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)