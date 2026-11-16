# Careless Whisper Lab

Educational **simulation** of the ideas in *Careless Whisper: Exploiting Silent Delivery Receipts to Monitor Users on Mobile Instant Messengers* (Gegenhuber et al., University of Vienna / SBA Research).

This app teaches the **concepts**. It does **not** talk to WhatsApp, Signal, or any real messenger.

---

## Disclaimer (read first)

**This repository is for education and demonstration of privacy side-channel concepts only.**

- It does **not** include live WhatsApp, Signal, or Threema attack tooling.
- It does **not** document step-by-step instructions, payloads, client configs, or runbooks to probe, monitor, fingerprint, or drain real user accounts.
- Using messenger automation or protocol clients to silently track people without authorization can violate platform Terms of Service, privacy law, and criminal statutes (e.g. stalking / unlawful surveillance). **Do not do that.**
- The original research was conducted under an academic threat model with responsible disclosure to vendors (see paper §III and slide deck p.17). Reading the paper is not permission to weaponize it.
- Anything in this README labeled “how researchers studied it” is a **high-level summary of published science**, not an implementation guide for live attacks.
- Safe path in this project: **simulator, synthetic RTTs, scripted replays, classroom dual-UI demos.**

If you need a live empirical replication, that belongs in a separate ethics-approved research program with consenting lab accounts—not in this app and not via instructions in this file.

---

## Gap: live messenger study vs this lab (and what we will not publish)

There is a hard gap between **(A) what the paper did on real messengers** and **(B) what this lab ships**. There is a third line **(C) live attack steps**—intentionally **not** written here.

| Layer | What it is | Present in this repo? |
|-------|------------|------------------------|
| **A. Paper / live research** | Real WhatsApp/Signal (and Threema comparison), custom clients, silent delivery-receipt probing, RTT measurement, multi-device tracking, OS hints, resource-exhaustion measurements | **No code** — cited only |
| **B. This educational lab** | Fake devices, JSON probes, synthetic delays, WebSocket UI, teaching charts | **Yes** |
| **C. Operational attack steps** | Exact commands, session login flows, packet recipes, targeting phone numbers, continuous monitor scripts against production apps | **Deliberately omitted** |

### A — How the paper’s live work worked (high level only)

Cited from Gegenhuber et al., arXiv:2411.11194:

1. **Access the real protocol** using research/community clients with API-level access (Table II: e.g. whatsmeow, Cobalt, signal-cli) — §III-D.  
2. **Choose a threat model**: *creepy companion* (existing chat) vs *spooky stranger* (phone number only) — §III-B.  
3. **Trigger delivery receipts** with message types beyond plain text (react / edit / delete); identify which stay silent (no useful victim notification) — §IV, Tables III–IV.  
4. **Measure RTT** from probe send → device delivery receipt; sample often enough to see activity (e.g. screen on/off in Fig. 1) — §II, §V-C.  
5. **Exploit client-fanout**: each online companion device acks independently; reconnect flushes pending receipts — Fig. 2, §V-B.  
6. **Optional further goals in the paper**: device/OS fingerprinting and resource exhaustion measurements — §I, §III-A, §V; slide deck p.14–15.

That is the **scientific outline**. This README stops there on purpose.

### B — How this lab approximates it (what you can run)

| Paper idea | Lab stand-in |
|------------|--------------|
| Real delivery receipt | Synthetic `Receipt` row + WebSocket event |
| Silent vs noisy probe | `ACTION_META` flags (`silent` / `notified_victim`) |
| Screen / network effects | Rules in `backend/app/simulator.py` |
| Multi-device fan-out | Hardcoded phone / desktop / web devices |
| Long measurement campaign | Manual button clicks (+ future replay CSV, not live apps) |

### C — Live WhatsApp / Signal attack steps: not provided

**We will not add** to this repository or README:

- How to log into or automate WhatsApp/Signal for silent probing  
- How to craft or send real reaction/edit/delete frames against production servers  
- How to target real phone numbers, run 1 Hz monitors, fingerprint OS from live receipts, or reproduce battery/data drain  
- Copy-paste “PoC” commands, scripts, or configs that close gap A→C  

**Why the gap stays closed here**

- Closing A→C turns an educational sim into surveillance tooling.  
- Platform ToS and law generally forbid unauthorized monitoring.  
- Vendor mitigations and client behavior change over time (paper/slides note Meta privacy updates after disclosure); stale attack recipes are both harmful and unreliable.  
- Students get a clearer lesson from a **controlled simulator** plus reading §III–V of the paper than from an unofficial exploit runbook.

**If your goal is demonstration:** use this lab (layer B), cite the paper for authority (layer A), and show the dual-UI / RTT chart story.  
**If your goal is academic replication of layer A:** work from the paper under institutional ethics review—do not expect step-by-step attack instructions from this repo.

---

## How this lab works

The UI is a toy messenger lab with three parts:

### 1. Lab chat probes
You trigger four actions:

| Action | In the lab | Educational point |
|--------|------------|-------------------|
| **Text** | Marked **noisy** — “victim notified” | Normal messages produce delivery receipts *and* a visible notification |
| **React** | Marked **silent** — no victim notification | Self-reactions can still produce receipts without alerting the user |
| **Edit** | Silent | Edits can ack without a normal chat alert |
| **Delete** | Silent | Deletes can ack without a normal chat alert |

Each probe creates a **message** row and, for every **online** device, a synthetic **delivery receipt** with an RTT (round-trip time) in milliseconds.

### 2. Device board
Three fake companion devices ship with each session:

- Smartphone (cellular)
- Home Workstation (wired)
- Work Web Client (wifi; offline by default)

You can toggle:

- **Online** — offline devices issue no receipt
- **Screen on** — screen-off adds a large delay to synthetic RTT
- **Network** — cellular is slower than wifi/wired

This mirrors the paper’s idea that **each linked device can ack independently**, so presence can be inferred per device.

### 3. RTT timeline
Recharts plots receipt RTTs per device after each probe. Turning screen off or switching to cellular should push points higher — same *shape* of leakage the paper measured, with fake numbers.

### Under the hood
- **Frontend:** React + Vite + Recharts  
- **Backend:** FastAPI + WebSocket + SQLite  
- **Realtime:** probes and device updates are broadcast over WebSocket  
- **Timing model:** simple rules in `backend/app/simulator.py` (base RTT by network + extra delay if screen off + jitter). No real protocol packets.

---

## How this differs from the research paper

| | **This lab** | **Careless Whisper paper** |
|--|--------------|----------------------------|
| **Target** | Fake in-app devices only | Real WhatsApp / Signal (and Threema for comparison) |
| **Protocol** | JSON REST + WebSocket toy API | Real messenger protocol via custom/open clients (e.g. whatsmeow, Cobalt, signal-cli) |
| **Silent probes** | Labels and UI flags only | Crafted reactions/edits/deletes (including non-existent message IDs in stranger scenarios) that the real app acks without notifying the user |
| **RTT data** | Synthetic formula | Measured wall-clock delay from send → real delivery receipt |
| **Multi-device** | Three hard-coded lab devices | Real phone + desktop/web companion sessions on a user’s account |
| **OS fingerprinting** | Not implemented | Differences in receipt handling across Android / iOS / desktop clients |
| **Resource exhaustion** | Not implemented | High-rate silent probes draining battery/data (reported especially severe on WhatsApp at the time) |
| **Access model** | Anyone with the lab URL | Paper studied “creepy companion” (existing chat) and “spooky stranger” (phone number only) |
| **Ethics / disclosure** | Classroom demo | Responsible disclosure to Meta; later privacy-setting changes |
| **Goal** | Teach *why* delivery receipts leak | Empirically prove and measure the leak on production messengers |

**Short version:** the paper attacked **real** delivery-receipt side channels on production apps. This repo **replays the lesson** with a simulator so you can see noisy vs silent, multi-device acks, and RTT shifts — without monitoring anyone.

---

## What this app lacks vs the paper

Gaps between the lab and the actual Careless Whisper study, with **paper citations** and a **safe demo implementation** note for each.

**Primary reference:** Gabriel K. Gegenhuber et al., *Careless Whisper: Exploiting Silent Delivery Receipts to Monitor Users on Mobile Instant Messengers*, arXiv:2411.11194, 2024. https://arxiv.org/abs/2411.11194  
(Also the slide deck in this repo: `Careless_Whisper_Gabriel_Gegenhuber_Universität-Wien_SBA-Research.pdf`.)

**Demo policy for this repo:** implement gaps as **simulations, recorded traces, or dual-UI classroom demos**. Do **not** wire this product to live WhatsApp/Signal probing of real users. Academic replication of the paper’s live measurements requires separate ethics approval, consenting lab accounts, and is out of scope for this app.

For each item: **Gap → Paper basis → How to demo it (safely) in/near this lab.**

### Protocol & platforms

1. **No real WhatsApp / Signal / Threema**  
   - **Paper:** Analysis limited to messengers with multi-device E2EE + delivery receipts; focused on WhatsApp, Signal, Threema (§III-C, Table I).  
   - **Demo:** Keep the toy protocol; add a “platform preset” dropdown (`WhatsApp-like` / `Signal-like` / `Threema-like`) that changes which actions are silent and whether multi-device acks fan out—matching Table III/IV behavior at a conceptual level.

2. **No custom messenger clients**  
   - **Paper:** API-level access via whatsmeow, Cobalt, signal-cli, libsignal, threema-android (§III-D, Table II).  
   - **Demo:** Document those as *research-only references* in the UI (“How researchers measured this”). Do not embed them in the student app; optional advanced module = link to paper + Table II only.

3. **No crafted protocol messages**  
   - **Paper:** Receipts also issued for reactions, edits, deletes; stealth depends on action type (§IV, Tables III–IV). Stranger case used reactions referencing non-existing message IDs (§IV).  
   - **Demo:** Extend `ACTION_META` so each button shows a “packet storyboard” (send → server ack → device ack → notify? Y/N) drawn from Table III. Still synthetic payloads (JSON), not real messenger frames.

4. **No server-ack vs device-ack distinction**  
   - **Paper:** Server ack (queued at server) vs device ack (received/decrypted on device); RTT uses the device path (§II Message Delivery; Fig. 2).  
   - **Demo:** Emit two timed events per probe: `server_ack` (~fixed small delay) and `device_ack` (state-dependent delay). Chart both series so students see why only device timing leaks activity.

5. **No cross-platform comparison**  
   - **Paper:** WhatsApp/Signal allow covert probing; Threema restricts receipts (esp. no silent stranger/companion path; aggregated multi-device receipts) (§IV summary, Table IV).  
   - **Demo:** Side-by-side mode: same probe on three presets; Threema-like returns **one** aggregated receipt and marks silent stranger probes as “not possible / becomes noisy text.”

### Threat models the paper studied

6. **No “creepy companion” path**  
   - **Paper:** Attacker already has a chat with ≥1 message; self-reactions / remove-reaction stay silent but still ack (§III-B; §IV-B).  
   - **Demo:** Lab mode toggle **Companion**: require seeding one prior “shared message,” then only allow silent react/remove on that message ID. Show that Text remains noisy.

7. **No “spooky stranger” path**  
   - **Paper:** No prior contact; phone number enough; silent probing via reactions to non-existing message IDs on WhatsApp/Signal; not on Threema (§III-B; §IV).  
   - **Demo:** Lab mode **Stranger**: no seeded chat; silent probe still works on WhatsApp/Signal presets, fails/noisy on Threema preset. Use fake “lab numbers,” never real people.

8. **No phone-number targeting**  
   - **Paper:** Spooky stranger only needs the victim’s phone number; burner/prepaid SIM hides attacker identity (§III-B).  
   - **Demo:** Accept a synthetic lab ID shaped like `+lab-555-…` for teaching the threat model UI—not a gateway to real directories.

9. **No contact-list / conversation bootstrap**  
   - **Paper:** Companion-style silent reacts need an existing conversation message to react to (§IV-B).  
   - **Demo:** “Bootstrap chat” button that inserts one prior message; until then, Companion mode blocks silent reacts and explains why (cite §IV-B).

### Measurements & inference

10. **No real RTT measurement**  
    - **Paper:** RTT = delay from sending probe to receiving delivery receipt; used as timing side channel (§II; §V-C; Fig. 1).  
    - **Demo:** In-sim: timestamp `t_send` / `t_ack` in SQLite and plot `t_ack - t_send`. Optionally load **CSV replays** of figures from the paper (digitized or author-provided) for “paper trace” mode.

11. **No high-frequency continuous monitoring**  
    - **Paper:** Stealth enables high-frequency probing (up to sub-second; Fig. 1 uses 1 Hz) without notifying the victim (§I; contributions).  
    - **Demo:** “Auto-probe” slider (e.g. 1 probe / 1–20 s) **inside the simulator only**, with a visible ethics banner. Do not point this at live messengers.

12. **No screen on/off classification from live data**  
    - **Paper:** Screen-on RTTs typically ≤1 s; screen-off often >1 s (WhatsApp/iPhone example, 1 Hz) (Fig. 1; §V-C; slide deck p.12).  
    - **Demo:** Hide the screen toggle from the “attacker” view; run a simple threshold classifier (`rtt < 1000 ms ⇒ screen on`) and score against the hidden ground truth. Matches the paper’s teaching claim without real devices.

13. **No app-foreground / tab-active detection**  
    - **Paper:** In some scenarios, finer activity (messenger in foreground / tab active) also shifts RTT (§I Activity Leakage; slide deck p.12).  
    - **Demo:** Add states `background` / `foreground` / `tab_active` with smaller RTT deltas than screen-off; quiz students to label the state from the chart.

14. **No Wi‑Fi vs cellular inference from receipts alone**  
    - **Paper:** Access technology and environment influence RTTs; prior work also linked receipts to coarse location / access tech (§II Mitigation Status; §V; related [21]).  
    - **Demo:** Preset delay distributions per network (as now) plus a blind “guess the network” exercise from RTT samples.

15. **No schedule / routine reconstruction**  
    - **Paper:** Multi-device online patterns can reveal daily routines (home workstation vs work computer vs phone) (§I Multi-Device Amplification; §V-B; slide deck p.11, p.13).  
    - **Demo:** Ship a **scripted day timeline** (JSON): at 09:00 work web goes online, at 18:00 home desktop, etc. Playback emits receipts; students annotate “left home / at work.”

16. **No open-world field case**  
    - **Paper:** Open-world measurement under real-world conditions following complex routines across devices (§I Activity Leakage).  
    - **Demo:** Include one anonymized **replay dataset** labeled “open-world style (synthetic)” that mimics Fig. 3/4-style traces—not live following of a person.

### Multi-device & fingerprinting

17. **No real companion sessions**  
    - **Paper:** Client-fanout: each recipient device has its own keys and issues independent delivery receipts (Fig. 2; §II Multi Device Setups).  
    - **Demo:** Already partial. Improve by letting students **add/remove companion slots** and see fan-out receipt count = number of online devices.

18. **No pending-receipt burst on reconnect**  
    - **Paper:** If a device was offline, receipts for missed messages are issued when it comes online (§V-B; slide deck p.11).  
    - **Demo:** While a device is offline, queue N probes; on flipping Online, emit N receipts in a burst with timestamps—teaches the reconnect side channel.

19. **No device-count / key-directory reconnaissance**  
    - **Paper:** Key directory / device list can leak how many sessions exist; main device has lowest index (WhatsApp 0, Signal 1); validated with concurrent work (§V; device directory discussion).  
    - **Demo:** Show a read-only “device directory” panel listing lab device indexes when a session starts—conceptual recon UI with fake entries.

20. **No OS / client fingerprinting**  
    - **Paper:** Implementation differences across architectures leak OS/client type (§I; §V; slide deck p.14 “Device Operating System Fingerprinting”).  
    - **Demo:** Assign each lab device a `client_profile` with distinct receipt delay noise / ordering quirks; students match traces to Android / iOS / Desktop profiles using a legend from the paper’s qualitative claim.

21. **No main-vs-companion device indexing**  
    - **Paper:** Main vs companion distinguishable via device index semantics on WhatsApp/Signal (§V).  
    - **Demo:** Label devices `index=0 (main)` vs `index≥1 (companion)` in the board; probes annotate which index acked.

### Offensive results in the paper (demo carefully — prefer charts, not attacks)

22. **No resource-exhaustion demo**  
    - **Paper:** Silent reaction spam consumed resources without notifications; WhatsApp example ~18%/h battery and ~13.3 GB/h data in their measurements (slide deck p.15; §I Resource Exhaustion; §V).  
    - **Demo:** **Static teaching chart** re-plotting the paper’s reported figures + a calculator (“if probe rate = X, estimated data = …”) using their published numbers. Do **not** implement a live drain tool.

23. **No rate-limit comparison**  
    - **Paper:** Signal had better rate-limiting, harder to exploit; WhatsApp did not meaningfully rate-limit their requests (slide deck p.15; discussion in §V/§VI).  
    - **Demo:** Platform preset: after N probes/minute, Signal-like returns `429 / delayed`; WhatsApp-like keeps answering—shows why mitigations matter.

24. **No DoS / call-quality degradation experiments**  
    - **Paper:** Resource exhaustion can degrade bandwidth-heavy uses (e.g. video calls) (§III-A attack goals).  
    - **Demo:** Narrative + optional simulated “call quality meter” that drops when background probe rate is high in the **simulator**—no real call disruption.

### Methodology & rigor

25. **No controlled device farm**  
    - **Paper:** Two-step method; many models/chipsets/OS versions in Appendix Table VIII (§III-D).  
    - **Demo:** “Device farm” page listing Table VIII as reference data; pick a model card to load that profile’s synthetic delay parameters.

26. **No statistical evaluation**  
    - **Paper:** Systematic measurements of RTT distributions for activity classification (§V-C).  
    - **Demo:** Export lab receipts to CSV; notebook or in-app panel computes moving average (paper/slides use Mov. Avg. N=5) and simple accuracy for screen-on detection.

27. **No geolocation angle**  
    - **Paper:** Builds on prior delivery-receipt geolocation (country-level) via RTT [21], cited in §I/§II; Appendix A1 discusses server infra / RTT limits.  
    - **Demo:** Map cartoon “regions” to coarse base latency buckets; students see that **fine** indoor activity needs stealthy high-rate probes (this paper), while **coarse** location was earlier work—cite both.

28. **No responsible-disclosure / vendor-fix timeline**  
    - **Paper / slides:** Reported to Meta 2024-09-05; internal forward 2024-09-24; new privacy settings Oct 2024 (slide deck p.17).  
    - **Demo:** Timeline component in the UI with those dates; toggle “pre-fix / post-fix” lab rules (e.g. stranger silent probe disabled after fix).

29. **No “read receipts off, delivery receipts still on” live proof**  
    - **Paper:** Read receipts can be disabled; delivery receipts generally cannot (§I; §II).  
    - **Demo:** Privacy settings panel: turning off Read hides read events but **Delivery** checkboxes remain forced on—interactive proof of the design claim.

### Product / lab limits

30. **Single short session UI**  
    - **Paper:** Long traces over minutes–hours (Figs. 1, 3, 4; slide deck p.12–13).  
    - **Demo:** Session recording, CSV/JSON export, and “load paper-like trace” for classroom replay.

31. **No victim-perspective phone UI**  
    - **Paper:** Stealth = no notification / no unread affordance for chosen actions (§IV).  
    - **Demo:** Split view: **Attacker lab** | **Victim phone mock**. Noisy text lights up the victim UI; silent react does not—while receipts still appear on the attacker chart.

32. **No mitigation playground**  
    - **Paper:** Random receipt delay and similar mitigations proposed earlier were not widely adopted; Threema’s restrictive receipt design impedes stealth (§II Mitigation Status; §IV).  
    - **Demo:** Toggles for students: `aggregate multi-device acks`, `randomize receipt delay`, `rate-limit probes`, `allow delivery-receipt privacy off`. Re-run probes and discuss which mitigations kill which attacks from Table IV.

These gaps are **by design** for an educational simulator. Closing them **inside this repo** should stay on simulation, replays, and teaching UI. Reproducing the paper’s live messenger measurements is a separate, ethics-bound research activity—not a feature to ship in this app.

---

## What the paper showed (context)

1. **Delivery receipts** (message reached the device) are harder to turn off than **read receipts**.
2. Some actions (especially reactions to your own messages, and certain edits/deletes) can trigger receipts **without** a useful notification to the target.
3. In multi-device setups, **each online device** can emit its own receipt → online/offline tracking across phone and companions.
4. **Timing** of receipts correlates with activity (e.g. screen on vs standby) and environment (network).
5. The same channel can be abused for **reconnaissance** (device/OS hints) and, at high rate, **resource drain**.

Use the lab to internalize those ideas. Do not use real messenger automation to probe people.

---

## Setup

```powershell
# Backend
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Frontend (new terminal)
cd frontend
npm install
```

## Run

```powershell
# Terminal 1 — API
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

```powershell
# Terminal 2 — UI
cd frontend
npm run dev
```

Open http://127.0.0.1:5173  
Health check: http://127.0.0.1:8000/api/health

## Try this walkthrough

1. Click **Text** → feed shows **noisy** / victim notified.  
2. Click **React** → feed shows **silent** / no victim notification; chart still gets RTTs.  
3. Uncheck **Screen on** on Smartphone → probe again → phone RTT jumps.  
4. Uncheck **Online** on Home Workstation → that device stops appearing in new receipts.  
5. Set network to **Cellular** vs **Wired** → compare RTT heights.

## Reference

- Paper / talk materials in this repo: `Careless_Whisper_Gabriel_Gegenhuber_Universität-Wien_SBA-Research.pdf`  
- arXiv: https://arxiv.org/abs/2411.11194  
