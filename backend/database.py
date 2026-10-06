"""
Persistent SQLite Database Models and Engine for AegisSafe
"""
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Float, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "familysafety.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

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
    security_pin = Column(String, default="1234") # Server-side verified emergency PIN

    # Latest location coordinates
    lat = Column(Float, default=6.9271)
    lng = Column(Float, default=79.8612)
    location_name = Column(String, default="Colombo, Sri Lanka")
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
    location_name = Column(String, default="Colombo, Sri Lanka")
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
    
    # Check if circle exists; if not, seed default data
    if not db.query(Circle).filter_by(id="FAM-9021").first():
        circle = Circle(
            id="FAM-9021",
            name="My Family",
            code="SAFE99"
        )
        db.add(circle)
        db.commit()

        # Seed 3 realistic members matching the design (Colombo locations)
        users = [
            User(
                id="usr_sarah",
                name="Sarah",
                role="Guardian",
                phone="+94 77 123 4567",
                circle_id="FAM-9021",
                avatar_emoji="👩‍💼",
                avatar_url="https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150",
                color="#3B82F6",
                battery=88,
                is_charging=False,
                status_text="At home • Last updated just now",
                security_pin="1234",
                lat=6.9360,
                lng=79.8450,
                location_name="Colombo Fort, Sri Lanka"
            ),
            User(
                id="usr_leo",
                name="Leo",
                role="Family",
                phone="+94 71 987 6543",
                circle_id="FAM-9021",
                avatar_emoji="👦",
                avatar_url="https://images.unsplash.com/photo-1543610892-0b1f7e6d8ac1?w=150",
                color="#10B981",
                battery=42,
                is_charging=False,
                status_text="On the move • Last updated 2 min ago",
                security_pin="1234",
                lat=6.9200,
                lng=79.8700,
                location_name="Cinnamon Gardens, Colombo"
            ),
            User(
                id="usr_grandpa",
                name="Grandpa Joe",
                role="Senior",
                phone="+94 70 555 0192",
                circle_id="FAM-9021",
                avatar_emoji="👴",
                avatar_url="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150",
                color="#F59E0B",
                battery=65,
                is_charging=False,
                status_text="At home • Last updated just now",
                security_pin="1234",
                lat=6.8950,
                lng=79.8560,
                location_name="Bambalapitiya, Colombo"
            )
        ]
        for u in users:
            db.add(u)

        # Seed Geofences
        geofences = [
            Geofence(
                id="geo_home",
                circle_id="FAM-9021",
                name="Home safe zone",
                lat=6.8950,
                lng=79.8560,
                radius=300.0,
                zone_type="SAFE"
            ),
            Geofence(
                id="geo_school",
                circle_id="FAM-9021",
                name="Colombo Fort Station Zone",
                lat=6.9360,
                lng=79.8450,
                radius=400.0,
                zone_type="SAFE"
            )
        ]
        for g in geofences:
            db.add(g)

        db.add(AuditLog(
            category="SYSTEM",
            message="Database initialized with persistent SQLite store.",
            level="INFO"
        ))
        db.commit()
    db.close()
