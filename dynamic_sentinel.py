#!/usr/bin/env python3
"""
Dynamic Sentinel — Time-Rotating Security Layer for Sovereign Ecosystem Ω
"""

import hashlib
import hmac
import time
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

# Setup logging
_log = logging.getLogger("dynamic_sentinel")
_log.setLevel(logging.INFO)

# Quantum Constants
QUANTUM_SIGNATURE = "SOVEREIGN_Ω"
QUANTUM_PI5 = 306.01968478528146
COHERENCE_THRESHOLD = 0.947


class ExternalIdP:
    """External Identity Provider interface"""
    
    def __init__(self):
        self._users: Dict[str, str] = {}
        self._tokens: Dict[str, Dict] = {}

    def issue_token(self, user_id: str, scope: str = "openid") -> str:
        token = hashlib.sha256(f"{user_id}:{time.time_ns()}:{QUANTUM_SIGNATURE}".encode()).hexdigest()
        self._users[user_id] = token
        self._tokens[token] = {
            "user_id": user_id,
            "scope": scope,
            "issued_at": time.time(),
            "expires_at": time.time() + 3600
        }
        return token

    def validate(self, user_id: str, token: str) -> bool:
        stored = self._users.get(user_id)
        if stored != token:
            return False
        token_data = self._tokens.get(token)
        if token_data and token_data.get("expires_at", 0) < time.time():
            return False
        return True


class DynamicSentinel:
    """
    Dynamic Sentinel — Time-rotating SHA-256 tokens with identity binding
    
    Key rotation: 3600 seconds (1 hour)
    Token format: HMAC-SHA256(SOVEREIGN_Ω:slot:user_id:PI5)
    """
    
    def __init__(self, secret: bytes, rotation_seconds: int = 3600):
        self._secret = secret
        self._window = rotation_seconds
        self._idp = ExternalIdP()
        self._tokens: Dict[str, Dict] = {}

    def _slot(self, at: Optional[float] = None) -> int:
        return int((at or time.time()) // self._window)

    def _key(self, slot: int, user_id: str) -> bytes:
        base = f"{QUANTUM_SIGNATURE}:{slot}:{user_id}:{QUANTUM_PI5}".encode()
        return hmac.new(self._secret, base, hashlib.sha256).digest()

    def issue(self, user_id: str) -> Dict[str, Any]:
        slot = self._slot()
        idp_token = self._idp.issue_token(user_id)
        sentinel = hmac.new(
            self._key(slot, user_id),
            f"{user_id}:{slot}".encode(),
            hashlib.sha256
        ).hexdigest()
        
        result = {
            "sentinel": sentinel,
            "idp_token": idp_token,
            "slot": slot,
            "user_id": user_id,
            "issued_at": time.time()
        }
        self._tokens[sentinel] = result
        _log.info(f"Issued sentinel for user={user_id} slot={slot}")
        return result

    def verify(self, user_id: str, sentinel: str, idp_token: str, tolerance: int = 1) -> bool:
        # Validate IdP token first
        if not self._idp.validate(user_id, idp_token):
            _log.warning(f"IdP validation failed for user={user_id}")
            return False
        
        # Check cache
        if sentinel in self._tokens and self._tokens[sentinel].get("user_id") == user_id:
            return True
        
        # Verify against time windows
        now = self._slot()
        for delta in range(-tolerance, tolerance + 1):
            key = self._key(now + delta, user_id)
            expected = hmac.new(
                key,
                f"{user_id}:{now + delta}".encode(),
                hashlib.sha256
            ).hexdigest()
            if hmac.compare_digest(expected, sentinel):
                self._tokens[sentinel] = {"user_id": user_id, "slot": now + delta}
                _log.info(f"Verified sentinel for user={user_id} slot={now + delta}")
                return True
        
        _log.warning(f"Sentinel verification FAILED for user={user_id}")
        return False

    def revoke(self, user_id: str) -> bool:
        for tok, data in list(self._tokens.items()):
            if data.get("user_id") == user_id:
                del self._tokens[tok]
        return True


class DynamicSentinelConfig:
    """Configuration for Dynamic Sentinel"""
    
    def __init__(self, window_seconds: int = 3600, tolerance: int = 1):
        self.window_seconds = window_seconds
        self.tolerance = tolerance
        self.secret = b"sovereign-sentinel-secure"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "window_seconds": self.window_seconds,
            "tolerance": self.tolerance,
            "signature": QUANTUM_SIGNATURE,
            "coherence": COHERENCE_THRESHOLD
        }


if __name__ == "__main__":
    # Demo
    sentinel = DynamicSentinel(b"test-secret")
    creds = sentinel.issue("test-user")
    print(f"Sentinel: {creds['sentinel'][:16]}...")
    print(f"IdP Token: {creds['idp_token'][:16]}...")
    
    valid = sentinel.verify("test-user", creds['sentinel'], creds['idp_token'])
    print(f"Valid: {valid}")