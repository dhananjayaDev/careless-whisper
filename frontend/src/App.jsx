import { useEffect, useMemo, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { connectSocket, createSession, patchDevice, probe } from "./api";
import "./App.css";

const ACTIONS = [
  { id: "text", label: "Text", hint: "Noisy — victim gets a notification" },
  { id: "react", label: "React", hint: "Silent — delivery receipt, no UI ping" },
  { id: "edit", label: "Edit", hint: "Silent — receipt without alert" },
  { id: "delete", label: "Delete", hint: "Silent — receipt without alert" },
];

export default function App() {
  const [session, setSession] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let ws;
    let cancelled = false;

    (async () => {
      try {
        const created = await createSession();
        if (cancelled) return;
        setSession(created);
        ws = connectSocket(created.id, (msg) => {
          if (cancelled) return;
          if (msg.type === "session" && msg.session) {
            setSession(msg.session);
          } else if (msg.type === "device_updated" && msg.device) {
            setSession((prev) => {
              if (!prev) return prev;
              return {
                ...prev,
                devices: prev.devices.map((d) =>
                  d.id === msg.device.id ? { ...d, ...msg.device } : d,
                ),
              };
            });
          } else if (msg.type === "receipt" && msg.receipt) {
            setSession((prev) => {
              if (!prev) return prev;
              const messages = prev.messages.some((m) => m.id === msg.message.id)
                ? prev.messages
                : [...prev.messages, msg.message];
              const receipts = prev.receipts.some((r) => r.id === msg.receipt.id)
                ? prev.receipts
                : [...prev.receipts, msg.receipt];
              return { ...prev, messages, receipts };
            });
          }
        });
      } catch (err) {
        if (!cancelled) setError(String(err.message || err));
      }
    })();

    return () => {
      cancelled = true;
      if (ws) ws.close();
    };
  }, []);

  const deviceSeries = useMemo(() => {
    if (!session) return [];
    return session.devices.map((d) => d.label);
  }, [session]);

  const chartData = useMemo(() => {
    if (!session) return [];
    const byMessage = new Map();
    for (const r of session.receipts) {
      if (!byMessage.has(r.message_id)) {
        byMessage.set(r.message_id, { label: `msg ${r.message_id}` });
      }
      byMessage.get(r.message_id)[r.device_label] = r.rtt_ms;
    }
    return [...byMessage.values()];
  }, [session]);

  async function onProbe(action) {
    if (!session || busy) return;
    setBusy(true);
    setError("");
    try {
      const next = await probe(session.id, action);
      setSession(next);
    } catch (err) {
      setError(String(err.message || err));
    } finally {
      setBusy(false);
    }
  }

  async function onDeviceChange(deviceId, patch) {
    if (!session) return;
    try {
      const updated = await patchDevice(session.id, deviceId, patch);
      setSession((prev) => ({
        ...prev,
        devices: prev.devices.map((d) => (d.id === updated.id ? updated : d)),
      }));
    } catch (err) {
      setError(String(err.message || err));
    }
  }

  return (
    <div className="page">
      <header className="hero">
        <p className="brand">Careless Whisper Lab</p>
        <h1>Delivery receipts as a side channel</h1>
        <p className="lede">
          Simulated lab — noisy vs silent probes, device state, synthetic RTTs
          (no real WhatsApp / Signal).
        </p>
      </header>

      {error && <div className="banner error">{error}</div>}
      {!session && !error && <div className="banner">Starting lab session…</div>}

      {session && (
        <main className="grid">
          <section className="panel">
            <h2>Lab chat probes</h2>
            <p className="sub">
              Noisy text vs silent react / edit / delete — both still yield
              receipts.
            </p>
            <div className="actions">
              {ACTIONS.map((a) => (
                <button
                  key={a.id}
                  type="button"
                  disabled={busy}
                  onClick={() => onProbe(a.id)}
                  title={a.hint}
                >
                  {a.label}
                </button>
              ))}
            </div>
            <ul className="feed">
              {[...session.messages].reverse().map((m) => (
                <li key={m.id} className={m.silent ? "silent" : "noisy"}>
                  <span className="tag">{m.silent ? "silent" : "noisy"}</span>
                  <strong>{m.action}</strong> — {m.body}
                  <em>
                    {m.notified_victim
                      ? "Victim notified"
                      : "No victim notification"}
                  </em>
                </li>
              ))}
            </ul>
          </section>

          <section className="panel">
            <h2>Device board</h2>
            <p className="sub">
              Online companions ack independently; offline stays dark.
            </p>
            <div className="devices">
              {session.devices.map((d) => (
                <article key={d.id} className={d.online ? "online" : "offline"}>
                  <header>
                    <strong>{d.label}</strong>
                    <span>{d.kind}</span>
                  </header>
                  <label>
                    <input
                      type="checkbox"
                      checked={d.online}
                      onChange={(e) =>
                        onDeviceChange(d.id, { online: e.target.checked })
                      }
                    />
                    Online
                  </label>
                  <label>
                    <input
                      type="checkbox"
                      checked={d.screen_on}
                      onChange={(e) =>
                        onDeviceChange(d.id, { screen_on: e.target.checked })
                      }
                    />
                    Screen on
                  </label>
                  <label>
                    Network
                    <select
                      value={d.network}
                      onChange={(e) =>
                        onDeviceChange(d.id, { network: e.target.value })
                      }
                    >
                      <option value="wifi">Wi‑Fi</option>
                      <option value="cellular">Cellular</option>
                      <option value="wired">Wired</option>
                    </select>
                  </label>
                </article>
              ))}
            </div>
          </section>

          <section className="panel wide">
            <h2>RTT timeline</h2>
            <p className="sub">
              Screen-off / cellular raise synthetic RTT — same shape as the
              paper.
            </p>
            <div className="chart">
              {chartData.length === 0 ? (
                <p className="empty">Send a probe to plot receipt RTTs.</p>
              ) : (
                <div className="chart-wrap">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart
                      data={chartData}
                      margin={{ top: 4, right: 8, left: 0, bottom: 0 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#2a3038" />
                      <XAxis dataKey="label" stroke="#8b939c" tick={{ fontSize: 10 }} />
                      <YAxis
                        stroke="#8b939c"
                        width={42}
                        tick={{ fontSize: 10 }}
                        label={{
                          value: "ms",
                          angle: -90,
                          position: "insideLeft",
                          fill: "#8b939c",
                          fontSize: 10,
                        }}
                      />
                      <Tooltip
                        contentStyle={{
                          background: "#0e1116",
                          border: "1px solid #2a3038",
                          fontFamily: "IBM Plex Mono, monospace",
                          fontSize: 11,
                        }}
                      />
                      <Legend wrapperStyle={{ fontSize: 11 }} />
                      {deviceSeries.map((name, idx) => (
                        <Line
                          key={name}
                          type="monotone"
                          dataKey={name}
                          stroke={["#3dff9a", "#e6b84d", "#9aa4ad"][idx % 3]}
                          strokeWidth={2}
                          dot={{ r: 2 }}
                          connectNulls
                        />
                      ))}
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          </section>
        </main>
      )}

      <footer className="foot">
        Educational simulation only. Delivery receipts cannot be turned off in
        many real messengers; read receipts usually can.
      </footer>
    </div>
  );
}
