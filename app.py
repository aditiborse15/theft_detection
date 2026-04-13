"""
╔══════════════════════════════════════════════════════════════════╗
║     SMART ELECTRICITY THEFT DETECTION SYSTEM — DASHBOARD        ║
║     Built with Streamlit + Firebase Realtime Database            ║
║     ESP32 | Voltage Sensor | Current Sensor | Relay | LCD        ║
╚══════════════════════════════════════════════════════════════════╝

Requirements:
    pip install streamlit firebase-admin plotly pandas

Run:
    streamlit run dashboard.py
"""

import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import pandas as pd

from datetime import datetime, timezone
import time
import json
import os

# ─────────────────────────────────────────────
#  PAGE CONFIG  (must be FIRST Streamlit call)
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Smart Electricity Theft Detection",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
#  CUSTOM CSS — Industrial Dark Theme
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=Share+Tech+Mono&family=Exo+2:wght@300;400;600;700&display=swap');

/* ── Root Variables ── */
:root {
    --bg-dark:      #0a0e1a;
    --bg-panel:     #0f1526;
    --bg-card:      #141c2e;
    --accent-blue:  #00d4ff;
    --accent-green: #00ff88;
    --accent-red:   #ff2d55;
    --accent-amber: #ffb300;
    --accent-purple:#a855f7;
    --text-primary: #e8f0fe;
    --text-muted:   #6b7a99;
    --border:       #1e2a42;
    --glow-blue:    0 0 20px rgba(0,212,255,0.3);
    --glow-red:     0 0 20px rgba(255,45,85,0.4);
    --glow-green:   0 0 20px rgba(0,255,136,0.3);
}

/* ── App Background ── */
.stApp {
    background: var(--bg-dark) !important;
    background-image:
        radial-gradient(ellipse at 10% 0%, rgba(0,212,255,0.04) 0%, transparent 50%),
        radial-gradient(ellipse at 90% 100%, rgba(168,85,247,0.04) 0%, transparent 50%) !important;
    font-family: 'Exo 2', sans-serif !important;
}

/* ── Hide Streamlit Branding ── */
#MainMenu, footer, header {visibility: hidden;}
.block-container {padding-top: 1.5rem !important;}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: var(--bg-panel) !important;
    border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] * {
    color: var(--text-primary) !important;
    font-family: 'Exo 2', sans-serif !important;
}

/* ── Metric Cards ── */
div[data-testid="metric-container"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    padding: 20px !important;
    position: relative;
    overflow: hidden;
}
div[data-testid="metric-container"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--accent-blue), var(--accent-purple));
}
div[data-testid="metric-container"] label {
    color: var(--text-muted) !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: var(--accent-blue) !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 2.2rem !important;
    font-weight: 700 !important;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #0f2744, #1a3a6b) !important;
    color: var(--accent-blue) !important;
    border: 1px solid var(--accent-blue) !important;
    border-radius: 8px !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    transition: all 0.25s ease !important;
    box-shadow: 0 0 15px rgba(0,212,255,0.15) !important;
}
.stButton > button:hover {
    box-shadow: var(--glow-blue) !important;
    transform: translateY(-1px) !important;
}

/* ── DataFrames ── */
.stDataFrame, .dataframe {
    background: var(--bg-card) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.82rem !important;
}

/* ── Selectbox / Inputs ── */
.stSelectbox > div > div,
.stTextInput > div > div > input,
.stNumberInput > div > div > input {
    background: var(--bg-card) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    font-family: 'Exo 2', sans-serif !important;
}

/* ── Divider ── */
hr {border-color: var(--border) !important;}

/* ── Custom Alert Boxes ── */
.theft-alert {
    background: linear-gradient(135deg, rgba(255,45,85,0.12), rgba(255,45,85,0.05));
    border: 1.5px solid var(--accent-red);
    border-radius: 12px;
    padding: 18px 22px;
    margin: 10px 0;
    box-shadow: var(--glow-red);
    animation: pulse-red 2s infinite;
}
@keyframes pulse-red {
    0%, 100% { box-shadow: 0 0 15px rgba(255,45,85,0.3); }
    50%       { box-shadow: 0 0 30px rgba(255,45,85,0.6); }
}
.theft-alert h4 { color: var(--accent-red) !important; font-family: 'Rajdhani'; margin:0 0 8px 0; font-size:1.1rem; }
.theft-alert p  { color: #ffb3c1 !important; margin: 3px 0; font-size:0.88rem; font-family:'Share Tech Mono'; }

.normal-status {
    background: linear-gradient(135deg, rgba(0,255,136,0.08), rgba(0,255,136,0.02));
    border: 1.5px solid var(--accent-green);
    border-radius: 12px;
    padding: 18px 22px;
    margin: 10px 0;
    box-shadow: var(--glow-green);
}
.normal-status h4 { color: var(--accent-green) !important; font-family:'Rajdhani'; margin:0; }

/* ── Section Headers ── */
.section-header {
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.35rem;
    font-weight: 700;
    color: var(--accent-blue);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    border-bottom: 1px solid var(--border);
    padding-bottom: 8px;
    margin: 24px 0 16px 0;
    display: flex;
    align-items: center;
    gap: 10px;
}

/* ── Status Badge ── */
.badge {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 20px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.08em;
}
.badge-online  { background: rgba(0,255,136,0.15); color: #00ff88; border:1px solid #00ff88; }
.badge-offline { background: rgba(255,45,85,0.15);  color: #ff2d55; border:1px solid #ff2d55; }
.badge-on      { background: rgba(0,212,255,0.15);  color: #00d4ff; border:1px solid #00d4ff; }
.badge-off     { background: rgba(107,122,153,0.2); color: #6b7a99; border:1px solid #6b7a99; }
.badge-theft   { background: rgba(255,45,85,0.2);   color: #ff2d55; border:1px solid #ff2d55; }

/* ── Hero Title ── */
.hero-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 2.4rem;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: 0.06em;
    line-height: 1.1;
}
.hero-title span { color: var(--accent-blue); }
.hero-sub {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.78rem;
    color: var(--text-muted);
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-top: 4px;
}

/* ── Relay Card ── */
.relay-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 22px;
    text-align: center;
}
.relay-indicator {
    width: 80px; height: 80px;
    border-radius: 50%;
    margin: 12px auto;
    display: flex; align-items: center; justify-content: center;
    font-size: 2rem;
}
.relay-on  { background: rgba(0,255,136,0.12); border: 3px solid #00ff88; box-shadow: 0 0 25px rgba(0,255,136,0.4); }
.relay-off { background: rgba(107,122,153,0.1); border: 3px solid #6b7a99; }

/* ── Plotly container borders ── */
.js-plotly-plot { border-radius: 12px !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: var(--bg-dark); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  FIREBASE INITIALISATION
# ─────────────────────────────────────────────
FIREBASE_DB_URL = "https://smart-electricity-theft-d-default-rtdb.firebaseio.com/"

def init_firebase():
    """
    Initialises the Firebase Admin SDK once per session.
    To authenticate, place your serviceAccountKey.json in the same
    directory as this file, OR set GOOGLE_APPLICATION_CREDENTIALS.
    For testing without credentials, the dashboard falls back to
    anonymous/mock data so the UI can still be demonstrated.
    """
    if not firebase_admin._apps:
        key_path = "serviceAccountKey.json"
        if os.path.exists(key_path):
            cred = credentials.Certificate("serviceAccountKey.json")
            firebase_admin.initialize_app(cred, {"databaseURL": 'https://electricitytheft-70724-default-rtdb.firebaseio.com/'})
            return True
        else:
            # Try Application Default Credentials (GCP / env var)
            try:
                cred = credentials.ApplicationDefault()
                firebase_admin.initialize_app(cred, {"databaseURL": 'https://electricitytheft-70724-default-rtdb.firebaseio.com/'})
                return True
            except Exception:
                return False   # No credentials found – use mock data
    return True


FIREBASE_AVAILABLE = init_firebase()


# ─────────────────────────────────────────────
#  MOCK DATA (shown when Firebase is offline)
# ─────────────────────────────────────────────
MOCK_DATA = {
    "latest": {"voltage": 230, "current": 1.8, "power": 414, "relay": "ON",  "status": "NORMAL",    "timestamp": 0},
    "alerts": {
        "alert1": {"current": 5.5, "power": 1265, "reason": "CURRENT_SPIKE",
                   "resolved": False, "timestamp": 0, "voltage": 230}
    },
    "history": {
        "sample1": {"voltage": 220, "current": 1.2, "power": 264, "relay": "ON",  "status": "NORMAL", "timestamp": 0},
        "sample2": {"voltage": 228, "current": 1.5, "power": 342, "relay": "ON",  "status": "NORMAL", "timestamp": 0},
        "sample3": {"voltage": 231, "current": 5.5, "power": 1265,"relay": "OFF", "status": "THEFT",  "timestamp": 0},
    },
    "config":   {"currentMax": 15, "currentMin": 0.2, "mismatchPercent": 30, "powerBaseline": 500},
    "commands": {"relay": "ON"},
    "system":   {"lastBoot": 0, "status": "ONLINE"},
}


# ─────────────────────────────────────────────
#  DATA FETCH HELPERS
# ─────────────────────────────────────────────
def fetch(path: str):
    """Fetch a path from Firebase; fall back to mock data on error."""
    if FIREBASE_AVAILABLE:
        try:
            return db.reference(path).get() or {}
        except Exception as e:
            st.session_state["firebase_error"] = str(e)
            return {}
    # Navigate the mock dict using the path
    keys = [k for k in path.strip("/").split("/") if k]
    node = MOCK_DATA
    for k in keys:
        if isinstance(node, dict):
            node = node.get(k, {})
        else:
            return {}
    return node if node is not None else {}


def write(path: str, value):
    """Write a value to Firebase."""
    if FIREBASE_AVAILABLE:
        try:
            db.reference(path).set(value)
            return True
        except Exception as e:
            st.error(f"Firebase write error: {e}")
            return False
    else:
        st.warning("⚠️ Firebase not connected — running in demo mode.")
        return False


# ─────────────────────────────────────────────
#  AI / ANOMALY DETECTION LOGIC
# ─────────────────────────────────────────────
def ai_analyse(latest: dict, config: dict) -> dict:
    """
    Simple rule-based anomaly engine that mimics 'AI' logic:
    1. Current spike detection
    2. Power–voltage–current mismatch (P ≠ V × I)
    3. Zero-current with relay ON (possible bypass/tamper)
    Returns dict with 'anomaly' (bool) and 'reason' (str).
    """
    voltage  = float(latest.get("voltage", 0))
    current  = float(latest.get("current", 0))
    power    = float(latest.get("power",   0))
    relay    = latest.get("relay", "ON")
    c_max    = float(config.get("currentMax",      15))
    c_min    = float(config.get("currentMin",     0.2))
    mismatch = float(config.get("mismatchPercent",  30))

    reasons = []

    # Rule 1 — Current exceeds max threshold
    if current > c_max:
        reasons.append(f"Current spike: {current:.2f} A > {c_max} A limit")

    # Rule 2 — Power mismatch  |P - V*I| / P > threshold
    expected_power = voltage * current
    if power > 0 and abs(power - expected_power) / max(power, 1) * 100 > mismatch:
        reasons.append(
            f"Power mismatch: measured {power:.0f}W vs expected {expected_power:.0f}W "
            f"({abs(power-expected_power)/max(power,1)*100:.1f}% deviation)"
        )

    # Rule 3 — Relay ON but near-zero current (possible line bypass)
    if relay == "ON" and 0 < current < float(c_min) and voltage > 100:
        reasons.append(f"Suspiciously low current ({current:.3f}A) with relay ON — possible bypass")

    return {"anomaly": len(reasons) > 0, "reasons": reasons}



# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 10px 0 20px 0;'>
        <div style='font-size:2.5rem;'>⚡</div>
        <div style='font-family:Rajdhani; font-size:1.1rem; color:#00d4ff; font-weight:700; letter-spacing:0.1em;'>
            THEFT DETECTION
        </div>
        <div style='font-family:Share Tech Mono; font-size:0.68rem; color:#6b7a99; margin-top:4px;'>
            ESP32 MONITORING SYSTEM
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Auto-refresh toggle
    auto_refresh = st.toggle("🔄 Auto-Refresh", value=True)
    refresh_interval = st.select_slider(
        "Refresh Interval",
        options=[3, 5, 10, 15, 30],
        value=5,
        format_func=lambda x: f"{x}s",
    )

    st.divider()

    # Firebase status
    fb_status = "🟢 Connected" if FIREBASE_AVAILABLE else "🔴 Demo Mode"
    st.markdown(f"**Firebase:** {fb_status}")
    if not FIREBASE_AVAILABLE:
        st.caption("Place `serviceAccountKey.json` in the same folder to connect to Firebase.")

    st.divider()

    # Config display
    config = fetch("/config")
    st.markdown("**⚙️ Thresholds**")
    st.markdown(f"""
    <div style='font-family:Share Tech Mono; font-size:0.78rem; color:#6b7a99; line-height:1.9;'>
    Current Max : <span style='color:#00d4ff'>{config.get('currentMax', '—')} A</span><br>
    Current Min : <span style='color:#00d4ff'>{config.get('currentMin', '—')} A</span><br>
    Mismatch    : <span style='color:#00d4ff'>{config.get('mismatchPercent', '—')} %</span><br>
    Pwr Baseline: <span style='color:#00d4ff'>{config.get('powerBaseline', '—')} W</span>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Last refreshed
    st.caption(f"🕐 Last update: {datetime.now().strftime('%H:%M:%S')}")


# ─────────────────────────────────────────────
#  MAIN CONTENT
# ─────────────────────────────────────────────

# ── Hero Header ──────────────────────────────
col_title, col_sys = st.columns([3, 1])
with col_title:
    system_info = fetch("/system")
    sys_status  = system_info.get("status", "OFFLINE") if system_info else "OFFLINE"
    badge_cls   = "badge-online" if sys_status == "ONLINE" else "badge-offline"
    st.markdown(f"""
    <div class='hero-title'>⚡ Smart <span>Electricity Theft</span><br>Detection System</div>
    <div class='hero-sub'>ESP32 • Voltage Sensor • Current Sensor • Relay Module • I²C LCD</div>
    """, unsafe_allow_html=True)

with col_sys:
    st.markdown(f"""
    <div style='text-align:right; padding-top:12px;'>
        <div style='font-family:Share Tech Mono; font-size:0.72rem; color:#6b7a99; margin-bottom:6px;'>
            SYSTEM STATUS
        </div>
        <span class='badge {badge_cls}'>{sys_status}</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ── Fetch all live data ───────────────────────
latest   = fetch("/latest")   or {}
alerts   = fetch("/alerts")   or {}
history  = fetch("/history")  or {}
commands = fetch("/commands") or {}

voltage = float(latest.get("voltage", 0))
current = float(latest.get("current", 0))
power   = float(latest.get("power",   0))
relay   = latest.get("relay", "ON")
status  = latest.get("status", "NORMAL")

led_on    = status == "THEFT"
buzzer_on = status == "THEFT"

ai_result = ai_analyse(latest, config if config else {})

# ── Theft / Normal Banner ─────────────────────
if status == "THEFT" or ai_result["anomaly"]:
    st.markdown("""
    <div class='theft-alert'>
        <h4>🚨 THEFT / ANOMALY DETECTED</h4>
        <p>Immediate inspection required. Relay may be tripped. Authorities notified.</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class='normal-status'>
        <h4>✅ System Normal — No Theft Detected</h4>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════
#  SECTION 1 — LIVE SENSOR DATA
# ══════════════════════════════════════════════
st.markdown("<div class='section-header'>📡 Live Sensor Data</div>", unsafe_allow_html=True)

m1, m2, m3, m4, m5 = st.columns(5)

with m1:
    st.metric("⚡ Voltage", f"{voltage:.1f} V",
              delta="Nominal 230V" if 210 <= voltage <= 250 else "⚠ Out of range")

with m2:
    st.metric("🔌 Current", f"{current:.2f} A",
              delta=f"Max {config.get('currentMax','—')}A" if config else None)

with m3:
    st.metric("💡 Power", f"{power:.0f} W")

with m4:
    pf = (power / (voltage * current)) if voltage > 0 and current > 0 else 0
    st.metric("📊 Power Factor", f"{min(pf, 1.0):.2f}")

with m5:
    expected = voltage * current
    mismatch_pct = abs(power - expected) / max(power, 1) * 100 if power > 0 else 0
    st.metric("⚠️ Mismatch", f"{mismatch_pct:.1f}%",
              delta="🔴 HIGH" if mismatch_pct > 30 else "🟢 OK")


# ══════════════════════════════════════════════
#  SECTION 2 — STATUS INDICATORS
# ══════════════════════════════════════════════
st.markdown("<div class='section-header'>🔴 Status Indicators</div>", unsafe_allow_html=True)

s1, s2, s3, s4 = st.columns(4)

def status_card(col, icon, label, active, active_label="ON", inactive_label="OFF", color="on"):
    badge = f"badge-{color}" if active else "badge-off"
    text  = active_label if active else inactive_label
    col.markdown(f"""
    <div style='background:#141c2e; border:1px solid #1e2a42; border-radius:12px;
                padding:20px; text-align:center;'>
        <div style='font-size:2rem; margin-bottom:8px;'>{icon}</div>
        <div style='font-family:Rajdhani; font-size:0.85rem; color:#6b7a99;
                    text-transform:uppercase; letter-spacing:0.1em;'>{label}</div>
        <span class='badge {badge}' style='margin-top:8px; display:inline-block;'>{text}</span>
    </div>
    """, unsafe_allow_html=True)

with s1:
    status_card(s1, "💡", "LED Indicator", led_on, color="on")
with s2:
    status_card(s2, "🔔", "Buzzer", buzzer_on, color="on")
with s3:
    theft = status == "THEFT"
    s3.markdown(f"""
    <div style='background:#141c2e; border:1px solid #1e2a42; border-radius:12px;
                padding:20px; text-align:center;'>
        <div style='font-size:2rem; margin-bottom:8px;'>🚨</div>
        <div style='font-family:Rajdhani; font-size:0.85rem; color:#6b7a99;
                    text-transform:uppercase; letter-spacing:0.1em;'>Theft Status</div>
        <span class='badge {"badge-theft" if theft else "badge-online"}' 
              style='margin-top:8px; display:inline-block;'>
            {"⚠ THEFT" if theft else "✓ CLEAR"}
        </span>
    </div>
    """, unsafe_allow_html=True)
with s4:
    relay_on = relay == "ON"
    s4.markdown(f"""
    <div style='background:#141c2e; border:1px solid #1e2a42; border-radius:12px;
                padding:20px; text-align:center;'>
        <div style='font-size:2rem; margin-bottom:8px;'>🔌</div>
        <div style='font-family:Rajdhani; font-size:0.85rem; color:#6b7a99;
                    text-transform:uppercase; letter-spacing:0.1em;'>Relay Module</div>
        <span class='badge {"badge-on" if relay_on else "badge-offline"}' 
              style='margin-top:8px; display:inline-block;'>
            {relay}
        </span>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════
#  SECTION 3 — ALERT PANEL
# ══════════════════════════════════════════════
st.markdown("<div class='section-header'>🚨 Active Alerts</div>", unsafe_allow_html=True)

active_alerts = {k: v for k, v in alerts.items()
                 if isinstance(v, dict) and not v.get("resolved", True)}

# Add AI-detected anomalies as a virtual alert
if ai_result["anomaly"]:
    for i, reason in enumerate(ai_result["reasons"]):
        active_alerts[f"ai_alert_{i}"] = {
            "voltage": voltage, "current": current, "power": power,
            "reason": reason, "resolved": False, "timestamp": 0, "_ai": True,
        }

if active_alerts:
    for alert_id, alert in active_alerts.items():
        ai_tag = " 🤖 AI-Detected" if alert.get("_ai") else ""
        ts = alert.get("timestamp", 0)
        ts_str = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S") if ts else "—"
        st.markdown(f"""
        <div class='theft-alert'>
            <h4>🚨 Alert: {alert.get('reason','UNKNOWN')}{ai_tag}</h4>
            <p>🔋 Voltage : {alert.get('voltage','—')} V &nbsp;|&nbsp;
               ⚡ Current : {alert.get('current','—')} A &nbsp;|&nbsp;
               💡 Power   : {alert.get('power','—')} W</p>
            <p>🕐 Timestamp : {ts_str} &nbsp;|&nbsp;
               ✅ Resolved : {'Yes' if alert.get('resolved') else 'No'}</p>
        </div>
        """, unsafe_allow_html=True)

        # Resolve button (real Firebase alerts only)
        if not alert.get("_ai") and st.button(f"Mark Resolved — {alert_id}", key=f"resolve_{alert_id}"):
            write(f"/alerts/{alert_id}/resolved", True)
            st.success("Alert marked as resolved. Refresh to update.")
else:
    st.markdown("""
    <div style='background:#141c2e; border:1px solid #1e2a42; border-radius:12px;
                padding:20px; text-align:center; color:#6b7a99; font-family:Share Tech Mono; font-size:0.85rem;'>
        ✅ No active alerts at this time.
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════
#  SECTION 4 — RELAY CONTROL
# ══════════════════════════════════════════════
st.markdown("<div class='section-header'>🔌 Relay Control</div>", unsafe_allow_html=True)

rc1, rc2, rc3 = st.columns([1, 2, 1])
with rc2:
    relay_cls = "relay-on" if relay == "ON" else "relay-off"
    relay_icon = "🟢" if relay == "ON" else "⭕"
    st.markdown(f"""
    <div class='relay-card'>
        <div style='font-family:Share Tech Mono; font-size:0.72rem; color:#6b7a99; letter-spacing:0.12em;'>
            RELAY STATUS
        </div>
        <div class='relay-indicator {relay_cls}'>{relay_icon}</div>
        <div style='font-family:Rajdhani; font-size:1.6rem; font-weight:700;
                    color:{"#00ff88" if relay=="ON" else "#6b7a99"};'>
            RELAY {relay}
        </div>
        <div style='font-family:Share Tech Mono; font-size:0.75rem; color:#6b7a99; margin-top:6px;'>
            Current command: {commands.get('relay','—')}
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("🟢 TURN RELAY ON", use_container_width=True):
            if write("/commands/relay", "ON"):
                st.success("✅ Command sent: Relay ON")
    with btn_col2:
        if st.button("🔴 TURN RELAY OFF", use_container_width=True):
            if write("/commands/relay", "OFF"):
                st.warning("⚠️ Command sent: Relay OFF")


#
# ══════════════════════════════════════════════
#  SECTION 6 — HISTORY LOG
# ══════════════════════════════════════════════
st.markdown("<div class='section-header'>🗂 History Log</div>", unsafe_allow_html=True)

if history:
    rows = []
    for k, v in history.items():
        if isinstance(v, dict):
            ts = v.get("timestamp", 0)
            ts_str = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S") if ts else "—"
            rows.append({
                "ID":        k,
                "Timestamp": ts_str,
                "Voltage (V)":  v.get("voltage", "—"),
                "Current (A)":  v.get("current", "—"),
                "Power (W)":    v.get("power",   "—"),
                "Relay":        v.get("relay",   "—"),
                "Status":       v.get("status",  "—"),
            })

    df_hist = pd.DataFrame(rows)

    def color_status(val):
        if val == "THEFT":
            return "background-color: rgba(255,45,85,0.2); color: #ff2d55; font-weight:bold;"
        elif val == "NORMAL":
            return "color: #00ff88;"
        return ""

    styled = df_hist.style.applymap(color_status, subset=["Status"])
    st.dataframe(styled, use_container_width=True, hide_index=True)
else:
    st.info("No history records found.")



# ══════════════════════════════════════════════
#  FOOTER
# ══════════════════════════════════════════════
st.markdown("---")
st.markdown("""
<div style='text-align:center; font-family:Share Tech Mono; font-size:0.72rem;
            color:#2d3a52; padding:10px 0 20px 0;'>
    SMART ELECTRICITY THEFT DETECTION SYSTEM &nbsp;|&nbsp;
    ESP32 + Firebase Realtime DB &nbsp;|&nbsp;
    Built with Streamlit &amp; Python
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  AUTO-REFRESH
# ─────────────────────────────────────────────
if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()
