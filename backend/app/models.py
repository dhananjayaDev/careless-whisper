from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class LabSession(Base):
    __tablename__ = "lab_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    devices: Mapped[list["Device"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    messages: Mapped[list["Message"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    receipts: Mapped[list["Receipt"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("lab_sessions.id"))
    label: Mapped[str] = mapped_column(String(80))
    kind: Mapped[str] = mapped_column(String(40))  # phone | desktop | web
    online: Mapped[bool] = mapped_column(Boolean, default=True)
    screen_on: Mapped[bool] = mapped_column(Boolean, default=True)
    network: Mapped[str] = mapped_column(String(20), default="wifi")  # wifi | cellular | wired

    session: Mapped["LabSession"] = relationship(back_populates="devices")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("lab_sessions.id"))
    action: Mapped[str] = mapped_column(String(20))  # text | react | edit | delete
    body: Mapped[str] = mapped_column(Text)
    silent: Mapped[bool] = mapped_column(Boolean, default=False)
    notified_victim: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["LabSession"] = relationship(back_populates="messages")


class Receipt(Base):
    __tablename__ = "receipts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("lab_sessions.id"))
    message_id: Mapped[int] = mapped_column(ForeignKey("messages.id"))
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"))
    rtt_ms: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["LabSession"] = relationship(back_populates="receipts")
