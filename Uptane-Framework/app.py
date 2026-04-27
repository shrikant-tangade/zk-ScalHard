"""
app.py  –  Uptane Upstream Framework  –  Streamlit Dashboard
Run:  streamlit run app.py
"""

import streamlit as st
import json, time, sys
from uptane_engine import algo1_full_workflow

# ── Size helpers ───────────────────────────────
def _json_bytes(obj: dict) -> int:
    return len(json.dumps(obj, separators=(",", ":")).encode("utf-8"))

def _field_bytes(value) -> int:
    if isinstance(value, str):
        return len(value.encode("utf-8"))
    if isinstance(value, int):
        return len(str(value).encode("utf-8"))
    if isinstance(value, dict):
        return _json_bytes(value)
    return len(json.dumps(value).encode("utf-8"))

# ── Page config ────────────────────────────────
st.set_page_config(
    page_title="Uptane Upstream Simulator",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS – industrial/cybersecurity aesthetic ──
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700&family=Orbitron:wght@700&display=swap');

  html, body, [data-testid="stAppViewContainer"] {
      background: #080d14 !important;
      color: #c8d8e8 !important;
  }
  [data-testid="stSidebar"] {
      background: #0a1018 !important;
      border-right: 1px solid #1a3a5c !important;
  }
  h1, h2, h3 { font-family: 'Rajdhani', sans-serif !important; letter-spacing: 1px; }
  h1 { font-family: 'Orbitron', monospace !important; color: #00d4ff !important; font-size: 1.6rem !important; }
  h2 { color: #00b4d8 !important; }
  h3 { color: #90e0ef !important; }

  .metric-box {
      background: #0d1b2a;
      border: 1px solid #1e4060;
      border-left: 3px solid #00d4ff;
      border-radius: 4px;
      padding: 14px 18px;
      margin: 6px 0;
      font-family: 'Rajdhani', sans-serif;
  }
  .metric-box .label { font-size: 0.7rem; color: #5a8aaa; letter-spacing: 2px; text-transform: uppercase; }
  .metric-box .value { font-size: 1.8rem; font-weight: 700; color: #00d4ff; }
  .metric-box.green  { border-left-color: #00ff88; }
  .metric-box.green .value { color: #00ff88; }
  .metric-box.red    { border-left-color: #ff3a3a; }
  .metric-box.red .value { color: #ff3a3a; }
  .metric-box.yellow { border-left-color: #ffcc00; }
  .metric-box.yellow .value { color: #ffcc00; }

  .log-box {
      background: #060c12;
      border: 1px solid #162840;
      border-radius: 4px;
      padding: 12px 16px;
      font-family: 'Share Tech Mono', monospace;
      font-size: 0.78rem;
      color: #7fbbdd;
      height: 340px;
      overflow-y: auto;
      line-height: 1.7;
  }
  .log-box .log-ok   { color: #00ff88; }
  .log-box .log-warn { color: #ffcc00; }
  .log-box .log-err  { color: #ff3a3a; }
  .log-box .log-hdr  { color: #00d4ff; font-weight: bold; }

  .badge-ok   { background:#003322; color:#00ff88; border:1px solid #00ff88; border-radius:3px; padding:2px 8px; font-family:'Share Tech Mono'; font-size:0.75rem; }
  .badge-fail { background:#330000; color:#ff3a3a; border:1px solid #ff3a3a; border-radius:3px; padding:2px 8px; font-family:'Share Tech Mono'; font-size:0.75rem; }
  .badge-atk  { background:#332200; color:#ffcc00; border:1px solid #ffcc00; border-radius:3px; padding:2px 8px; font-family:'Share Tech Mono'; font-size:0.75rem; }

  .json-panel {
      background: #060c12;
      border: 1px solid #162840;
      border-radius: 4px;
      padding: 14px;
      font-family: 'Share Tech Mono', monospace;
      font-size: 0.74rem;
      color: #90c8e8;
      max-height: 480px;
      overflow-y: auto;
  }

  .stButton button {
      background: linear-gradient(135deg, #003a5c, #005080) !important;
      color: #00d4ff !important;
      border: 1px solid #00d4ff !important;
      font-family: 'Rajdhani', sans-serif !important;
      font-weight: 700 !important;
      letter-spacing: 2px !important;
      font-size: 1rem !important;
      padding: 10px 28px !important;
      border-radius: 3px !important;
      text-transform: uppercase !important;
      transition: all 0.2s !important;
  }
  .stButton button:hover {
      background: linear-gradient(135deg, #005080, #0070a0) !important;
      box-shadow: 0 0 16px #00d4ff55 !important;
  }

  div[data-testid="stSelectbox"] label { color: #5a8aaa !important; font-family: 'Rajdhani', sans-serif; }
  div[data-testid="stNumberInput"] label { color: #5a8aaa !important; font-family: 'Rajdhani', sans-serif; }

  .section-hdr {
      font-family: 'Rajdhani', sans-serif;
      font-weight: 700;
      font-size: 1.05rem;
      color: #00d4ff;
      border-bottom: 1px solid #1a3a5c;
      padding-bottom: 4px;
      margin: 16px 0 10px 0;
      letter-spacing: 2px;
      text-transform: uppercase;
  }
  .inv-row {
      display: flex; gap: 6px; align-items: center;
      padding: 5px 0; border-bottom: 1px solid #101e2e;
      font-family: 'Share Tech Mono', monospace; font-size: 0.73rem;
  }
  .inv-id   { color: #00d4ff; width: 140px; flex-shrink: 0; }
  .inv-key  { color: #7fbbdd; width: 120px; overflow: hidden; text-overflow: ellipsis; }
  .inv-fw   { color: #90c8a8; }
  .inv-pri  { color: #ffcc00; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="font-family:Orbitron,monospace;color:#00d4ff;font-size:1rem;letter-spacing:2px;margin-bottom:2px;">UPTANE</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-family:Rajdhani,sans-serif;color:#5a8aaa;font-size:0.8rem;letter-spacing:3px;margin-bottom:20px;">UPSTREAM FRAMEWORK v1.0</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**⚙ Simulation Parameters**")
    n_sec = st.number_input("Secondary ECUs", min_value=1, max_value=100, value=100, step=1)

    st.markdown("---")
    st.markdown("**☠ Attack Injection**")
    attack_mode = st.selectbox("Attack Scenario", [
        "None – Clean Run",
        "1 ECU Compromised",
        "3 ECUs Compromised",
        "5 ECUs Compromised",
        "Custom Indices",
    ])
    inject = []
    if attack_mode == "1 ECU Compromised":
        inject = [5]
    elif attack_mode == "3 ECUs Compromised":
        inject = [5, 22, 67]
    elif attack_mode == "5 ECUs Compromised":
        inject = [3, 14, 27, 55, 88]
    elif attack_mode == "Custom Indices":
        raw = st.text_input("Indices (comma-sep, 0-based)", "0,9,49")
        try:
            inject = [int(x.strip()) for x in raw.split(",") if x.strip()]
        except Exception:
            inject = []

    st.markdown("---")
    run = st.button("🚀  RUN SIMULATION", use_container_width=True)


# ── Header ─────────────────────────────────────
st.markdown("""
<div style="background:linear-gradient(90deg,#060c12,#0a1828,#060c12);
            border:1px solid #1a3a5c; border-radius:4px;
            padding:18px 28px; margin-bottom:20px;">
  <div style="font-family:Orbitron,monospace;color:#00d4ff;font-size:1.6rem;
              letter-spacing:3px;text-shadow:0 0 20px #00d4ff66;">
    🛡 UPTANE UPSTREAM FRAMEWORK
  </div>
  <div style="font-family:Rajdhani,sans-serif;color:#5a8aaa;letter-spacing:4px;font-size:0.85rem;margin-top:4px;">
    OTA SECURITY SIMULATION  ·  ED25519 DIGITAL SIGNATURES  ·  DIRECTOR REPOSITORY
  </div>
</div>
""", unsafe_allow_html=True)


# ── Session state ──────────────────────────────
if "results" not in st.session_state:
    st.session_state["results"] = None

if run:
    with st.spinner("Running Uptane simulation…"):
        results = algo1_full_workflow(
            n_secondary=int(n_sec),
            inject_attacks_on=inject,
        )
        st.session_state["results"] = results

results = st.session_state.get("results")

if results is None:
    st.markdown("""
    <div style="text-align:center;padding:80px 0;color:#2a5a7a;font-family:Rajdhani,sans-serif;font-size:1.1rem;letter-spacing:2px;">
        ► Configure parameters in the sidebar and press RUN SIMULATION
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Unpack ─────────────────────────────────────
vvm          = results["vvm"]
verification = results["verification"]
inv_db       = results["inventory_db"]
vin          = results["vin"]
logs         = results["logs"]
evr_results  = verification["evr_results"]
summary      = verification["summary"]


# ═══════════════════════════════════════════════
# ROW 1: Summary Metrics
# ═══════════════════════════════════════════════
st.markdown('<div class="section-hdr">📊 Verification Summary</div>', unsafe_allow_html=True)
c1, c2, c3, c4, c5 = st.columns(5)

status_cls = "green" if summary["status"] == "SUCCESS" else "red"
with c1:
    st.markdown(f'<div class="metric-box {status_cls}"><div class="label">Status</div><div class="value">{summary["status"]}</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="metric-box"><div class="label">Total ECUs</div><div class="value">{summary["total_evrs"]}</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="metric-box green"><div class="label">Passed</div><div class="value">{summary["passed"]}</div></div>', unsafe_allow_html=True)
with c4:
    fail_cls = "red" if summary["failed"] > 0 else "green"
    st.markdown(f'<div class="metric-box {fail_cls}"><div class="label">Failed / Attacked</div><div class="value">{summary["failed"]}</div></div>', unsafe_allow_html=True)
with c5:
    vvm_ok = "✓ VALID" if verification["vvm_signature_valid"] else "✗ INVALID"
    vvm_cls = "green" if verification["vvm_signature_valid"] else "red"
    st.markdown(f'<div class="metric-box {vvm_cls}"><div class="label">VVM Signature</div><div class="value" style="font-size:1.2rem;">{vvm_ok}</div></div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════
# ROW 1b: Per-ECU EVR Parameter Table + VVM Size + Timing + Key Sizes
# ═══════════════════════════════════════════════
st.markdown('<div class="section-hdr">📐 ECU Version Report (EVR) Parameters – All ECUs · Timing · Key Sizes · VVM Size</div>', unsafe_allow_html=True)

# ── Pre-compute ────────────────────────────────
all_evrs_in_vvm = vvm["payload"]["evrs"]
total_vvm_sz    = _json_bytes(vvm)
evrs_bundle_sz  = sum(_json_bytes(e) for e in all_evrs_in_vvm)
avg_evr_sz      = evrs_bundle_sz // max(len(all_evrs_in_vvm), 1)
sample_evr      = results["secondary_evrs"][0]

vtiming        = verification["timing"]
evr_gen_times  = [e["_timing"]["total_evr_gen_us"] for e in results["secondary_evrs"]]
evr_sign_times = [e["_timing"]["signing_us"]        for e in results["secondary_evrs"]]
total_evr_gen_ms = sum(evr_gen_times) / 1000
avg_sign_us      = sum(evr_sign_times) / max(len(evr_sign_times), 1)
ks = sample_evr["_key_sizes"]

# ── Row 1: 4 size cards ────────────────────────
sz1, sz2, sz3, sz4 = st.columns(4)
with sz1:
    single_sz = _json_bytes(sample_evr)
    st.markdown(
        f'<div class="metric-box"><div class="label">Single EVR Size</div>'
        f'<div class="value" style="font-size:1.4rem;">{single_sz:,} B</div>'
        f'<div style="font-size:0.75rem;color:#5a8aaa;font-family:''Share Tech Mono'';">{single_sz/1024:.2f} KB</div></div>',
        unsafe_allow_html=True)
with sz2:
    st.markdown(
        f'<div class="metric-box"><div class="label">Avg EVR ({len(all_evrs_in_vvm)} ECUs)</div>'
        f'<div class="value" style="font-size:1.4rem;">{avg_evr_sz:,} B</div>'
        f'<div style="font-size:0.75rem;color:#5a8aaa;font-family:''Share Tech Mono'';">{avg_evr_sz/1024:.2f} KB</div></div>',
        unsafe_allow_html=True)
with sz3:
    st.markdown(
        f'<div class="metric-box yellow"><div class="label">All EVRs Bundle</div>'
        f'<div class="value" style="font-size:1.4rem;">{evrs_bundle_sz:,} B</div>'
        f'<div style="font-size:0.75rem;color:#5a8aaa;font-family:''Share Tech Mono'';">{evrs_bundle_sz/1024:.2f} KB</div></div>',
        unsafe_allow_html=True)
with sz4:
    st.markdown(
        f'<div class="metric-box green"><div class="label">Total VVM Size</div>'
        f'<div class="value" style="font-size:1.4rem;">{total_vvm_sz:,} B</div>'
        f'<div style="font-size:0.75rem;color:#5a8aaa;font-family:''Share Tech Mono'';">{total_vvm_sz/1024:.2f} KB</div></div>',
        unsafe_allow_html=True)

# ── Simulation config info bar ────────────────
sim_cfg = results.get("sim_config", {})
evr_hr  = sim_cfg.get("evr_hash_rounds", "?")
vvm_hr  = sim_cfg.get("vvm_hash_rounds", "?")
ver_r   = sim_cfg.get("verify_rounds",   "?")
vvm_t   = vvm["_timing"]
total_verify_ms = vtiming["total_algo4_us"] / 1000
avg_verify      = vtiming["avg_evr_verify_us"]

st.markdown(
    f'''<div style="background:#060e18;border:1px solid #1a3a5c;border-left:3px solid #ff9944;
    border-radius:4px;padding:8px 16px;margin-bottom:8px;font-family:Rajdhani,sans-serif;font-size:0.82rem;
    color:#c8d8e8;display:flex;gap:32px;flex-wrap:wrap;">
    <span>⚙ <b style="color:#ff9944;">EVR Hash Rounds:</b> {evr_hr}× SHA-256 per ECU
    <span style="color:#5a8aaa;"> — models embedded key-stretch / integrity chain</span></span>
    <span>⚙ <b style="color:#a060ff;">VVM Hash Rounds:</b> {vvm_hr}× SHA-256 on full manifest</span>
    <span>⚙ <b style="color:#60c0ff;">Verify Rounds:</b> {ver_r}× redundant sig checks at Director
    <span style="color:#5a8aaa;"> — models strict OTA server cross-check policy</span></span>
    </div>''', unsafe_allow_html=True)

# ── Row 2: 4 timing cards ──────────────────────
tm1, tm2, tm3, tm4 = st.columns(4)
with tm1:
    avg_gen_us = sum(evr_gen_times) / max(len(evr_gen_times), 1)
    st.markdown(
        f'<div class="metric-box" style="border-left-color:#ff9944;">'
        f'<div class="label">Total EVR Creation ({len(evr_gen_times)} ECUs)</div>'
        f'<div class="value" style="font-size:1.4rem;color:#ff9944;">{total_evr_gen_ms:.1f} ms</div>'
        f'<div style="font-size:0.75rem;color:#5a8aaa;font-family:''Share Tech Mono'';">avg {avg_gen_us:.0f} µs/ECU · {evr_hr}× hash rounds</div></div>',
        unsafe_allow_html=True)
with tm2:
    avg_hash_us = sum(e["_timing"]["payload_hash_us"] for e in results["secondary_evrs"]) / max(len(results["secondary_evrs"]),1)
    st.markdown(
        f'<div class="metric-box" style="border-left-color:#ff9944;">'
        f'<div class="label">Avg EVR Hash Time</div>'
        f'<div class="value" style="font-size:1.4rem;color:#ff9944;">{avg_hash_us:.0f} µs</div>'
        f'<div style="font-size:0.75rem;color:#5a8aaa;font-family:''Share Tech Mono'';">{evr_hr}× SHA-256 · per ECU</div></div>',
        unsafe_allow_html=True)
with tm3:
    st.markdown(
        f'<div class="metric-box yellow">'
        f'<div class="label">Avg EVR Sign Time</div>'
        f'<div class="value" style="font-size:1.4rem;">{avg_sign_us:.0f} µs</div>'
        f'<div style="font-size:0.75rem;color:#5a8aaa;font-family:''Share Tech Mono'';">Ed25519 per ECU · VVM sign {vvm_t["vvm_signing_us"]:.0f} µs</div></div>',
        unsafe_allow_html=True)
with tm4:
    st.markdown(
        f'<div class="metric-box green">'
        f'<div class="label">Total Sig Verification</div>'
        f'<div class="value" style="font-size:1.4rem;">{total_verify_ms:.1f} ms</div>'
        f'<div style="font-size:0.75rem;color:#5a8aaa;font-family:''Share Tech Mono'';">avg {avg_verify:.0f} µs/ECU · {ver_r}× rounds each</div></div>',
        unsafe_allow_html=True)

# ── Row 3: 4 key size cards ────────────────────
st.markdown('<div style="margin-top:4px;font-family:Rajdhani,sans-serif;font-size:0.7rem;color:#00d4ff;letter-spacing:2px;">🔑 KEY SIZE ANALYSIS – Ed25519 / Curve25519</div>', unsafe_allow_html=True)
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(
        f'<div class="metric-box" style="border-left-color:#a060ff;">'
        f'<div class="label">Private Key</div>'
        f'<div class="value" style="font-size:1.4rem;color:#a060ff;">{ks["private_key_bits"]} bits</div>'
        f'<div style="font-size:0.75rem;color:#5a8aaa;font-family:''Share Tech Mono'';">{ks["private_key_bytes"]} bytes · {ks["algorithm"]}</div></div>',
        unsafe_allow_html=True)
with k2:
    st.markdown(
        f'<div class="metric-box" style="border-left-color:#60c0ff;">'
        f'<div class="label">Public Key</div>'
        f'<div class="value" style="font-size:1.4rem;color:#60c0ff;">{ks["public_key_bits"]} bits</div>'
        f'<div style="font-size:0.75rem;color:#5a8aaa;font-family:''Share Tech Mono'';">{ks["public_key_bytes"]} bytes · {ks["curve"]}</div></div>',
        unsafe_allow_html=True)
with k3:
    st.markdown(
        f'<div class="metric-box" style="border-left-color:#ff8844;">'
        f'<div class="label">Signature Size</div>'
        f'<div class="value" style="font-size:1.4rem;color:#ff8844;">{ks["signature_bits"]} bits</div>'
        f'<div style="font-size:0.75rem;color:#5a8aaa;font-family:''Share Tech Mono'';">{ks["signature_bytes"]} bytes · fixed length</div></div>',
        unsafe_allow_html=True)
with k4:
    total_key_overhead = (ks["public_key_bytes"] + ks["signature_bytes"]) * len(all_evrs_in_vvm)
    st.markdown(
        f'<div class="metric-box" style="border-left-color:#ffcc00;">'
        f'<div class="label">Total Crypto Overhead</div>'
        f'<div class="value" style="font-size:1.4rem;color:#ffcc00;">{total_key_overhead:,} B</div>'
        f'<div style="font-size:0.75rem;color:#5a8aaa;font-family:''Share Tech Mono'';">(pubkey+sig) × {len(all_evrs_in_vvm)} ECUs</div></div>',
        unsafe_allow_html=True)

# ── Per-ECU full table ─────────────────────────
st.markdown('<div style="margin-top:10px;"></div>', unsafe_allow_html=True)
verify_time_map = {r["ecu_id"]: r.get("verify_us", 0) for r in verification["evr_results"]}

CW = {
    "ecu_id":"108px","key_id":"108px","filename":"170px",
    "length":"68px","hash":"106px","version":"62px",
    "nonce":"88px","timestamp":"126px","attack":"62px",
    "evr_sz":"68px","gen_us":"76px","sign_us":"72px","verify_us":"76px",
}

def _th(label, w, color="#00d4ff"):
    return (f'<span style="width:{w};flex-shrink:0;color:{color};font-family:Rajdhani,sans-serif;'
            f'font-size:0.65rem;letter-spacing:1px;font-weight:700;overflow:hidden;text-overflow:ellipsis;'
            f'white-space:nowrap;">{label}</span>')

def _td(val, w, color="#c8d8e8", bold=False):
    fw = "font-weight:700;" if bold else ""
    return (f'<span style="width:{w};flex-shrink:0;color:{color};font-family:Share Tech Mono,monospace;'
            f'font-size:0.65rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;{fw}">{val}</span>')

tbl_header = (
    '<div style="display:flex;gap:3px;padding:5px 0 5px 6px;border-bottom:2px solid #1a4060;background:#0a1828;position:sticky;top:0;z-index:10;">'
    + _th("ECU ID",CW["ecu_id"]) + _th("KEY ID",CW["key_id"])
    + _th("FW FILENAME",CW["filename"]) + _th("FW LENGTH",CW["length"],"#90c8e8")
    + _th("FW HASH",CW["hash"],"#90c8e8") + _th("VERSION",CW["version"],"#90c8e8")
    + _th("NONCE",CW["nonce"],"#a0b8d0") + _th("TIMESTAMP",CW["timestamp"],"#a0b8d0")
    + _th("ATK",CW["attack"],"#ffcc00") + _th("EVR SIZE",CW["evr_sz"],"#00ff88")
    + _th(f"GEN µs ({evr_hr}h)",CW["gen_us"],"#ff9944") + _th("SIGN µs",CW["sign_us"],"#a060ff")
    + _th(f"VERIFY µs ({ver_r}r)",CW["verify_us"],"#60c0ff") + '</div>'
)

tbl_rows = ""
for evr in all_evrs_in_vvm:
    p = evr["payload"]; sa = evr["signature_attr"]; img = p["image"]
    ecu_id  = p["ecu_id"]; key_id = sa["public_key_id"]
    fname   = img["filename"]; flength = f'{img["length"]:,}'
    fhash   = img["hash"][:13]+"…"; version = img["version"]
    nonce   = p["nonce"][:9]+"…"; ts = p["evr_time"]
    atk     = p.get("attack_flag",0); evr_sz = _json_bytes(evr)
    timing  = evr.get("_timing",{}); gen_us = timing.get("total_evr_gen_us",0)
    sign_us = timing.get("signing_us",0); ver_us = verify_time_map.get(ecu_id,0)
    is_primary = (ecu_id == results["primary"].ecu_id); atk_val = atk == 1
    row_bg   = "background:#110d00;" if atk_val else ("background:#0a1420;" if is_primary else "")
    id_color = "#ffcc00" if is_primary else "#00d4ff"
    atk_color= "#ff3a3a" if atk_val else "#234a30"
    atk_label= "⚠ YES" if atk_val else "NO"
    tbl_rows += (
        f'<div style="display:flex;gap:3px;padding:3px 0 3px 6px;border-bottom:1px solid #0d1e30;{row_bg}">'
        + _td(ecu_id,CW["ecu_id"],id_color,is_primary) + _td(key_id,CW["key_id"],"#7fbbdd")
        + _td(fname,CW["filename"],"#90c8a8") + _td(flength,CW["length"],"#c8b870")
        + _td(fhash,CW["hash"],"#5a8aaa") + _td(version,CW["version"],"#a0b090")
        + _td(nonce,CW["nonce"],"#607080") + _td(ts,CW["timestamp"],"#708090")
        + _td(atk_label,CW["attack"],atk_color,atk_val)
        + _td(f"{evr_sz} B",CW["evr_sz"],"#00ff88",True)
        + _td(f"{gen_us:.1f}",CW["gen_us"],"#ff9944") + _td(f"{sign_us:.1f}",CW["sign_us"],"#a060ff")
        + _td(f"{ver_us:.1f}",CW["verify_us"],"#60c0ff") + '</div>'
    )

vvm_p=vvm["payload"]; vvm_sa=vvm["signature_attr"]; vvm_t=vvm["_timing"]
tbl_rows += (
    f'<div style="display:flex;gap:3px;padding:5px 0 5px 6px;border-top:2px solid #2a5020;background:#0d2a0d;margin-top:4px;">'
    + _td("── VVM TOTAL ──",CW["ecu_id"],"#ffcc00",True)
    + _td(vvm_sa["public_key_id"],CW["key_id"],"#ffcc00")
    + _td(f'VIN:{vvm_p["vehicle_vin"][-6:]}',CW["filename"],"#ffcc00")
    + _td(f'{vvm_p["evr_count"]} EVRs',CW["length"],"#ffcc00")
    + _td(vvm_sa["hash_of_payload"][:13]+"…",CW["hash"],"#ffcc00")
    + _td("ed25519",CW["version"],"#ffcc00") + _td("–",CW["nonce"],"#ffcc00")
    + _td(vvm_p["vvm_time"],CW["timestamp"],"#ffcc00") + _td("–",CW["attack"],"#ffcc00")
    + _td(f"{total_vvm_sz:,} B",CW["evr_sz"],"#ffcc00",True)
    + _td(f'{vvm_t["total_vvm_gen_us"]:.1f}',CW["gen_us"],"#ff9944",True)
    + _td(f'{vvm_t["vvm_signing_us"]:.1f}',CW["sign_us"],"#a060ff",True)
    + _td(f'{vtiming["vvm_sig_verify_us"]:.1f}',CW["verify_us"],"#60c0ff",True)
    + '</div>'
)

st.markdown(
    f'<div class="log-box" style="height:400px;padding:0;overflow-x:auto;overflow-y:auto;">{tbl_header}{tbl_rows}</div>',
    unsafe_allow_html=True
)

st.markdown("""
<div style="display:flex;gap:18px;flex-wrap:wrap;margin-top:6px;font-family:Rajdhani,sans-serif;font-size:0.76rem;color:#5a8aaa;letter-spacing:1px;">
  <span><span style="color:#00d4ff;">&#9632;</span> Secondary ECU</span>
  <span><span style="color:#ffcc00;">&#9632;</span> Primary ECU / VVM row</span>
  <span><span style="color:#ff3a3a;">&#9632;</span> Attack flag active</span>
  <span><span style="color:#00ff88;">&#9632;</span> EVR wire size</span>
  <span><span style="color:#ff9944;">&#9632;</span> GEN µs = total EVR creation (incl. {evr_hr}-round SHA-256 hash)</span>
  <span><span style="color:#a060ff;">&#9632;</span> SIGN µs = Ed25519 signing only</span>
  <span><span style="color:#60c0ff;">&#9632;</span> VERIFY µs = Director verification ({ver_r}-round redundant check)</span>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════
# ROW 2: Live Log | ECU Verification Table
# ═══════════════════════════════════════════════
st.markdown('<div class="section-hdr">🔄 Simulation Log &nbsp;&amp;&nbsp; ECU Verification Results</div>', unsafe_allow_html=True)
col_log, col_tbl = st.columns([1, 1])

with col_log:
    st.markdown("**Live Process Log**")
    def colorize(line):
        if "ATTACK" in line or "ALERT" in line:
            return f'<span class="log-warn">{line}</span>'
        if "FAILED" in line or "invalid" in line.lower() or "✗" in line:
            return f'<span class="log-err">{line}</span>'
        if "═══" in line or "───" in line:
            return f'<span class="log-hdr">{line}</span>'
        if "✓" in line or "SUCCESS" in line:
            return f'<span class="log-ok">{line}</span>'
        return line

    log_html = "<br>".join(colorize(l) for l in logs)
    st.markdown(f'<div class="log-box">{log_html}</div>', unsafe_allow_html=True)

with col_tbl:
    st.markdown("**EVR Verification per ECU**")
    def badge(status):
        if status == "PASSED":
            return '<span class="badge-ok">PASSED</span>'
        if status == "ATTACK_DETECTED":
            return '<span class="badge-atk">ATTACK</span>'
        return '<span class="badge-fail">FAILED</span>'

    rows_html = ""
    for r in evr_results:
        sig_icon  = "✓" if r["sig_valid"]      else "✗"
        hw_icon   = "✓" if r["hash_match"]     else "✗"
        fw_icon   = "✓" if r["firmware_match"] else "✗"
        rows_html += f"""
        <div class="inv-row">
          <span class="inv-id">{r['ecu_id']}</span>
          {badge(r['status'])}
          <span style="color:#5a8aaa;margin-left:8px;font-size:0.7rem;">
            SIG:{sig_icon} HASH:{hw_icon} FW:{fw_icon}
          </span>
        </div>"""

    st.markdown(f'<div class="log-box" style="height:340px;">{rows_html}</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════
# ROW 3: Inventory Database
# ═══════════════════════════════════════════════
st.markdown('<div class="section-hdr">🗄 Director Repository – Inventory Database</div>', unsafe_allow_html=True)
st.markdown(f'**VIN:** `{vin}`  &nbsp;|&nbsp;  **ECU Records:** {len(inv_db[vin]["ecus"])}')

ecus_list = list(inv_db[vin]["ecus"].values())
header = '<div class="inv-row" style="border-bottom:1px solid #1a4060;margin-bottom:4px;">' \
         '<span class="inv-id" style="color:#00d4ff;font-weight:bold;">ECU ID</span>' \
         '<span class="inv-key" style="color:#00d4ff;width:130px;">KEY ID (16-hex)</span>' \
         '<span style="color:#00d4ff;width:120px;">FIRMWARE FILE</span>' \
         '<span style="color:#00d4ff;width:80px;">VERSION</span>' \
         '<span style="color:#00d4ff;">HASH (first 24)</span>' \
         '</div>'
rows = ""
for e in ecus_list:
    pri_tag = ' <span class="inv-pri">[PRIMARY]</span>' if e["is_primary"] else ""
    rows += f"""<div class="inv-row">
      <span class="inv-id">{e['ecu_id']}{pri_tag}</span>
      <span class="inv-key" style="width:130px;">{e['public_key_id']}</span>
      <span style="color:#90c8a8;width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{e['expected_firmware_filename']}</span>
      <span style="color:#c8a870;width:80px;">{e['expected_firmware_version']}</span>
      <span style="color:#5a8aaa;">{e['expected_firmware_hash'][:24]}…</span>
    </div>"""

st.markdown(f'<div class="log-box" style="height:260px;">{header}{rows}</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════
# ROW 4: Technical Inspector
# ═══════════════════════════════════════════════
st.markdown('<div class="section-hdr">🔬 Technical Inspector – Raw JSON Structures</div>', unsafe_allow_html=True)

ti1, ti2, ti3 = st.tabs(["📦  EVR Sample (Secondary ECU)", "📋  Vehicle Version Manifest (VVM)", "🔑  Signature Attribute Blocks"])

with ti1:
    st.markdown("**Sample ECU Version Report** – first Secondary ECU (Algorithm 2 output)")
    st.markdown(f'<div class="json-panel"><pre>{json.dumps(sample_evr, indent=2)}</pre></div>', unsafe_allow_html=True)

with ti2:
    st.markdown("**Vehicle Version Manifest** – Primary ECU output (Algorithm 3)")
    # Truncate EVRs list for display sanity
    vvm_display = json.loads(json.dumps(vvm))
    full_evrs   = vvm_display["payload"]["evrs"]
    vvm_display["payload"]["evrs"] = full_evrs[:2]
    vvm_display["payload"]["_note"] = f"[…{len(full_evrs)-2} more EVRs truncated for display…]"
    st.markdown(f'<div class="json-panel"><pre>{json.dumps(vvm_display, indent=2)}</pre></div>', unsafe_allow_html=True)

with ti3:
    st.markdown("**Signature Attribute Blocks** – highlighted from EVR and VVM")
    sig_blocks = {
        "EVR_signature_attr_block (Algorithm 2 – Step 8)":
            results["secondary_evrs"][0]["signature_attr"],
        "VVM_signature_attr_block (Algorithm 3 – Step 6)":
            vvm["signature_attr"],
    }
    if inject:
        attacked_idx = inject[0] if inject[0] < len(results["secondary_evrs"]) else 0
        sig_blocks[f"ATTACKED ECU signature_attr (index {attacked_idx})"] = \
            results["secondary_evrs"][attacked_idx]["signature_attr"]

    st.markdown(f'<div class="json-panel"><pre>{json.dumps(sig_blocks, indent=2)}</pre></div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="margin-top:12px;padding:10px 14px;background:#0d1b0d;border:1px solid #1a4a1a;
                border-radius:4px;font-family:Rajdhani,sans-serif;font-size:0.85rem;color:#70b870;">
      <b>Signature Block Fields:</b><br>
      <code>public_key_id</code>  — 16-hex shortened key identifier stored in Inventory DB<br>
      <code>public_key_hex</code> — Full 32-byte Ed25519 public key (hex) for signature verification<br>
      <code>signing_method</code> — Algorithm used: <b>ed25519</b><br>
      <code>hash_function</code>  — Digest algorithm: <b>sha256</b><br>
      <code>hash_of_payload</code>— SHA-256 digest of the JSON-serialised payload<br>
      <code>signature</code>      — Base-64 encoded Ed25519 signature over the payload hash
    </div>
    """, unsafe_allow_html=True)


# ── Footer ─────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center;font-family:Rajdhani,sans-serif;font-size:0.75rem;
            color:#2a4a6a;letter-spacing:2px;padding:8px 0;">
  UPTANE UPSTREAM FRAMEWORK SIMULATION  ·  Ed25519 / SHA-256  ·  101 ECUs  ·  IEEE Conference Paper Implementation
</div>
""", unsafe_allow_html=True)
