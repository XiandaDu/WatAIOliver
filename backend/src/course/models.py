from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Course(Base):
    __tablename__ = 't_course'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('t_user.id'))
    name = Column(String(200))
    notes = Column(String(2000))
    doc = Column(String(200))
    model = Column(String(200))
    prompt = Column(String(500))
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow)

    # relationships
    user = relationship("User", back_populates="courses")
    logs = relationship("Log", back_populates="course")