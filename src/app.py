"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.

This version uses SQLAlchemy ORM for persistent database storage.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
from pathlib import Path
from sqlalchemy.orm import Session
from database import Activity, Participant, get_db, init_db, SessionLocal
from seed_db import seed_database

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=current_dir / "static"), name="static")


@app.on_event("startup")
def startup_event():
    """Initialize database and seed with sample data on startup."""
    init_db()
    # Check if database is empty and seed if needed
    db = SessionLocal()
    try:
        if db.query(Activity).count() == 0:
            seed_database()
    finally:
        db.close()


class SignupRequest(BaseModel):
    email: EmailStr


class ActivityResponse(BaseModel):
    name: str
    description: str
    schedule: str
    max_participants: int
    participants: list[str]

    class Config:
        from_attributes = True


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities(db: Session = Depends(get_db)):
    """Get all activities with their participants."""
    activities = db.query(Activity).all()
    result = {}
    
    for activity in activities:
        result[activity.name] = {
            "description": activity.description,
            "schedule": activity.schedule,
            "max_participants": activity.max_participants,
            "participants": [p.email for p in activity.participants]
        }
    
    return result


@app.post("/activities/{activity_name}/signup", status_code=201)
def signup_for_activity(activity_name: str, request: SignupRequest, db: Session = Depends(get_db)):
    """Sign up a student for an activity"""
    # Validate activity exists
    activity = db.query(Activity).filter(Activity.name == activity_name).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Validate student is not already signed up
    participant = db.query(Participant).filter(Participant.email == request.email).first()
    if participant and activity in participant.activities:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Create participant if doesn't exist
    if not participant:
        participant = Participant(email=request.email)
        db.add(participant)
        db.flush()
    
    # Add student to activity
    if activity not in participant.activities:
        participant.activities.append(activity)
    
    db.commit()
    return {"message": f"Signed up {request.email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, request: SignupRequest, db: Session = Depends(get_db)):
    """Unregister a student from an activity"""
    # Validate activity exists
    activity = db.query(Activity).filter(Activity.name == activity_name).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Validate student is signed up
    participant = db.query(Participant).filter(Participant.email == request.email).first()
    if not participant or activity not in participant.activities:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student from activity
    participant.activities.remove(activity)
    db.commit()
    return {"message": f"Unregistered {request.email} from {activity_name}"}
