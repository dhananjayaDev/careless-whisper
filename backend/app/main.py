from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .db import Base, SessionLocal, engine, get_db
from .models import Device, LabSession, Message, Receipt
from .schemas import DeviceOut, DevicePatch, MessageOut, ProbeRequest, ReceiptOut, SessionOut
from .simulator import ACTION_META, DEFAULT_DEVICES, estimate_rtt

app = FastAPI(title="Careless Whisper Lab", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Hub:
    def __init__(self) -> None:
        self._rooms: dict[str, set[WebSocket]] = {}

    async def connect(self, session_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self._rooms.setdefault(session_id, set()).add(ws)

    def disconnect(self, session_id: str, ws: WebSocket) -> None:
        room = self._rooms.get(session_id)
        if not room:
            return
        room.discard(ws)
        if not room:
            self._rooms.pop(session_id, None)

    async def broadcast(self, session_id: str, payload: dict[str, Any]) -> None:
        room = list(self._rooms.get(session_id, set()))
        dead: list[WebSocket] = []
        data = json.dumps(payload, default=str)
        for ws in room:
            try:
                await ws.send_text(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(session_id, ws)


hub = Hub()


def _receipts_for_session(db: Session, session_id: str) -> list[ReceiptOut]:
    rows = (
        db.query(Receipt, Device)
        .join(Device, Device.id == Receipt.device_id)
        .filter(Receipt.session_id == session_id)
        .order_by(Receipt.id.asc())
        .all()
    )
    return [
        ReceiptOut(
            id=r.id,
            message_id=r.message_id,
            device_id=r.device_id,
            device_label=d.label,
            rtt_ms=r.rtt_ms,
            created_at=r.created_at,
        )
        for r, d in rows
    ]


def serialize_session(db: Session, session: LabSession) -> SessionOut:
    return SessionOut(
        id=session.id,
        devices=[DeviceOut.model_validate(d) for d in session.devices],
        messages=[MessageOut.model_validate(m) for m in session.messages],
        receipts=_receipts_for_session(db, session.id),
    )


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/sessions", response_model=SessionOut)
def create_session(db: Session = Depends(get_db)) -> SessionOut:
    session = LabSession(id=str(uuid.uuid4()))
    db.add(session)
    db.flush()
    for spec in DEFAULT_DEVICES:
        db.add(Device(session_id=session.id, **spec))
    db.commit()
    db.refresh(session)
    return serialize_session(db, session)


@app.get("/api/sessions/{session_id}", response_model=SessionOut)
def get_session(session_id: str, db: Session = Depends(get_db)) -> SessionOut:
    session = db.get(LabSession, session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return serialize_session(db, session)


@app.patch("/api/sessions/{session_id}/devices/{device_id}", response_model=DeviceOut)
async def patch_device(
    session_id: str,
    device_id: int,
    body: DevicePatch,
    db: Session = Depends(get_db),
) -> DeviceOut:
    device = db.get(Device, device_id)
    if not device or device.session_id != session_id:
        raise HTTPException(404, "Device not found")
    data = body.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(device, key, value)
    db.commit()
    db.refresh(device)
    await hub.broadcast(
        session_id,
        {"type": "device_updated", "device": DeviceOut.model_validate(device).model_dump()},
    )
    return DeviceOut.model_validate(device)


@app.post("/api/sessions/{session_id}/probe", response_model=SessionOut)
async def probe(
    session_id: str,
    body: ProbeRequest,
    db: Session = Depends(get_db),
) -> SessionOut:
    session = db.get(LabSession, session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    meta = ACTION_META[body.action]
    default_bodies = {
        "text": "Hello from the lab",
        "react": "👍 self-reaction",
        "edit": "Edited message content",
        "delete": "Message deleted for everyone",
    }
    message = Message(
        session_id=session_id,
        action=body.action,
        body=body.body or default_bodies[body.action],
        silent=meta["silent"],
        notified_victim=meta["notified_victim"],
    )
    db.add(message)
    db.flush()

    created_receipts: list[ReceiptOut] = []
    for device in session.devices:
        rtt = estimate_rtt(
            online=device.online,
            screen_on=device.screen_on,
            network=device.network,
        )
        if rtt is None:
            continue
        # Simulate network delay before the receipt lands.
        await asyncio.sleep(min(rtt / 1000.0, 0.35))
        receipt = Receipt(
            session_id=session_id,
            message_id=message.id,
            device_id=device.id,
            rtt_ms=rtt,
            created_at=datetime.utcnow(),
        )
        db.add(receipt)
        db.flush()
        out = ReceiptOut(
            id=receipt.id,
            message_id=message.id,
            device_id=device.id,
            device_label=device.label,
            rtt_ms=rtt,
            created_at=receipt.created_at,
        )
        created_receipts.append(out)
        await hub.broadcast(
            session_id,
            {
                "type": "receipt",
                "message": MessageOut.model_validate(message).model_dump(),
                "receipt": out.model_dump(),
            },
        )

    db.commit()
    db.refresh(session)
    snapshot = serialize_session(db, session)
    await hub.broadcast(session_id, {"type": "session", "session": snapshot.model_dump()})
    return snapshot


@app.websocket("/ws/{session_id}")
async def ws_session(session_id: str, websocket: WebSocket) -> None:
    db = SessionLocal()
    try:
        session = db.get(LabSession, session_id)
        if not session:
            await websocket.close(code=4404)
            return
        await hub.connect(session_id, websocket)
        await websocket.send_text(
            json.dumps(
                {"type": "session", "session": serialize_session(db, session).model_dump()},
                default=str,
            )
        )
        while True:
            # Keep connection alive; client may send pings.
            await websocket.receive_text()
    except WebSocketDisconnect:
        hub.disconnect(session_id, websocket)
    finally:
        db.close()
