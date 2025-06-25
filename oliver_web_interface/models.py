# models.py

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = 't_user'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(200), unique=True, index=True)
    password = Column(String(200))
    nickname = Column(String(200))
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow)

    # 关系
    courses = relationship("Course", back_populates="user")
    logs = relationship("Log", back_populates="user")

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

    # 关系
    user = relationship("User", back_populates="courses")
    logs = relationship("Log", back_populates="course")

class Log(Base):
    __tablename__ = 't_log'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('t_user.id'), nullable=True)
    course_id = Column(Integer, ForeignKey('t_course.id'), nullable=True)
    query = Column(Text)
    answer = Column(Text)  # 存储助手的回答
    background = Column(Text)
    llm = Column(Text)
    link = Column(String)
    create_time = Column(DateTime, default=datetime.utcnow)

    # 关系
    user = relationship("User", back_populates="logs")
    course = relationship("Course", back_populates="logs")
