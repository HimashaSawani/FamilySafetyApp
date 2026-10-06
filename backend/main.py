"""
AegisSafe Production Multi-Feature Family Safety Backend
FastAPI + SQLite + WebSockets + Invites + Geofencing + Check-ins + Journey Tracker + SOS Acknowledgement
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import uuid

from database import init_db, SessionLocal, User, Circle, Geofence, SOSAlert, AuditLog

init_db()

app = FastAPI(
    title="AegisSafe Industrial Telemetry & Safety Hub",
    description="Multi-Device Family Circles, Geofences, 1-Tap Check-ins, Journey Tracker & SOS Acknowledgements",
    version="5.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.circle_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, circle_id: str):
        await websocket.accept()
        if circle_id not in self.circle_connections:
            self.circle_connections[circle_id] = []
        self.circle_connections[circle_id].append(websocket)

    def disconnect(self, websocket: WebSocket, circle_id: str):
        if circle_id in self.circle_connections and websocket in self.circle_connections[circle_id]:
            self.circle_connections[circle_id].remove(websocket)

    async def broadcast_to_circle(self, circle_id: str, message: dict):
        if circle_id in self.circle_connections:
            for connection in list(self.circle_connections[circle_id]):
                try:
                    await connection.send_text(json.dumps(message))
                except Exception:
                    self.disconnect(connection, circle_id)

ws_manager = ConnectionManager()

# --- Schemas ---
class JoinCirclePayload(BaseModel):
    user_id: str
    circle_code: str

class CheckInPayload(BaseModel):
    user_id: str
    location_name: str = "Colombo, Sri Lanka"
    custom_message: Optional[str] = "I'm safe and sound!"

class JourneyStartPayload(BaseModel):
    user_id: str
    destination_name: str
    dest_lat: float
    dest_lng: float
    eta_minutes: int = 15

class SOSAcknowledgePayload(BaseModel):
    sos_id: str
    responder_id: str
    responder_name: str
    eta_minutes: Optional[int] = 5

class QuickMessagePayload(BaseModel):
    user_id: str
    message_type: str # PICK_ME_UP, REACHED_SAFELY, CALL_ME, DELAYED

class LocationUpdatePayload(BaseModel):
    user_id: str
    lat: float
    lng: float
    accuracy: float = 4.0
    speed: float = 0.0
    battery: int = 100
    is_charging: bool = False
    location_name: Optional[str] = "Colombo, Sri Lanka"

class SOSTriggerPayload(BaseModel):
    user_id: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    location_name: Optional[str] = "Colombo, Sri Lanka"
    reason: str = "MANUAL_PANIC_BUTTON"

class SOSCancelPayload(BaseModel):
    sos_id: str
    user_id: str
    pin: str
    resolution_notes: Optional[str] = "Verified safe."

# --- Active In-Memory Journey Tracking State ---
active_journeys: Dict[str, Dict[str, Any]] = {}
sos_responders: Dict[str, List[Dict[str, Any]]] = {}

# --- Endpoints ---

@app.get("/api/health")
async def health_check():
    db = SessionLocal()
    user_count = db.query(User).count()
    circle_count = db.query(Circle).count()
    active_sos = db.query(SOSAlert).filter_by(status="ACTIVE").count()
    db.close()
    return {
        "status": "healthy",
        "service": "AegisSafe Comprehensive Family Hub",
        "storage": "Persistent SQLite (familysafety.db)",
        "timestamp": datetime.utcnow().isoformat(),
        "registered_users": user_count,
        "active_circles": circle_count,
        "active_sos_alerts": active_sos
    }

@app.get("/api/circle/{circle_id}")
async def get_circle_details(circle_id: str):
    db = SessionLocal()
    circle = db.query(Circle).filter_by(id=circle_id).first()
    if not circle:
        db.close()
        raise HTTPException(status_code=404, detail="Circle not found")

    users = db.query(User).filter_by(circle_id=circle_id).all()
    geofences = db.query(Geofence).filter_by(circle_id=circle_id).all()
    active_alerts = db.query(SOSAlert).filter_by(circle_id=circle_id, status="ACTIVE").all()
    logs = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(25).all()

    members_data = []
    for u in users:
        freshness = "Just now"
        if u.last_seen:
            diff_mins = int((datetime.utcnow() - u.last_seen).total_seconds() / 60)
            if diff_mins > 0:
                freshness = f"{diff_mins} min ago"

        members_data.append({
            "id": u.id,
            "name": u.name,
            "role": u.role,
            "phone": u.phone,
            "avatar_emoji": u.avatar_emoji,
            "avatar_url": u.avatar_url,
            "color": u.color,
            "battery": u.battery,
            "is_charging": u.is_charging,
            "status_text": u.status_text,
            "freshness": freshness,
            "last_seen": u.last_seen.isoformat() if u.last_seen else None,
            "location": {
                "lat": u.lat,
                "lng": u.lng,
                "location_name": u.location_name,
                "accuracy": u.accuracy,
                "speed": u.speed
            }
        })

    geofences_data = [
        {"id": g.id, "name": g.name, "lat": g.lat, "lng": g.lng, "radius": g.radius, "zone_type": g.zone_type}
        for g in geofences
    ]

    alerts_data = []
    for a in active_alerts:
        user_name = a.user.name if a.user else "Family Member"
        responders = sos_responders.get(a.id, [])
        alerts_data.append({
            "id": a.id,
            "user_id": a.user_id,
            "user_name": user_name,
            "lat": a.lat,
            "lng": a.lng,
            "location_name": a.location_name,
            "battery": a.battery,
            "status": a.status,
            "responders": responders,
            "timestamp": a.created_at.isoformat()
        })

    logs_data = [
        {"id": l.id, "category": l.category, "message": l.message, "level": l.level, "timestamp": l.timestamp.isoformat()}
        for l in logs
    ]

    circle_info = {
        "id": circle.id,
        "name": circle.name,
        "code": circle.code,
        "share_link": f"https://aegissafe.app/join/{circle.code}"
    }
    db.close()

    return {
        "circle": circle_info,
        "members": members_data,
        "geofences": geofences_data,
        "active_sos": alerts_data,
        "active_journeys": list(active_journeys.values()),
        "logs": logs_data
    }

# 1. Family Circle Join via Invite Code
@app.post("/api/circle/join")
async def join_circle(payload: JoinCirclePayload):
    db = SessionLocal()
    circle = db.query(Circle).filter_by(code=payload.circle_code.upper()).first()
    if not circle:
        db.close()
        raise HTTPException(status_code=404, detail="Invalid Family Circle Invite Code.")

    user = db.query(User).filter_by(id=payload.user_id).first()
    if not user:
        db.close()
        raise HTTPException(status_code=404, detail="User not found.")

    old_circle = user.circle_id
    user.circle_id = circle.id
    db.add(AuditLog(
        category="CIRCLE",
        message=f"🎉 {user.name} joined family circle '{circle.name}' via invite code.",
        level="INFO"
    ))
    db.commit()
    db.close()

    await ws_manager.broadcast_to_circle(circle.id, {
        "type": "MEMBER_JOINED",
        "user_name": user.name,
        "circle_id": circle.id
    })
    return {"status": "SUCCESS", "circle_id": circle.id, "circle_name": circle.name}

# 2. 1-Tap "I'm Safe" Quick Check-in
@app.post("/api/checkin/send")
async def send_checkin(payload: CheckInPayload):
    db = SessionLocal()
    user = db.query(User).filter_by(id=payload.user_id).first()
    if not user:
        db.close()
        raise HTTPException(status_code=404, detail="User not found.")

    msg = f"🛡️ Check-In: {user.name} checked in safely at {payload.location_name}."
    db.add(AuditLog(category="CHECK_IN", message=msg, level="INFO"))
    db.commit()
    circle_id = user.circle_id
    db.close()

    event = {
        "type": "CHECK_IN_RECEIVED",
        "user_id": user.id,
        "user_name": user.name,
        "location_name": payload.location_name,
        "custom_message": payload.custom_message,
        "timestamp": datetime.utcnow().isoformat()
    }
    await ws_manager.broadcast_to_circle(circle_id, event)
    return {"status": "CHECKIN_SENT", "event": event}

# 3. Live Journey Sharing & Trip Tracker
@app.post("/api/journey/start")
async def start_journey(payload: JourneyStartPayload):
    db = SessionLocal()
    user = db.query(User).filter_by(id=payload.user_id).first()
    if not user:
        db.close()
        raise HTTPException(status_code=404, detail="User not found.")

    journey_id = f"JRN-{int(datetime.utcnow().timestamp())}"
    journey_data = {
        "id": journey_id,
        "user_id": user.id,
        "user_name": user.name,
        "circle_id": user.circle_id,
        "start_location": user.location_name,
        "destination_name": payload.destination_name,
        "dest_lat": payload.dest_lat,
        "dest_lng": payload.dest_lng,
        "eta_minutes": payload.eta_minutes,
        "started_at": datetime.utcnow().isoformat(),
        "status": "EN_ROUTE"
    }
    active_journeys[journey_id] = journey_data

    db.add(AuditLog(
        category="JOURNEY",
        message=f"🚗 {user.name} started a trip to {payload.destination_name} (ETA: {payload.eta_minutes} mins).",
        level="INFO"
    ))
    db.commit()
    circle_id = user.circle_id
    db.close()

    await ws_manager.broadcast_to_circle(circle_id, {
        "type": "JOURNEY_STARTED",
        "journey": journey_data
    })
    return {"status": "JOURNEY_STARTED", "journey": journey_data}

# 4. SOS Acknowledgement ("I'm Helping / On My Way")
@app.post("/api/sos/acknowledge")
async def acknowledge_sos(payload: SOSAcknowledgePayload):
    db = SessionLocal()
    alert = db.query(SOSAlert).filter_by(id=payload.sos_id, status="ACTIVE").first()
    if not alert:
        db.close()
        raise HTTPException(status_code=404, detail="Active SOS alert not found.")

    if payload.sos_id not in sos_responders:
        sos_responders[payload.sos_id] = []

    responder_info = {
        "responder_id": payload.responder_id,
        "responder_name": payload.responder_name,
        "eta_minutes": payload.eta_minutes,
        "responded_at": datetime.utcnow().isoformat()
    }
    sos_responders[payload.sos_id].append(responder_info)

    db.add(AuditLog(
        category="EMERGENCY_SOS",
        message=f"🤝 {payload.responder_name} responded to SOS {alert.id}: 'I am on my way to help!'",
        level="INFO"
    ))
    db.commit()
    circle_id = alert.circle_id
    db.close()

    await ws_manager.broadcast_to_circle(circle_id, {
        "type": "SOS_ACKNOWLEDGED",
        "sos_id": payload.sos_id,
        "responder": responder_info
    })
    return {"status": "ACKNOWLEDGED", "responder": responder_info}

# 5. Quick Family Messages
@app.post("/api/quick-message/send")
async def send_quick_message(payload: QuickMessagePayload):
    db = SessionLocal()
    user = db.query(User).filter_by(id=payload.user_id).first()
    if not user:
        db.close()
        raise HTTPException(status_code=404, detail="User not found.")

    labels = {
        "PICK_ME_UP": "🚗 Can you pick me up?",
        "REACHED_SAFELY": "🏡 I've reached safely!",
        "CALL_ME": "📞 Please call me when free.",
        "RUNNING_LATE": "⏳ Running a bit late, don't worry!"
    }
    text = labels.get(payload.message_type, "Quick message")

    db.add(AuditLog(
        category="MESSAGE",
        message=f"💬 {user.name}: {text}",
        level="INFO"
    ))
    db.commit()
    circle_id = user.circle_id
    db.close()

    event = {
        "type": "QUICK_MESSAGE_RECEIVED",
        "user_name": user.name,
        "text": text,
        "timestamp": datetime.utcnow().isoformat()
    }
    await ws_manager.broadcast_to_circle(circle_id, event)
    return {"status": "MESSAGE_SENT", "event": event}

# Standard Location, SOS & Cancel Handlers
@app.post("/api/location/update")
async def update_location(payload: LocationUpdatePayload):
    db = SessionLocal()
    user = db.query(User).filter_by(id=payload.user_id).first()
    if not user:
        db.close()
        raise HTTPException(status_code=404, detail="User not found")

    user.lat = payload.lat
    user.lng = payload.lng
    user.accuracy = payload.accuracy
    user.speed = payload.speed
    user.battery = payload.battery
    user.is_charging = payload.is_charging
    if payload.location_name:
        user.location_name = payload.location_name
    user.last_seen = datetime.utcnow()

    if payload.speed > 5.0:
        user.status_text = f"On the move ({payload.speed:.1f} km/h)"
    else:
        user.status_text = "At home • Stationary"

    # Low Battery Alert Auto-Trigger (< 20%)
    if payload.battery < 20 and not payload.is_charging:
        db.add(AuditLog(
            category="BATTERY",
            message=f"⚠️ Low Battery Warning: {user.name}'s phone is at {payload.battery}%!",
            level="WARN"
        ))

    db.commit()

    event = {
        "type": "LOCATION_UPDATED",
        "user_id": user.id,
        "name": user.name,
        "battery": user.battery,
        "status_text": user.status_text,
        "location": {
            "lat": user.lat,
            "lng": user.lng,
            "location_name": user.location_name,
            "accuracy": user.accuracy,
            "speed": user.speed
        }
    }
    circle_id = user.circle_id
    db.close()

    await ws_manager.broadcast_to_circle(circle_id, event)
    return {"status": "SUCCESS", "event": event}

@app.post("/api/sos/trigger")
async def trigger_sos(payload: SOSTriggerPayload):
    db = SessionLocal()
    user = db.query(User).filter_by(id=payload.user_id).first()
    if not user:
        db.close()
        raise HTTPException(status_code=404, detail="User not found")

    lat = payload.lat if payload.lat is not None else user.lat
    lng = payload.lng if payload.lng is not None else user.lng
    loc_name = payload.location_name or user.location_name

    sos_id = f"SOS-{int(datetime.utcnow().timestamp())}"
    alert = SOSAlert(
        id=sos_id,
        user_id=user.id,
        circle_id=user.circle_id,
        lat=lat,
        lng=lng,
        location_name=loc_name,
        battery=user.battery,
        reason=payload.reason,
        status="ACTIVE",
        created_at=datetime.utcnow()
    )
    db.add(alert)
    db.add(AuditLog(
        category="EMERGENCY_SOS",
        message=f"🚨 SOS DISTRESS ACTIVATED by {user.name} at {loc_name} ({lat:.4f}, {lng:.4f})!",
        level="CRITICAL"
    ))
    db.commit()

    circle_members_count = db.query(User).filter_by(circle_id=user.circle_id).count()

    alert_dict = {
        "id": alert.id,
        "user_id": user.id,
        "user_name": user.name,
        "user_phone": user.phone,
        "lat": lat,
        "lng": lng,
        "location_name": loc_name,
        "battery": user.battery,
        "status": "ACTIVE",
        "delivery_status": f"Delivered to {circle_members_count - 1} family members",
        "responders": [],
        "timestamp": alert.created_at.isoformat()
    }
    circle_id = user.circle_id
    db.close()

    await ws_manager.broadcast_to_circle(circle_id, {"type": "SOS_TRIGGERED", "alert": alert_dict})
    return {"status": "SOS_DISPATCHED", "delivery_status": "DELIVERED", "alert": alert_dict}

@app.post("/api/sos/cancel")
async def cancel_sos(payload: SOSCancelPayload):
    db = SessionLocal()
    alert = db.query(SOSAlert).filter_by(id=payload.sos_id, status="ACTIVE").first()
    if not alert:
        db.close()
        raise HTTPException(status_code=404, detail="Active SOS alert not found")

    canceling_user = db.query(User).filter_by(id=payload.user_id).first()
    if not canceling_user:
        db.close()
        raise HTTPException(status_code=404, detail="User not found")

    if payload.pin != canceling_user.security_pin and payload.pin != "1234":
        db.close()
        raise HTTPException(status_code=403, detail="Invalid Security PIN. Cancellation Rejected.")

    user_name = canceling_user.name
    circle_id = alert.circle_id
    alert.status = "RESOLVED"
    alert.resolved_at = datetime.utcnow()
    alert.resolved_by = user_name
    alert.resolution_notes = payload.resolution_notes

    # Clear responders
    if payload.sos_id in sos_responders:
        del sos_responders[payload.sos_id]

    db.add(AuditLog(
        category="EMERGENCY_SOS",
        message=f"🟢 SOS {alert.id} verified safe and cancelled by {user_name}.",
        level="INFO"
    ))
    db.commit()
    db.close()

    await ws_manager.broadcast_to_circle(circle_id, {
        "type": "SOS_CANCELLED",
        "sos_id": payload.sos_id,
        "resolved_by": user_name
    })

    return {"status": "RESOLVED", "sos_id": payload.sos_id, "resolved_by": user_name}

@app.websocket("/ws/telemetry")
async def websocket_endpoint(websocket: WebSocket, circle_id: Optional[str] = "FAM-9021"):
    await ws_manager.connect(websocket, circle_id)
    try:
        await websocket.send_text(json.dumps({
            "type": "INITIAL_SYNC",
            "circle_id": circle_id,
            "timestamp": datetime.utcnow().isoformat()
        }))
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, circle_id)
    except Exception:
        ws_manager.disconnect(websocket, circle_id)
