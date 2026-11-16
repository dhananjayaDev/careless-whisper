from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ActionType = Literal["text", "react", "edit", "delete"]
NetworkType = Literal["wifi", "cellular", "wired"]


class DeviceOut(BaseModel):
    id: int
    label: str
    kind: str
    online: bool
    screen_on: bool
    network: str

    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    id: int
    action: str
    body: str
    silent: bool
    notified_victim: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ReceiptOut(BaseModel):
    id: int
    message_id: int
    device_id: int
    device_label: str
    rtt_ms: float
    created_at: datetime


class SessionOut(BaseModel):
    id: str
    devices: list[DeviceOut]
    messages: list[MessageOut]
    receipts: list[ReceiptOut]


class ProbeRequest(BaseModel):
    action: ActionType = "react"
    body: str = Field(default="", max_length=280)


class DevicePatch(BaseModel):
    online: bool | None = None
    screen_on: bool | None = None
    network: NetworkType | None = None
