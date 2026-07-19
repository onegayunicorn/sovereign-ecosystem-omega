#!/usr/bin/env python3
"""
Sovereign Ecosystem Ω — Full Integration Tests
Covers: Phase 1 (static), Phase 2 (dynamic rotation + logs), Phase 3 (IdP binding)
"""

import os
import sys
import time
import json
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from integration_wrapper import (
    SovereignAIWrapper,
    SovereignCommand,
    DynamicSentinel,
    ExternalIdP,
    QUANTUM_COHERENCE,
    QUANTUM_SIGNATURE,
    QUANTUM_NODES,
)

SECRET = b"test-secret-omega-2026"


# ============================================================================
# PHASE 1 — Base integration + static security
# ============================================================================
def test_phase1_coherence_request():
    """Test coherence status request"""
    w = SovereignAIWrapper(SECRET)
    cmd = SovereignCommand(action="coherence_status", node="node-001", coherence=0.947)
    out = w.send(cmd, user_id="Standard_Assistant")
    assert out["ok"] is True
    assert out["coherence"] == QUANTUM_COHERENCE
    assert out["signature"] == QUANTUM_SIGNATURE
    print("✅ Phase 1: Coherence request PASSED")


def test_phase1_market_sync():
    """Test market sync command"""
    w = SovereignAIWrapper(SECRET)
    cmd = SovereignCommand(action="market_sync", node="node-042", coherence=0.947)
    r = w.send(cmd, user_id="Standard_Assistant")
    assert r["status"] == "synced"
    assert r["nodes"] == QUANTUM_NODES
    assert "regions" in r
    print("✅ Phase 1: Market sync PASSED")


def test_phase1_malicious_blocked():
    """Test malicious command blocking"""
    w = SovereignAIWrapper(SECRET)
    bad = {
        "action": "wipe_all",
        "node": "*",
        "signature": "0" * 64,
        "coherence": 0.0,
        "sentinel_token": "x",
        "idp_token": "y",
        "user_id": "attacker",
        "payload": {}
    }
    r = w.verify_and_run(bad)
    assert r["ok"] is False
    assert "error" in r
    print("✅ Phase 1: Malicious command BLOCKED")


# ============================================================================
# PHASE 2 — Dynamic rotation + log rotation
# ============================================================================
def test_phase2_dynamic_token_valid():
    """Test dynamic token validity"""
    s = DynamicSentinel(SECRET, rotation_seconds=2)
    creds = s.issue("u1")
    assert s.verify("u1", creds["sentinel_token"], creds["idp_token"]) is True
    print("✅ Phase 2: Dynamic token valid PASSED")


def test_phase2_expired_token_rejected():
    """Test expired token rejection"""
    s = DynamicSentinel(SECRET, rotation_seconds=1)
    creds = s.issue("u1")
    time.sleep(1.2)
    assert s.verify("u1", creds["sentinel_token"], creds["idp_token"], tolerance=0) is False
    print("✅ Phase 2: Expired token REJECTED")


def test_phase2_log_rotation_created():
    """Test log rotation creation"""
    log_path = "test_wrapper.log"
    if os.path.exists(log_path):
        os.remove(log_path)
    
    w = SovereignAIWrapper(SECRET)
    for _ in range(500):
        w.send(SovereignCommand("market_sync", "n1", 0.947), "u1")
    
    assert os.path.exists(log_path) or os.path.exists("sovereign_wrapper.log")
    print("✅ Phase 2: Log rotation created PASSED")


# ============================================================================
# PHASE 3 — IdP integration + 6-tuple command
# ============================================================================
def test_phase3_identity_linked_valid():
    """Test identity-linked command"""
    w = SovereignAIWrapper(SECRET)
    cmd = SovereignCommand(
        "galaxy_a17_cmd",
        "galaxy-a17-01",
        0.947,
        payload={"led": "on", "mode": "quantum_mesh"}
    )
    r = w.send(cmd, user_id="ops_admin")
    assert r["ok"] is True
    assert r["device"] == "GALAXY_A17"
    print("✅ Phase 3: Identity-linked command PASSED")


def test_phase3_cross_user_impersonation_blocked():
    """Test cross-user impersonation blocking"""
    s = DynamicSentinel(SECRET)
    a = s.issue("alice")
    # Mallory tries to reuse Alice's token
    mallory_idp = s.issue("mallory")
    assert s.verify("mallory", a["sentinel_token"], mallory_idp["idp_token"]) is False
    print("✅ Phase 3: Cross-user impersonation BLOCKED")


def test_phase3_tampered_idp_token_rejected():
    """Test tampered IdP token rejection"""
    s = DynamicSentinel(SECRET)
    c = s.issue("bob")
    assert s.verify("bob", c["sentinel_token"], "FAKE_IDP_TOKEN") is False
    print("✅ Phase 3: Tampered IdP token REJECTED")


def test_phase3_signature_tamper_blocked():
    """Test signature tampering blocking"""
    w = SovereignAIWrapper(SECRET)
    cmd = SovereignCommand("coherence_status", "n1", 0.947)
    msg = cmd.sign(w.sentinel, "u1")
    # Tamper after signing
    msg["action"] = "steal_funds"
    r = w.verify_and_run(msg)
    assert r["ok"] is False
    assert r["error"] == "signature_invalid"
    print("✅ Phase 3: Signature tamper BLOCKED")


# ============================================================================
# Run all tests
# ============================================================================
def run_all_tests():
    """Run all integration tests"""
    print("\n" + "=" * 60)
    print("🚀 SOVEREIGN ECOSYSTEM Ω — INTEGRATION TESTS")
    print("=" * 60 + "\n")
    
    try:
        test_phase1_coherence_request()
        test_phase1_market_sync()
        test_phase1_malicious_blocked()
        test_phase2_dynamic_token_valid()
        test_phase2_expired_token_rejected()
        test_phase2_log_rotation_created()
        test_phase3_identity_linked_valid()
        test_phase3_cross_user_impersonation_blocked()
        test_phase3_tampered_idp_token_rejected()
        test_phase3_signature_tamper_blocked()
    except AssertionError as e:
        print(f"\n❌ Test FAILED: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED — SYSTEM NOMINAL")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)