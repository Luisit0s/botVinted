from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, BigInteger
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    vinted_id = Column(BigInteger, unique=True, index=True) 
    title = Column(String)
    price = Column(Float)
    brand = Column(String)
    size = Column(String)
    url = Column(String)
    photo_url = Column(String)
    is_analyzed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    action = Column(String)
    details = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
