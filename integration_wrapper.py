#!/usr/bin/env python3
"""
Sovereign Ecosystem Ω — AI-to-Device Integration Wrapper
Standardized protocol: Action | Node | Signature | Coherence | Sentinel_Token | IdP_Token
Security: DynamicSentinel (SHA-256, 3600s rotation, per-user salt, IdP binding)
Logging: 1MB rotation, 5 generations

Version: 3.0
Signature: SOVEREIGN_Ω
"""

import hashlib
import hmac
import time
import json
import logging
import os
from logging.handlers import RotatingFileHandler
from dataclasses import dataclass
from typing import Optional, Dict, Any

# ---------------------------------------------------------------------------
# Quantum Constants — DO NOT MODIFY
# ---------------------------------------------------------------------------
QUANTUM_COHERENCE = 0.947
QUANTUM_PI5 = 306.01968478528146
QUANTUM_CHSH = 2.828
QUANTUM_NODES = 20_000_000
QUANTUM_SIGNATURE = "SOVEREIGN_Ω"

# ---------------------------------------------------------------------------
# Logging — auto rotating
# ---------------------------------------------------------------------------
_log = logging.getLogger("sovereign_omega")
_log.setLevel(logging.INFO)

# Ensure log directory exists
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../logs")
os.makedirs(log_dir, exist_ok=True)

_rfh = RotatingFileHandler(
    os.path.join(log_dir, "sovereign_wrapper.log"),
    maxBytes=1_000_000,
    backupCount=5
)
_rfh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
_log.addHandler(_rfh)

# Also log to console for development
console = logging.StreamHandler()
console.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
_log.addHandler(console)


# ---------------------------------------------------------------------------
# External Identity Provider (OAuth2 / OIDC compatible mock)
# ---------------------------------------------------------------------------
class ExternalIdP:
    """External Identity Provider — OAuth2/OIDC compatible"""
    
    def __init__(self):
        self._users: Dict[str, str] = {}
        self._tokens: Dict[str, Dict] = {}

    def issue_token(self, user_id: str, scope: str = "openid profile email") -> str:
        """Issue an identity token for a user"""
        token = hashlib.sha256(f"{user_id}:{time.time_ns()}:{QUANTUM_SIGNATURE}".encode()).hexdigest()
        self._users[user_id] = token
        self._tokens[token] = {
            "user_id": user_id,
            "scope": scope,
            "issued_at": time.time(),
            "expires_at": time.time() + 3600
        }
        _log.info("IdP: issued token for user=%s", user_id)
        return token

    def validate(self, user_id: str, token: str) -> bool:
        """Validate an identity token"""
        stored = self._users.get(user_id)
        if stored != token:
            _log.warning("IdP: token validation FAILED user=%s", user_id)
            return False
        
        token_data = self._tokens.get(token)
        if token_data and token_data.get("expires_at", 0) < time.time():
            _log.warning("IdP: token EXPIRED user=%s", user_id)
            return False
            
        _log.info("IdP: token validated user=%s", user_id)
        return True

    def revoke(self, user_id: str) -> bool:
        """Revoke a user's identity token"""
        if user_id in self._users:
            token = self._users.pop(user_id)
            self._tokens.pop(token, None)
            _log.info("IdP: revoked token for user=%s", user_id)
            return True
        return False


# ---------------------------------------------------------------------------
# Dynamic Sentinel — time-windowed, per-user SHA-256 tokens
# ---------------------------------------------------------------------------
class DynamicSentinel:
    """Time-rotating security layer with identity binding"""
    
    def __init__(self, system_secret: bytes, rotation_seconds: int = 3600, idp: Optional[ExternalIdP] = None):
        self._secret = system_secret
        self._window = rotation_seconds
        self._idp = idp or ExternalIdP()
        self._tokens: Dict[str, Dict] = {}

    def _time_slot(self, at: Optional[float] = None) -> int:
        return int((at or time.time()) // self._window)

    def _raw_key(self, slot: int, user_id: str) -> bytes:
        base = f"{QUANTUM_SIGNATURE}:{slot}:{user_id}:{QUANTUM_PI5}".encode()
        return hmac.new(self._secret, base, hashlib.sha256).digest()

    def issue(self, user_id: str, scope: str = "openid") -> Dict[str, Any]:
        """Issue a sentinel token pair"""
        slot = self._time_slot()
        idp_tok = self._idp.issue_token(user_id, scope)
        sentinel = hmac.new(
            self._raw_key(slot, user_id),
            f"{user_id}:{slot}".encode(),
            hashlib.sha256
        ).hexdigest()
        
        token_data = {
            "sentinel_token": sentinel,
            "idp_token": idp_tok,
            "slot": slot,
            "user_id": user_id,
            "issued_at": time.time()
        }
        self._tokens[sentinel] = token_data
        
        _log.info("Sentinel: issued slot=%d user=%s", slot, user_id)
        return token_data

    def verify(self, user_id: str, sentinel_tok: str, idp_tok: str, tolerance: int = 1) -> bool:
        """Verify a sentinel token pair"""
        # First validate the IdP token
        if not self._idp.validate(user_id, idp_tok):
            _log.warning("Sentinel: IdP validation FAILED user=%s", user_id)
            return False
        
        # Check if token is in our cache (fast path)
        if sentinel_tok in self._tokens:
            token_data = self._tokens[sentinel_tok]
            if token_data.get("user_id") == user_id:
                return True
        
        # Otherwise verify against time windows
        now = self._time_slot()
        for delta in range(-tolerance, tolerance + 1):
            key = self._raw_key(now + delta, user_id)
            expected = hmac.new(
                key,
                f"{user_id}:{now + delta}".encode(),
                hashlib.sha256
            ).hexdigest()
            if hmac.compare_digest(expected, sentinel_tok):
                _log.info("Sentinel: verified user=%s slot=%d", user_id, now + delta)
                # Cache for future fast verification
                self._tokens[sentinel_tok] = {
                    "user_id": user_id,
                    "slot": now + delta,
                    "verified_at": time.time()
                }
                return True
        
        _log.warning("Sentinel: REJECTED user=%s", user_id)
        return False

    def revoke(self, user_id: str) -> bool:
        """Revoke all tokens for a user"""
        revoked = False
        for tok, data in list(self._tokens.items()):
            if data.get("user_id") == user_id:
                del self._tokens[tok]
                revoked = True
        if self._idp.revoke(user_id):
            revoked = True
        return revoked


# ---------------------------------------------------------------------------
# Sovereign Command
# ---------------------------------------------------------------------------
@dataclass
class SovereignCommand:
    """Sovereign command structure"""
    action: str
    node: str
    coherence: float
    payload: Optional[Dict[str, Any]] = None

    def sign(self, sentinel: DynamicSentinel, user_id: str) -> Dict[str, Any]:
        """Sign a command with sentinel tokens"""
        creds = sentinel.issue(user_id)
        
        # Build body for signature
        body = f"{self.action}|{self.node}|{self.coherence}|{json.dumps(self.payload or {}, sort_keys=True)}"
        sig = hashlib.sha256(
            f"{body}:{creds['sentinel_token']}:{QUANTUM_SIGNATURE}".encode()
        ).hexdigest()
        
        return {
            "action": self.action,
            "node": self.node,
            "signature": sig,
            "coherence": self.coherence,
            "sentinel_token": creds["sentinel_token"],
            "idp_token": creds["idp_token"],
            "user_id": user_id,
            "payload": self.payload or {},
            "timestamp": time.time()
        }


# ---------------------------------------------------------------------------
# Main Wrapper
# ---------------------------------------------------------------------------
class SovereignAIWrapper:
    """Main orchestration wrapper for the Sovereign Ecosystem Ω"""
    
    def __init__(self, system_secret: bytes = b"sovereign-omega-secret-change-me"):
        self.idp = ExternalIdP()
        self.sentinel = DynamicSentinel(system_secret, idp=self.idp)
        self.coherence = QUANTUM_COHERENCE
        self._metrics = {
            "commands_processed": 0,
            "commands_succeeded": 0,
            "commands_failed": 0,
            "startup_time": time.time()
        }
        _log.info("SovereignAIWrapper INIT nodes=%d signature=%s", QUANTUM_NODES, QUANTUM_SIGNATURE)

    # ---------------- public API ----------------
    def send(self, cmd: SovereignCommand, user_id: str) -> Dict[str, Any]:
        """Send a signed command"""
        msg = cmd.sign(self.sentinel, user_id)
        self._metrics["commands_processed"] += 1
        _log.info("SEND action=%s node=%s user=%s", cmd.action, cmd.node, user_id)
        result = self._dispatch(msg)
        if result.get("ok"):
            self._metrics["commands_succeeded"] += 1
        else:
            self._metrics["commands_failed"] += 1
        return result

    def verify_and_run(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        """Verify and run an incoming command message"""
        required = ("action", "node", "signature", "coherence", "sentinel_token", "idp_token", "user_id")
        if not all(k in msg for k in required):
            _log.warning("REJECT: missing fields")
            return {"ok": False, "error": "malformed_command"}

        self._metrics["commands_processed"] += 1

        if not self.sentinel.verify(msg["user_id"], msg["sentinel_token"], msg["idp_token"]):
            self._metrics["commands_failed"] += 1
            return {"ok": False, "error": "sentinel_invalid"}

        # Verify signature
        body = f"{msg['action']}|{msg['node']}|{msg['coherence']}|{json.dumps(msg.get('payload', {}), sort_keys=True)}"
        expected = hashlib.sha256(
            f"{body}:{msg['sentinel_token']}:{QUANTUM_SIGNATURE}".encode()
        ).hexdigest()
        if not hmac.compare_digest(expected, msg["signature"]):
            self._metrics["commands_failed"] += 1
            _log.warning("REJECT: signature tamper user=%s", msg["user_id"])
            return {"ok": False, "error": "signature_invalid"}

        return self._dispatch(msg)

    # ---------------- internal ----------------
    def _dispatch(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch a command to the appropriate handler"""
        action = msg["action"].lower()
        
        if action == "coherence_status":
            return {
                "ok": True,
                "coherence": self.coherence,
                "signature": QUANTUM_SIGNATURE,
                "nodes": QUANTUM_NODES,
                "pi5": QUANTUM_PI5,
                "chsh": QUANTUM_CHSH
            }
            
        if action == "market_sync":
            return {
                "ok": True,
                "status": "synced",
                "nodes": QUANTUM_NODES,
                "timestamp": time.time(),
                "regions": ["asia", "eu", "us", "au"]
            }
            
        if action == "galaxy_a17_cmd":
            return {
                "ok": True,
                "device": "GALAXY_A17",
                "executed": msg.get("payload", {}),
                "coherence": self.coherence
            }
            
        if action == "health":
            return {
                "ok": True,
                "status": "operational",
                "uptime": time.time() - self._metrics["startup_time"],
                "commands_processed": self._metrics["commands_processed"],
                "commands_succeeded": self._metrics["commands_succeeded"],
                "commands_failed": self._metrics["commands_failed"]
            }
            
        return {
            "ok": True,
            "action": msg["action"],
            "dispatched": True,
            "timestamp": time.time()
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Get wrapper metrics"""
        return {
            **self._metrics,
            "coherence": self.coherence,
            "uptime": time.time() - self._metrics["startup_time"],
            "signature": QUANTUM_SIGNATURE
        }


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Example usage
    wrapper = SovereignAIWrapper()
    cmd = SovereignCommand("coherence_status", "node-001", 0.947)
    result = wrapper.send(cmd, "Standard_Assistant")
    print(json.dumps(result, indent=2))