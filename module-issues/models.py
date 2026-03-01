from sqlalchemy import Column, Integer, String
from db import Base

class Issue(Base):
    __tablename__ = "issues"
    id = Column(Integer, primary_key=True, index=True)
    task = Column(String, index=True)
    status = Column(String, default="Nowy")
