from sqlalchemy import create_engine, Column, String, Date, DateTime, Integer, ForeignKey, func, desc
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

DATABASE_URL = "sqlite:///users.db"  # Make sure this is the correct path to your SQLite database

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    phone_number = Column(String, unique=True, index=True)
    name = Column(String, index=True)
    date_of_birth = Column(Date)
    email = Column(String, unique=True, index=True)
    is_verified = Column(Integer, default=0)
    otps = relationship("OTPDB", back_populates="user")
    scores = relationship("ScoreDB", back_populates="user")


class OTPDB(Base):
    __tablename__ = "otps"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    phone_number = Column(String, index=True)
    otp = Column(String(6))
    expiry = Column(DateTime)
    user = relationship("UserDB", back_populates="otps")


class ScoreDB(Base):
    __tablename__ = "scores"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    score = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user = relationship("UserDB", back_populates="scores")


def create_tables():
    Base.metadata.create_all(bind=engine)

