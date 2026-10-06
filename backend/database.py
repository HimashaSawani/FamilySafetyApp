"""
Persistent SQLite Database Models and Engine for AegisSafe
"""
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Float, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "familysafety.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Security and default settings loaded from environment variables
DEFAULT_SECURITY_PIN = os.getenv("DEFAULT_SECURITY_PIN", "0000")
DEFAULT_CIRCLE_CODE = os.getenv("DEFAULT_CIRCLE_CODE", "DEMO99")
DEFAULT_CIRCLE_ID = os.getenv("DEFAULT_CIRCLE_ID", "CIRCLE-001")
DEFAULT_CIRCLE_NAME = os.getenv("DEFAULT_CIRCLE_NAME", "Demo Family Circle")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Circle(Base):
    __tablename__ = "circles"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    members = relationship("User", back_populates="circle")
    geofences = relationship("Geofence", back_populates="circle")

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    role = Column(String, default="MEMBER") # GUARDIAN, CHILD, SENIOR, MEMBER
    phone = Column(String, nullable=False)
    circle_id = Column(String, ForeignKey("circles.id"))
    avatar_url = Column(String, default="")
    avatar_emoji = Column(String, default="👤")
    color = Column(String, default="#3B82F6")
    battery = Column(Integer, default=100)
    is_charging = Column(Boolean, default=False)
    status_text = Column(String, default="At home")
    last_seen = Column(DateTime, default=datetime.utcnow)
    security_pin = Column(String, default=DEFAULT_SECURITY_PIN) # Server-side verified emergency PIN

    # Latest location coordinates (Generic Demo Coordinates)
    lat = Column(Float, default=37.7749)
    lng = Column(Float, default=-122.4194)
    location_name = Column(String, default="Demo Metro Area")
    accuracy = Column(Float, default=4.0)
    speed = Column(Float, default=0.0)

    circle = relationship("Circle", back_populates="members")
    sos_alerts = relationship("SOSAlert", back_populates="user")

class Geofence(Base):
    __tablename__ = "geofences"
    id = Column(String, primary_key=True, index=True)
    circle_id = Column(String, ForeignKey("circles.id"))
    name = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    radius = Column(Float, default=250.0) # meters
    zone_type = Column(String, default="SAFE") # SAFE or DANGER
    notify_on_entry = Column(Boolean, default=True)
    notify_on_exit = Column(Boolean, default=True)

    circle = relationship("Circle", back_populates="geofences")

class SOSAlert(Base):
    __tablename__ = "sos_alerts"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    circle_id = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    location_name = Column(String, default="Demo Metro Area")
    battery = Column(Integer, default=100)
    reason = Column(String, default="MANUAL_PANIC_BUTTON")
    status = Column(String, default="ACTIVE") # ACTIVE, RESOLVED
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String, nullable=True)
    resolution_notes = Column(Text, nullable=True)

    user = relationship("User", back_populates="sos_alerts")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    category = Column(String, default="SYSTEM")
    message = Column(String, nullable=False)
    level = Column(String, default="INFO") # INFO, WARN, CRITICAL

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Check if default circle exists; if not, seed generic mock demo data
    if not db.query(Circle).filter_by(id=DEFAULT_CIRCLE_ID).first():
        circle = Circle(
            id=DEFAULT_CIRCLE_ID,
            name=DEFAULT_CIRCLE_NAME,
            code=DEFAULT_CIRCLE_CODE
        )
        db.add(circle)
        db.commit()

        # Seed generic mock members using standard 555-fictitious phone numbers
        users = [
            User(
                id="usr_sarah",
                name="Alex (Guardian)",
                role="Guardian",
                phone="+1 555-0101",
                circle_id=DEFAULT_CIRCLE_ID,
                avatar_emoji="👩‍💼",
                avatar_url="https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150",
                color="#3B82F6",
                battery=88,
                is_charging=False,
                status_text="At home • Last updated just now",
                security_pin=DEFAULT_SECURITY_PIN,
                lat=37.7749,
                lng=-122.4194,
                location_name="Downtown Safe Zone"
            ),
            User(
                id="usr_leo",
                name="Jordan (Member)",
                role="Family",
                phone="+1 555-0102",
                circle_id=DEFAULT_CIRCLE_ID,
                avatar_emoji="👦",
                avatar_url="https://images.unsplash.com/photo-1543610892-0b1f7e6d8ac1?w=150",
                color="#10B981",
                battery=42,
                is_charging=False,
                status_text="On the move • Last updated 2 min ago",
                security_pin=DEFAULT_SECURITY_PIN,
                lat=37.7833,
                lng=-122.4167,
                location_name="North District Hub"
            ),
            User(
                id="usr_grandpa",
                name="Sam (Senior)",
                role="Senior",
                phone="+1 555-0103",
                circle_id=DEFAULT_CIRCLE_ID,
                avatar_emoji="👴",
                avatar_url="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150",
                color="#F59E0B",
                battery=65,
                is_charging=False,
                status_text="At home • Last updated just now",
                security_pin=DEFAULT_SECURITY_PIN,
                lat=37.7690,
                lng=-122.4467,
                location_name="Westside Residential Zone"
            )
        ]
        for u in users:
            db.add(u)

        # Seed Generic Geofences
        geofences = [
            Geofence(
                id="geo_home",
                circle_id=DEFAULT_CIRCLE_ID,
                name="Home safe zone",
                lat=37.7690,
                lng=-122.4467,
                radius=300.0,
                zone_type="SAFE"
            ),
            Geofence(
                id="geo_school",
                circle_id=DEFAULT_CIRCLE_ID,
                name="Central Transit Safe Zone",
                lat=37.7749,
                lng=-122.4194,
                radius=400.0,
                zone_type="SAFE"
            )
        ]
        for g in geofences:
            db.add(g)

        db.add(AuditLog(
            category="SYSTEM",
            message="Database initialized with demo configuration.",
            level="INFO"
        ))
        db.commit()
    db.close()

