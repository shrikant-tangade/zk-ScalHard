"""
uptane_engine.py
Uptane Upstream Framework – Core Simulation Engine
Implements Algorithms 1-4 with realistic ECU workload simulation:
  - EVR creation includes multi-round SHA-256 (models embedded key-stretching)
  - Signature verification includes DB key reconstruction + hash chain
  - All timing is measured with perf_counter for microsecond precision
"""

import os, json, hashlib, time, secrets, datetime
from dataclasses import dataclass
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey,
)
from cryptography.hazmat.primitives.serialization import (
    Encoding, PublicFormat, PrivateFormat, NoEncryption,
)
from cryptography.exceptions import InvalidSignature
import base64

# ─────────────────────────────────────────────────────────────
# Simulation realism constants
# Tune these to control how long operations take,
# modelling a real constrained automotive ECU / OTA server.
# ─────────────────────────────────────────────────────────────
# Number of SHA-256 rounds during EVR payload hashing
# (models PBKDF / firmware integrity chain on embedded MCU)
EVR_HASH_ROUNDS = 200

# Number of times signature is re-verified at Director
# (models redundant cross-check policy on OTA server)
VERIFY_ROUNDS = 15

# Extra hash iterations during VVM payload hashing
# (larger payload – models Director's workload on full manifest)
VVM_HASH_ROUNDS = 400

# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode()

def _sha256(data) -> str:
    if isinstance(data, str):
        data = data.encode()
    return hashlib.sha256(data).hexdigest()

def _sha256_rounds(data, rounds: int) -> str:
    """
    Iterated SHA-256 — models key-stretching / integrity chain
    on a resource-constrained ECU.
    Round 1  : SHA-256(raw payload)
    Round N  : SHA-256(prev_digest || raw_payload)
    Returns final hex digest.
    """
    if isinstance(data, str):
        data = data.encode()
    digest = hashlib.sha256(data).digest()
    for _ in range(rounds - 1):
        digest = hashlib.sha256(digest + data).digest()
    return digest.hex()

def _now_iso() -> str:
    return datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"

# ─────────────────────────────────────────────────────────────
# Key pair
# ─────────────────────────────────────────────────────────────

@dataclass
class KeyPair:
    private_key: Ed25519PrivateKey
    public_key:  Ed25519PublicKey
    public_key_id:  str
    public_key_hex: str

    @classmethod
    def generate(cls) -> "KeyPair":
        priv      = Ed25519PrivateKey.generate()
        pub       = priv.public_key()
        pub_bytes = pub.public_bytes(Encoding.Raw, PublicFormat.Raw)
        pub_hex   = pub_bytes.hex()
        return cls(priv, pub, pub_hex[:16], pub_hex)

    def sign(self, payload_hash: str) -> str:
        return _b64(self.private_key.sign(payload_hash.encode()))

    def key_sizes(self) -> dict:
        priv_raw = self.private_key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
        pub_raw  = bytes.fromhex(self.public_key_hex)
        return {
            "algorithm":         "Ed25519",
            "curve":             "Curve25519",
            "private_key_bytes": len(priv_raw),
            "private_key_bits":  len(priv_raw) * 8,
            "public_key_bytes":  len(pub_raw),
            "public_key_bits":   len(pub_raw) * 8,
            "signature_bytes":   64,
            "signature_bits":    512,
        }


def verify_signature_from_hex(pub_hex: str, payload_hash: str, sig_b64: str,
                               rounds: int = 1) -> bool:
    """
    Verify Ed25519 signature.
    rounds > 1  simulates the Director's redundant verification policy —
    each round reconstructs the public key from hex and re-verifies,
    modelling a strict OTA server that cross-checks N times before
    accepting an ECU's firmware report.
    """
    raw = bytes.fromhex(pub_hex)
    for _ in range(rounds):
        pub = Ed25519PublicKey.from_public_bytes(raw)
        try:
            sig = base64.b64decode(sig_b64)
            pub.verify(sig, payload_hash.encode())
        except InvalidSignature:
            return False
    return True

# ─────────────────────────────────────────────────────────────
# ECU
# ─────────────────────────────────────────────────────────────

@dataclass
class ECU:
    ecu_id: str
    is_primary: bool
    keypair: KeyPair
    firmware_filename: str
    firmware_version: str
    firmware_length: int
    firmware_hash: str

    @classmethod
    def create(cls, ecu_id: str, is_primary: bool = False) -> "ECU":
        kp      = KeyPair.generate()
        fname   = f"fw_{ecu_id.replace('-','_')}_v{secrets.randbelow(5)+1}.bin"
        version = f"1.{secrets.randbelow(10)}.{secrets.randbelow(100)}"
        length  = secrets.randbelow(500_000) + 50_000
        fhash   = _sha256(fname + version)
        return cls(ecu_id, is_primary, kp, fname, version, length, fhash)

# ─────────────────────────────────────────────────────────────
# Algorithm 2 – EVR Generation  (with realistic workload)
# ─────────────────────────────────────────────────────────────

def algo2_generate_evr(ecu: ECU, inject_attack: bool = False) -> dict:
    """
    INPUT : IDecu, Vimg, Limg, Himg, PRecu, PIDecu
    OUTPUT: Signed EVR with _timing and _key_sizes

    Realistic workload:
      • Nonce   : cryptographic random (models hardware RNG)
      • Hashing : EVR_HASH_ROUNDS iterations of SHA-256
                  (models firmware integrity chain on embedded MCU)
      • Signing : single Ed25519 sign (correct — one sign per EVR)
    """
    t_total = time.perf_counter()

    # Step 1 – metadata
    ecu_id   = ecu.ecu_id
    pub_id   = ecu.keypair.public_key_id
    img_meta = {
        "filename": ecu.firmware_filename,
        "version":  ecu.firmware_version,
        "length":   ecu.firmware_length,
        "hash":     ecu.firmware_hash,
    }

    # Step 2 – attack flag
    attack_flag = 1 if inject_attack else 0

    # Step 3 – timestamp
    evr_time = _now_iso()

    # Step 4 – Nonce generation (hardware RNG simulation)
    t0 = time.perf_counter()
    nonce = secrets.token_hex(16)
    t_nonce_us = (time.perf_counter() - t0) * 1_000_000

    # Step 5 – payload assembly
    payload = {
        "ecu_id":      ecu_id,
        "image":       img_meta,
        "attack_flag": attack_flag,
        "evr_time":    evr_time,
        "nonce":       nonce,
    }

    # Step 6 – Iterated SHA-256 hash (EVR_HASH_ROUNDS rounds)
    # Models constrained ECU doing integrity chain before signing
    t0 = time.perf_counter()
    payload_json = json.dumps(payload, sort_keys=True)
    Hevr = _sha256_rounds(payload_json, EVR_HASH_ROUNDS)
    t_hash_us = (time.perf_counter() - t0) * 1_000_000

    # Step 7 – Ed25519 sign (single sign of the final hash)
    t0 = time.perf_counter()
    DSIGhevr = ecu.keypair.sign(Hevr)
    t_sign_us = (time.perf_counter() - t0) * 1_000_000

    # Step 8 – signature attribute block
    sig_attr = {
        "public_key_id":   pub_id,
        "public_key_hex":  ecu.keypair.public_key_hex,
        "signing_method":  "ed25519",
        "hash_function":   f"sha256x{EVR_HASH_ROUNDS}",
        "hash_of_payload": Hevr,
        "signature":       DSIGhevr,
    }

    t_total_us = (time.perf_counter() - t_total) * 1_000_000

    return {
        "payload":        payload,
        "signature_attr": sig_attr,
        "_timing": {
            "nonce_gen_us":     round(t_nonce_us,  2),
            "payload_hash_us":  round(t_hash_us,   2),
            "hash_rounds":      EVR_HASH_ROUNDS,
            "signing_us":       round(t_sign_us,   2),
            "total_evr_gen_us": round(t_total_us,  2),
        },
        "_key_sizes": ecu.keypair.key_sizes(),
    }

# ─────────────────────────────────────────────────────────────
# Algorithm 3 – VVM Generation
# ─────────────────────────────────────────────────────────────

def algo3_generate_vvm(primary: ECU, vin: str, all_evrs: list) -> dict:
    t_total = time.perf_counter()

    primary_evr           = algo2_generate_evr(primary)
    all_evrs_with_primary = all_evrs + [primary_evr]

    payload_vvm = {
        "vehicle_vin":     vin,
        "primary_ecu_id":  primary.ecu_id,
        "primary_ecu_pub": primary.keypair.public_key_id,
        "evr_count":       len(all_evrs_with_primary),
        "evrs":            all_evrs_with_primary,
        "vvm_time":        _now_iso(),
    }

    # VVM payload is much larger (all EVRs bundled) → more hash rounds
    t0 = time.perf_counter()
    payload_json = json.dumps(payload_vvm, sort_keys=True)
    Hpvvm = _sha256_rounds(payload_json, VVM_HASH_ROUNDS)
    t_hash_us = (time.perf_counter() - t0) * 1_000_000

    t0 = time.perf_counter()
    DSIGNhpvvm = primary.keypair.sign(Hpvvm)
    t_sign_us  = (time.perf_counter() - t0) * 1_000_000

    sig_attr_vvm = {
        "primary_ecu_id":  primary.ecu_id,
        "public_key_id":   primary.keypair.public_key_id,
        "public_key_hex":  primary.keypair.public_key_hex,
        "signing_method":  "ed25519",
        "hash_function":   f"sha256x{VVM_HASH_ROUNDS}",
        "hash_of_payload": Hpvvm,
        "signature":       DSIGNhpvvm,
    }

    t_total_us = (time.perf_counter() - t_total) * 1_000_000

    return {
        "payload":        payload_vvm,
        "signature_attr": sig_attr_vvm,
        "_timing": {
            "payload_hash_us":  round(t_hash_us,  2),
            "hash_rounds":      VVM_HASH_ROUNDS,
            "vvm_signing_us":   round(t_sign_us,  2),
            "total_vvm_gen_us": round(t_total_us, 2),
        },
        "_key_sizes": primary.keypair.key_sizes(),
    }

# ─────────────────────────────────────────────────────────────
# Algorithm 4 – Director Repository Verification
# (with realistic multi-round verification workload)
# ─────────────────────────────────────────────────────────────

def algo4_director_verify(vvm: dict, inventory_db: dict) -> dict:
    """
    Realistic workload:
      • Hash recompute : EVR_HASH_ROUNDS iterations (must match ECU's hash)
      • Sig verify     : VERIFY_ROUNDS redundant Ed25519 verifications
                         (models OTA server's strict cross-check policy)
    """
    t_algo4_start = time.perf_counter()

    result = {
        "vvm_signature_valid": False,
        "vin_found":           False,
        "evr_results":         [],
        "summary":             {},
        "timing":              {},
    }

    payload_vvm  = vvm["payload"]
    sig_attr_vvm = vvm["signature_attr"]
    vin = payload_vvm.get("vehicle_vin", "UNKNOWN")

    if vin not in inventory_db:
        result["summary"] = {"status": "FAILED", "reason": "VIN not in inventory"}
        return result
    result["vin_found"] = True
    vehicle_record = inventory_db[vin]

    # ── VVM signature verification ───────────────
    t0 = time.perf_counter()
    primary_pub_hex = sig_attr_vvm["public_key_hex"]
    Hpvvm           = sig_attr_vvm["hash_of_payload"]
    DSIGNhpvvm      = sig_attr_vvm["signature"]
    payload_json    = json.dumps(payload_vvm, sort_keys=True)
    # Recompute with same rounds used during VVM generation
    computed_hash   = _sha256_rounds(payload_json, VVM_HASH_ROUNDS)
    hash_match      = (computed_hash == Hpvvm)
    vvm_sig_valid   = verify_signature_from_hex(
        primary_pub_hex, Hpvvm, DSIGNhpvvm, rounds=VERIFY_ROUNDS
    )
    t_vvm_verify_us = (time.perf_counter() - t0) * 1_000_000

    result["vvm_signature_valid"] = vvm_sig_valid and hash_match
    result["timing"]["vvm_sig_verify_us"] = round(t_vvm_verify_us, 2)

    if not result["vvm_signature_valid"]:
        result["summary"] = {"status": "FAILED", "reason": "VVM signature invalid"}
        return result

    # ── Per-ECU EVR verification ─────────────────
    evrs = payload_vvm.get("evrs", [])
    passed = 0
    total_evr_verify_us = 0.0

    for evr in evrs:
        ecu_payload  = evr["payload"]
        ecu_sig_attr = evr["signature_attr"]
        ecu_id       = ecu_payload["ecu_id"]

        db_record = vehicle_record["ecus"].get(ecu_id)
        if not db_record:
            result["evr_results"].append({
                "ecu_id": ecu_id, "status": "FAILED",
                "reason": "ECU not in inventory DB", "verify_us": 0,
            })
            continue

        t0 = time.perf_counter()

        # Recompute hash with same rounds used during EVR generation
        ep_json    = json.dumps(ecu_payload, sort_keys=True)
        computed_h = _sha256_rounds(ep_json, EVR_HASH_ROUNDS)
        stored_h   = ecu_sig_attr["hash_of_payload"]
        hash_ok    = (computed_h == stored_h)

        # Multi-round signature verification (VERIFY_ROUNDS)
        db_pub_hex = db_record["public_key_hex"]
        sig_ok     = verify_signature_from_hex(
            db_pub_hex, stored_h, ecu_sig_attr["signature"], rounds=VERIFY_ROUNDS
        )

        # Firmware metadata check
        fw_ok = (
            ecu_payload["image"]["hash"]     == db_record["expected_firmware_hash"] and
            ecu_payload["image"]["filename"] == db_record["expected_firmware_filename"]
        )

        t_verify_us = (time.perf_counter() - t0) * 1_000_000
        total_evr_verify_us += t_verify_us

        attack     = ecu_payload.get("attack_flag", 0) == 1
        evr_status = "PASSED" if (hash_ok and sig_ok) else "FAILED"
        if attack:
            evr_status = "ATTACK_DETECTED"
        if evr_status == "PASSED":
            passed += 1

        result["evr_results"].append({
            "ecu_id":         ecu_id,
            "status":         evr_status,
            "hash_match":     hash_ok,
            "sig_valid":      sig_ok,
            "firmware_match": fw_ok,
            "attack_flag":    attack,
            "nonce":          ecu_payload.get("nonce", ""),
            "verify_us":      round(t_verify_us, 2),
            "verify_rounds":  VERIFY_ROUNDS,
        })

    t_algo4_total_us = (time.perf_counter() - t_algo4_start) * 1_000_000
    failed = len(evrs) - passed

    result["timing"]["total_evr_verify_us"] = round(total_evr_verify_us, 2)
    result["timing"]["total_algo4_us"]      = round(t_algo4_total_us, 2)
    result["timing"]["avg_evr_verify_us"]   = round(total_evr_verify_us / max(len(evrs), 1), 2)
    result["timing"]["verify_rounds"]       = VERIFY_ROUNDS

    result["summary"] = {
        "status":     "SUCCESS" if failed == 0 else "PARTIAL_FAILURE",
        "total_evrs": len(evrs),
        "passed":     passed,
        "failed":     failed,
        "vin":        vin,
    }
    return result

# ─────────────────────────────────────────────────────────────
# Algorithm 1 – Full Workflow Orchestrator
# ─────────────────────────────────────────────────────────────

def algo1_full_workflow(
    n_secondary: int = 100,
    inject_attacks_on=None,
    log_cb=None,
) -> dict:
    inject_attacks_on = inject_attacks_on or []
    logs = []

    def log(msg: str):
        ts = datetime.datetime.utcnow().strftime("%H:%M:%S.%f")[:-3]
        entry = f"[{ts}] {msg}"
        logs.append(entry)
        if log_cb:
            log_cb(entry)

    log("═══ UPTANE UPSTREAM SIMULATION STARTED ═══")
    log(f"Initializing 1 Primary + {n_secondary} Secondary ECUs …")
    log(f"EVR hash rounds    : {EVR_HASH_ROUNDS}  (SHA-256 iterations per ECU)")
    log(f"VVM hash rounds    : {VVM_HASH_ROUNDS}  (SHA-256 iterations for manifest)")
    log(f"Verify rounds      : {VERIFY_ROUNDS}  (redundant signature checks at Director)")

    VIN         = "1HGBH41JXMN" + secrets.token_hex(3).upper()
    primary     = ECU.create("PRIMARY-ECU-001", is_primary=True)
    secondaries = [ECU.create(f"ECU-{i+1:03d}") for i in range(n_secondary)]
    log(f"VIN assigned: {VIN}")
    log(f"Key pairs generated for all {n_secondary+1} ECUs (Ed25519/Curve25519, 256-bit)")

    log("Building Director Repository Inventory Database …")
    inventory_db = {VIN: {"vin": VIN, "ecus": {}}}
    for ecu in [primary] + secondaries:
        inventory_db[VIN]["ecus"][ecu.ecu_id] = {
            "ecu_id":                     ecu.ecu_id,
            "is_primary":                 ecu.is_primary,
            "public_key_id":              ecu.keypair.public_key_id,
            "public_key_hex":             ecu.keypair.public_key_hex,
            "signing_method":             "ed25519",
            "expected_firmware_filename": ecu.firmware_filename,
            "expected_firmware_version":  ecu.firmware_version,
            "expected_firmware_hash":     ecu.firmware_hash,
            "expected_firmware_length":   ecu.firmware_length,
        }
    log(f"Inventory DB populated: {len(inventory_db[VIN]['ecus'])} ECU records")

    # ── Algorithm 2: EVR generation ──────────────
    log("─── STEP 1: Secondary ECUs generating EVRs (Algorithm 2) ───")
    t_evr_all = time.perf_counter()
    secondary_evrs = []
    for i, ecu in enumerate(secondaries):
        inject = i in inject_attacks_on
        evr    = algo2_generate_evr(ecu, inject_attack=inject)
        secondary_evrs.append(evr)
        tm     = evr["_timing"]
        if inject:
            log(f"  [ATTACK] {ecu.ecu_id} injected | hash={tm['payload_hash_us']:.0f}µs sign={tm['signing_us']:.0f}µs total={tm['total_evr_gen_us']:.0f}µs")
        elif i % 20 == 0:
            log(f"  [{i+1:3d}/{n_secondary}] {ecu.ecu_id} ✓ | hash={tm['payload_hash_us']:.0f}µs sign={tm['signing_us']:.0f}µs total={tm['total_evr_gen_us']:.0f}µs")
    t_evr_all_ms = (time.perf_counter() - t_evr_all) * 1000
    avg_gen = sum(e["_timing"]["total_evr_gen_us"] for e in secondary_evrs) / max(len(secondary_evrs), 1)
    log(f"All {n_secondary} EVRs generated in {t_evr_all_ms:.1f} ms  (avg {avg_gen:.0f} µs/ECU)")

    # ── Algorithm 3: VVM ─────────────────────────
    log("─── STEP 2: Primary ECU generating VVM (Algorithm 3) ───")
    t0  = time.perf_counter()
    vvm = algo3_generate_vvm(primary, VIN, secondary_evrs)
    t_vvm_ms = (time.perf_counter() - t0) * 1000
    vt = vvm["_timing"]
    log(f"VVM generated in {t_vvm_ms:.1f} ms — {vvm['payload']['evr_count']} EVRs bundled")
    log(f"  VVM hash ({VVM_HASH_ROUNDS} rounds): {vt['payload_hash_us']:.0f} µs  |  sign: {vt['vvm_signing_us']:.0f} µs")

    # ── Algorithm 4: Verification ─────────────────
    log("─── STEP 3: Director Repository verifying VVM (Algorithm 4) ───")
    t0           = time.perf_counter()
    verification = algo4_director_verify(vvm, inventory_db)
    elapsed_ms   = (time.perf_counter() - t0) * 1000
    vtiming      = verification["timing"]

    log(f"VVM sig verify     : {vtiming['vvm_sig_verify_us']:.0f} µs  ({VERIFY_ROUNDS} rounds)")
    log(f"All EVR verify     : {vtiming['total_evr_verify_us']/1000:.1f} ms  ({VERIFY_ROUNDS} rounds each)")
    log(f"Avg per ECU verify : {vtiming['avg_evr_verify_us']:.0f} µs")
    log(f"Total Algo4 time   : {vtiming['total_algo4_us']/1000:.1f} ms")
    log(f"EVR results        : {verification['summary']['passed']}/{verification['summary']['total_evrs']} passed")

    attacks  = [r for r in verification["evr_results"] if r["status"] == "ATTACK_DETECTED"]
    failures = [r for r in verification["evr_results"] if r["status"] == "FAILED"]
    if attacks:
        log(f"⚠ ALERT: {len(attacks)} ECU(s) ATTACK flags → {[a['ecu_id'] for a in attacks]}")
    if failures:
        log(f"✗ FAILURES: {len(failures)} EVR(s) failed")
    else:
        log("✓ All EVRs verified successfully")

    log(f"Final Status: {verification['summary']['status']}")
    log("═══ UPTANE SIMULATION COMPLETE ═══")

    return {
        "vin":            VIN,
        "primary":        primary,
        "secondaries":    secondaries,
        "inventory_db":   inventory_db,
        "secondary_evrs": secondary_evrs,
        "vvm":            vvm,
        "verification":   verification,
        "logs":           logs,
        "elapsed_ms":     round(elapsed_ms, 2),
        "t_evr_all_ms":   round(t_evr_all_ms, 2),
        "t_vvm_ms":       round(t_vvm_ms, 2),
        "sim_config": {
            "evr_hash_rounds":  EVR_HASH_ROUNDS,
            "vvm_hash_rounds":  VVM_HASH_ROUNDS,
            "verify_rounds":    VERIFY_ROUNDS,
        },
    }
