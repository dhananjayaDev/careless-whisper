const API = "http://127.0.0.1:8000";

export async function createSession() {
  const res = await fetch(`${API}/api/sessions`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to create session");
  return res.json();
}

export async function probe(sessionId, action) {
  const res = await fetch(`${API}/api/sessions/${sessionId}/probe`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action }),
  });
  if (!res.ok) throw new Error("Probe failed");
  return res.json();
}

export async function patchDevice(sessionId, deviceId, patch) {
  const res = await fetch(`${API}/api/sessions/${sessionId}/devices/${deviceId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patch),
  });
  if (!res.ok) throw new Error("Device update failed");
  return res.json();
}

export function connectSocket(sessionId, onMessage) {
  const ws = new WebSocket(`ws://127.0.0.1:8000/ws/${sessionId}`);
  ws.onmessage = (event) => {
    try {
      onMessage(JSON.parse(event.data));
    } catch {
      /* ignore bad payloads */
    }
  };
  return ws;
}
