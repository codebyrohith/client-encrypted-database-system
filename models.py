from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Client(Base):
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    encrypted_name = Column(String(500))
    encrypted_ssn = Column(String(500))
    encrypted_address = Column(String(1000))
    public_key = Column(String(500))
    created_at = Column(DateTime)
    last_accessed = Column(DateTime)