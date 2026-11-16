"""Synthetic delivery-receipt timing for the educational lab.

Models the paper's ideas only: screen on/off and network affect RTT.
No real messenger protocols are used.
"""

from __future__ import annotations

import random

# Actions that typically notify the victim in real messengers vs silent probes.
ACTION_META = {
    "text": {"silent": False, "notified_victim": True, "label": "Text message"},
    "react": {"silent": True, "notified_victim": False, "label": "Self-reaction"},
    "edit": {"silent": True, "notified_victim": False, "label": "Edit message"},
    "delete": {"silent": True, "notified_victim": False, "label": "Delete for everyone"},
}

BASE_RTT = {
    "wifi": 120.0,
    "cellular": 280.0,
    "wired": 80.0,
}

SCREEN_OFF_EXTRA = (900.0, 2200.0)
JITTER = (-40.0, 60.0)


def estimate_rtt(*, online: bool, screen_on: bool, network: str) -> float | None:
    if not online:
        return None
    base = BASE_RTT.get(network, 150.0)
    rtt = base + random.uniform(*JITTER)
    if not screen_on:
        rtt += random.uniform(*SCREEN_OFF_EXTRA)
    return max(20.0, round(rtt, 1))


DEFAULT_DEVICES = [
    {"label": "Smartphone", "kind": "phone", "online": True, "screen_on": True, "network": "cellular"},
    {"label": "Home Workstation", "kind": "desktop", "online": True, "screen_on": True, "network": "wired"},
    {"label": "Work Web Client", "kind": "web", "online": False, "screen_on": True, "network": "wifi"},
]
