from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class JobRecord(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True, index=True)
    repo = Column(String)
    status = Column(String)
    priority = Column(Integer, default=1)
    file_size = Column(Integer)
    code_hash = Column(String)

DATABASE_URL = "postgresql://user:password@db:5432/jenkins_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

# ADD THIS LINE at the bottom of database.py
if __name__ == "__main__":
    init_db()