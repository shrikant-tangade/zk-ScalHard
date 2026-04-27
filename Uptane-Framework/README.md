# Uptane Upstream Framework Simulator

> A real-world Python simulation of the **Uptane Upstream OTA Security Framework** for automotive ECUs — implementing all 4 algorithms from the IEEE conference paper with **101 ECUs**, **Ed25519 digital signatures**, and a live **Streamlit dashboard**.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Algorithms Implemented](#algorithms-implemented)
- [Project Structure](#project-structure)
- [System Requirements](#system-requirements)
- [Ubuntu Installation](#ubuntu-installation)
- [Running the Simulation](#running-the-simulation)
- [Dashboard Features](#dashboard-features)
- [Simulation Parameters](#simulation-parameters)
- [Timing & Performance Results](#timing--performance-results)
- [Key Size Analysis](#key-size-analysis)
- [Attack Injection Scenarios](#attack-injection-scenarios)
- [Troubleshooting](#troubleshooting)

---

## Overview

This project simulates the complete **Uptane upstream vehicle update workflow** — the security protocol used by automotive OEM OTA servers to authenticate ECU firmware reports before deploying software updates.

The simulation models:
- **101 ECUs** (1 Primary + 100 Secondary) each with unique Ed25519 key pairs
- **ECU Version Report (EVR)** generation per ECU with signed payloads
- **Vehicle Version Manifest (VVM)** bundling all 101 EVRs signed by the Primary ECU
- **Director Repository verification** with multi-round redundant signature checking
- **Real timing instrumentation** — every cryptographic operation is measured in microseconds
- **Attack injection** — flag selected ECUs as compromised to simulate security incidents

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    VEHICLE (In-Car)                          │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ ECU-001  │  │ ECU-002  │  │  ECU-...  │  │ ECU-100  │   │
│  │ Ed25519  │  │ Ed25519  │  │  Ed25519  │  │ Ed25519  │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │              │              │              │          │
│       └──────────────┴──────────────┴──────────────┘         │
│                           EVRs (signed)                       │
│                              │                                │
│                    ┌─────────▼─────────┐                     │
│                    │   PRIMARY-ECU-001  │                     │
│                    │   Bundles all EVRs │                     │
│                    │   Signs VVM        │                     │
│                    └─────────┬─────────┘                     │
└──────────────────────────────┼──────────────────────────────┘
                                │ VVM (signed)
                                ▼
┌─────────────────────────────────────────────────────────────┐
│           OTA CLOUD SERVER / DIRECTOR REPOSITORY             │
│                                                              │
│  1. Decode VVM → extract VIN                                 │
│  2. Query Inventory DB for vehicle record                    │
│  3. Verify VVM signature (Primary ECU public key)            │
│  4. Verify each EVR signature (15× redundant rounds)         │
│  5. Cross-check firmware metadata vs expected values         │
│  6. Detect attack flags → alert & log                        │
│  7. Determine software updates to deploy                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Algorithms Implemented

| Algorithm | Function | Description |
|---|---|---|
| **Algorithm 1** | `algo1_full_workflow()` | Master orchestrator — runs complete update cycle |
| **Algorithm 2** | `algo2_generate_evr()` | Each ECU generates a signed EVR with iterated SHA-256 |
| **Algorithm 3** | `algo3_generate_vvm()` | Primary ECU bundles all EVRs into a signed VVM |
| **Algorithm 4** | `algo4_director_verify()` | Director verifies VVM + all 101 EVRs with redundant rounds |

### EVR Structure (Algorithm 2 output)

```json
{
  "payload": {
    "ecu_id": "ECU-001",
    "image": {
      "filename": "fw_ECU_001_v3.bin",
      "version": "1.6.9",
      "length": 510218,
      "hash": "17153d3179..."
    },
    "attack_flag": 0,
    "evr_time": "2025-01-15T10:05:54Z",
    "nonce": "4d3f5d20a1b2c3d4..."
  },
  "signature_attr": {
    "public_key_id": "8a8f5863af2c1d4e",
    "public_key_hex": "8a8f5863af2c1d4e...(64 hex chars)",
    "signing_method": "ed25519",
    "hash_function": "sha256x200",
    "hash_of_payload": "a1b2c3d4...(64 hex chars)",
    "signature": "base64_encoded_64_byte_signature"
  }
}
```

### VVM Structure (Algorithm 3 output)

```json
{
  "payload": {
    "vehicle_vin": "1HGBH41JXMN5A2B3C",
    "primary_ecu_id": "PRIMARY-ECU-001",
    "evr_count": 101,
    "evrs": [ ... all 101 EVRs ... ],
    "vvm_time": "2025-01-15T10:05:55Z"
  },
  "signature_attr": {
    "primary_ecu_id": "PRIMARY-ECU-001",
    "public_key_id": "b86dfbffec...",
    "signing_method": "ed25519",
    "hash_function": "sha256x400",
    "hash_of_payload": "...",
    "signature": "..."
  }
}
```

---

## Project Structure

```
uptane_sim/
├── uptane_engine.py     # Core simulation engine (Algorithms 1–4)
├── app.py               # Streamlit dashboard
├── launch.sh            # One-click Ubuntu launcher
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

---

## System Requirements

| Requirement | Minimum | Recommended |
|---|---|---|
| OS | Ubuntu 20.04 LTS | Ubuntu 22.04 / 24.04 LTS |
| Python | 3.9 | 3.11 / 3.12 |
| RAM | 512 MB | 1 GB |
| Disk | 200 MB | 500 MB |
| Browser | Any modern browser | Chrome / Firefox |

---

## Ubuntu Installation

### Step 1 — Update system packages

```bash
sudo apt update && sudo apt upgrade -y
```

### Step 2 — Install Python 3 and pip

```bash
sudo apt install python3 python3-pip python3-venv -y
```

Verify installation:

```bash
python3 --version
pip3 --version
```

### Step 3 — Clone or download the project

**Option A — Clone from GitHub:**
```bash
git clone https://github.com/your-username/uptane-simulation.git
cd uptane-simulation
```

**Option B — Create folder manually and place files:**
```bash
mkdir ~/uptane_sim
cd ~/uptane_sim
# Place uptane_engine.py, app.py, launch.sh, requirements.txt here
```

### Step 4 — Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 5 — Install dependencies

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install streamlit>=1.32.0 cryptography>=41.0.0
```

Verify:

```bash
python3 -c "import streamlit, cryptography; print('streamlit:', streamlit.__version__, '| cryptography:', cryptography.__version__)"
```

---

## Running the Simulation

### Option A — Launch script (recommended)

```bash
chmod +x launch.sh
bash launch.sh
```

The script automatically:
1. Checks Python version (3.9+ required)
2. Verifies all project files are present
3. Creates and activates virtual environment
4. Installs dependencies from `requirements.txt`
5. Launches Streamlit at `http://localhost:8501`

### Option B — Run Streamlit directly

```bash
source venv/bin/activate
streamlit run app.py
```

### Option C — Custom port (if 8501 is busy)

```bash
streamlit run app.py --server.port 8502
```

### Option D — Headless server (no browser auto-open)

```bash
streamlit run app.py --server.headless true --server.port 8501
```

### Access the dashboard

Open your browser and go to:

```
http://localhost:8501
```

### Stop the server

```bash
Ctrl + C
```

---

## Dashboard Features

The dashboard has **5 sections**:

### 1. Verification Summary
Live metrics after each simulation run:
- Overall status (SUCCESS / PARTIAL_FAILURE)
- Total ECUs verified
- Passed / Failed counts
- VVM signature validity

### 2. ECU Parameters & Size Analysis Panel
Full sortable table with one row per ECU containing:

| Column | Description |
|---|---|
| ECU ID | Unique identifier |
| KEY ID | 16-hex public key ID stored in Inventory DB |
| FW FILENAME | Firmware image filename |
| FW LENGTH | Firmware file size in bytes |
| FW HASH | SHA-256 hash of firmware (truncated) |
| VERSION | Firmware version string |
| NONCE | 128-bit replay-prevention nonce (truncated) |
| TIMESTAMP | EVR generation time (ISO-8601 UTC) |
| ATK FLAG | Attack indicator (⚠ YES / NO) |
| EVR SIZE | Serialised EVR wire size in bytes |
| GEN µs | Total EVR creation time (µs) |
| SIGN µs | Ed25519 signing time only (µs) |
| VERIFY µs | Director verification time (µs) |

Plus a **VVM footer row** showing manifest totals and timing.

Size metric cards:
- Single EVR size (bytes / KB)
- Average EVR size across all ECUs
- All EVRs bundle size
- Total VVM wire size

Timing metric cards:
- Total EVR creation time (all 100 secondary ECUs)
- Average hash time per ECU (200× SHA-256)
- Average signing time per ECU (Ed25519)
- Total Director verification time (15× rounds × 101 ECUs)

Key size cards:
- Private key: **256 bits / 32 bytes** (Ed25519)
- Public key: **256 bits / 32 bytes** (Curve25519)
- Signature: **512 bits / 64 bytes** (fixed-length)
- Total crypto overhead across all ECUs

### 3. Simulation Log
Colour-coded real-time trace of the simulation with per-operation timing.

### 4. ECU Verification Table
Per-ECU pass/fail with SIG / HASH / FW check icons and attack indicators.

### 5. Inventory Database
All 101 ECU records with public key IDs, firmware metadata, and expected values.

### 6. Technical Inspector (3 tabs)
- Raw JSON of a sample EVR
- Full VVM structure (truncated EVR list)
- Signature Attribute Blocks with field explanations

---

## Simulation Parameters

Tune these constants at the top of `uptane_engine.py`:

```python
# Number of SHA-256 rounds during EVR payload hashing
# (models embedded key-stretching / firmware integrity chain on constrained MCU)
EVR_HASH_ROUNDS = 200

# Number of SHA-256 rounds for VVM payload hashing
# (larger payload — models Director's workload on full manifest)
VVM_HASH_ROUNDS = 400

# Number of redundant Ed25519 verifications at Director
# (models strict OTA server cross-check policy)
VERIFY_ROUNDS = 15
```

### Effect of increasing constants

| Parameter | Value | Avg time impact |
|---|---|---|
| `EVR_HASH_ROUNDS = 100` | Lower | ~150 µs/ECU hash |
| `EVR_HASH_ROUNDS = 200` | Default | ~300 µs/ECU hash |
| `EVR_HASH_ROUNDS = 500` | Higher | ~750 µs/ECU hash |
| `VERIFY_ROUNDS = 15` | Default | ~2,200 µs/ECU verify |
| `VERIFY_ROUNDS = 30` | Higher | ~4,400 µs/ECU verify |
| `VERIFY_ROUNDS = 50` | High | ~7,300 µs/ECU verify |

---

## Timing & Performance Results

Measured on **Ubuntu 22.04 / Python 3.12 / 101 ECUs** with default parameters:

| Operation | Time | Details |
|---|---|---|
| Key pair generation (101 ECUs) | ~5 ms | Ed25519/Curve25519 |
| Avg EVR hash time | ~300 µs | 200× SHA-256 iterations |
| Avg EVR sign time | ~50 µs | Single Ed25519 sign |
| Avg EVR creation total | ~400 µs | All steps combined |
| Total EVR creation (100 ECUs) | ~22 ms | Sequential generation |
| VVM payload hash | ~30 ms | 400× SHA-256 on full manifest |
| VVM sign | ~100 µs | Ed25519 sign of VVM hash |
| Avg Director verify per ECU | ~2,200 µs | 15× redundant Ed25519 verify + hash recompute |
| Total Director verification | ~230 ms | 101 ECUs × 15 rounds |
| Total Algo4 (Director) | ~275 ms | VVM verify + all EVR verify |

> **Key insight**: Verification at the Director takes ~10× longer than signing at the ECU. This proves the security overhead cost of Uptane's redundant verification policy at the OTA cloud server — a deliberate design trade-off for stronger replay and integrity protection.

---

## Key Size Analysis

Ed25519 key parameters (all ECUs use identical key geometry):

| Key Component | Size (bytes) | Size (bits) | Format |
|---|---|---|---|
| Private key | 32 B | 256 bits | Raw scalar |
| Public key | 32 B | 256 bits | Compressed point |
| Signature | 64 B | 512 bits | (R, S) pair — fixed length |
| Public key ID | 8 B | 64 bits | First 16 hex chars of public key |

Total cryptographic overhead per ECU EVR:
- Public key (32 B) + Signature (64 B) = **96 bytes of crypto data per EVR**
- For 101 ECUs: **9,696 bytes** of pure cryptographic material inside the VVM

Comparison with RSA-2048:

| Algorithm | Private key | Public key | Signature |
|---|---|---|---|
| **Ed25519** | **32 B** | **32 B** | **64 B** |
| RSA-2048 | 1,218 B | 270 B | 256 B |
| ECDSA P-256 | 32 B | 64 B | 71 B (avg) |

Ed25519 is the optimal choice for Uptane — smallest keys, fastest operations, fixed-length signatures.

---

## Attack Injection Scenarios

Select from the sidebar in the dashboard, or pass directly to the engine:

```python
from uptane_engine import algo1_full_workflow

# Clean run
results = algo1_full_workflow(n_secondary=100)

# Inject attack flags into specific secondary ECUs (0-based index)
results = algo1_full_workflow(n_secondary=100, inject_attacks_on=[4, 19, 44])
```

Available scenarios in dashboard sidebar:
- **None – Clean Run**: all 101 ECUs pass
- **1 ECU Compromised**: index 5
- **3 ECUs Compromised**: indices 5, 22, 67
- **5 ECUs Compromised**: indices 3, 14, 27, 55, 88
- **Custom Indices**: enter any comma-separated 0-based indices

When an attack is injected, the Director flags the ECU as `ATTACK_DETECTED` (not `FAILED`) — the signature is still valid (the ECU signed legitimately) but the payload contains `attack_flag: 1`, which triggers an alert and logging at the Director.

---

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'streamlit'` | Not installed | `pip install streamlit` |
| `ModuleNotFoundError: No module named 'cryptography'` | Not installed | `pip install cryptography` |
| `externally-managed-environment` error | Ubuntu 23+ pip policy | Add `--break-system-packages` flag |
| Port 8501 already in use | Another process | `streamlit run app.py --server.port 8502` |
| `Permission denied: ./launch.sh` | Not executable | `chmod +x launch.sh` |
| Browser doesn't open automatically | Headless environment | Navigate manually to `http://localhost:8501` |
| `python3: command not found` | Python not installed | `sudo apt install python3` |
| Simulation is very slow | High round constants | Lower `EVR_HASH_ROUNDS` / `VERIFY_ROUNDS` in `uptane_engine.py` |

### Full clean reinstall

```bash
cd ~/uptane_sim
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install streamlit cryptography
streamlit run app.py
```

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| `streamlit` | >= 1.32.0 | Dashboard UI and live rendering |
| `cryptography` | >= 41.0.0 | Ed25519 key generation, signing, verification |
| `hashlib` | stdlib | SHA-256 hashing (built-in) |
| `secrets` | stdlib | Cryptographic nonce generation (built-in) |
| `json` | stdlib | Payload serialisation (built-in) |
| `time` | stdlib | Microsecond timing with `perf_counter` (built-in) |

---

## Cryptography Details

```
Algorithm   :  Ed25519 (RFC 8032)
Curve       :  Curve25519 (Montgomery / Edwards form)
Key size    :  256-bit private · 256-bit public
Signature   :  64 bytes (R, S) — deterministic, no random required
Hash        :  SHA-256 (iterated × EVR_HASH_ROUNDS for EVR payload)
Library     :  cryptography >= 41.0.0 (hazmat primitives)
Nonce       :  128-bit cryptographically random (secrets.token_hex)
```

All signatures are verified by the Director using the public key stored in the Inventory DB at registration time — never trusting the key embedded in the incoming EVR/VVM packet.

---

## Quick Command Reference

```bash
# Install everything from scratch
sudo apt update && sudo apt install python3 python3-pip python3-venv -y
cd ~/uptane_sim
python3 -m venv venv
source venv/bin/activate
pip install streamlit cryptography

# Run the simulation
streamlit run app.py

# Run with custom port
streamlit run app.py --server.port 8502

# Run using launch script
chmod +x launch.sh && bash launch.sh

# Deactivate virtual environment
deactivate

# Re-activate next session
cd ~/uptane_sim && source venv/bin/activate && streamlit run app.py
```

---

## License

This project is for academic and research purposes, implementing the Uptane upstream framework as described in the IEEE conference paper.

---

*Simulated on Ubuntu 22.04 LTS · Python 3.12 · Ed25519 / Curve25519 · 101 ECUs · Streamlit 1.56*
