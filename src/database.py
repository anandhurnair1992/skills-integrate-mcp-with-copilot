"""
Database configuration and models for the High School Management System.

Uses SQLAlchemy ORM for database management with SQLite by default.
For production, configure PostgreSQL or MySQL connection string in DATABASE_URL.
"""

from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from pathlib import Path

# Database configuration
# Using SQLite by default for simplicity, stored in src/app.db
# For production, set DATABASE_URL environment variable:
# PostgreSQL: postgresql://user:password@localhost/dbname
# MySQL: mysql+pymysql://user:password@localhost/dbname

DATABASE_URL = "sqlite:///./src/app.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Association table for many-to-many relationship between participants and activities
participant_activity = Table(
    "participant_activity",
    Base.metadata,
    Column("participant_id", Integer, ForeignKey("participant.id")),
    Column("activity_id", Integer, ForeignKey("activity.id"))
)


class Activity(Base):
    """Activity model representing an extracurricular activity."""
    
    __tablename__ = "activity"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    schedule = Column(String)
    max_participants = Column(Integer)
    
    # Relationship to participants
    participants = relationship(
        "Participant",
        secondary=participant_activity,
        back_populates="activities"
    )


class Participant(Base):
    """Participant model representing a student."""
    
    __tablename__ = "participant"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    
    # Relationship to activities
    activities = relationship(
        "Activity",
        secondary=participant_activity,
        back_populates="participants"
    )


def get_db():
    """Dependency for getting database session in FastAPI endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize the database with tables."""
    Base.metadata.create_all(bind=engine)
