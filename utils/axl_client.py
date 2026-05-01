"""
utils/axl_client.py
Exact wrapper around Gensyn AXL HTTP interface.

AXL API (confirmed from official docs):
  GET  /topology                              → {our_public_key, our_ipv6, ...}
  POST /send + X-Destination-Peer-Id header  → send raw bytes to peer
  GET  /recv                                  → recv bytes, X-From-Peer-Id header

Peer ID = 64-char hex ed25519 public key.
All messages are raw bytes — we encode JSON ourselves.
"""

import json
import time
import requests
from utils.logger import log


class AXLClient:
    def __init__(self, port: int, agent_name: str):
        self.url  = f"http://127.0.0.1:{port}"
        self.name = agent_name
        self._peer_id: str | None = None

    # ── Identity ────────────────────────────────────────────────────────────

    def peer_id(self) -> str:
        """Return our public key (cached after first call)."""
        if self._peer_id:
            return self._peer_id
        try:
            r = requests.get(f"{self.url}/topology", timeout=5)
            r.raise_for_status()
            self._peer_id = r.json()["our_public_key"]
            log("axl", f"[{self.name}] peer_id={self._peer_id[:16]}…")
            return self._peer_id
        except Exception as e:
            log("axl", f"[{self.name}] /topology failed: {e}", ok=False)
            raise

    # ── Send ────────────────────────────────────────────────────────────────

    def send(self, destination_peer_id: str, payload: dict) -> bool:
        """JSON-encode payload and POST to destination peer via AXL."""
        body = json.dumps(payload).encode("utf-8")
        try:
            r = requests.post(
                f"{self.url}/send",
                headers={"X-Destination-Peer-Id": destination_peer_id},
                data=body,
                timeout=10,
            )
            r.raise_for_status()
            log("axl", f"[{self.name}] → sent {len(body)}B to {destination_peer_id[:14]}…")
            return True
        except Exception as e:
            log("axl", f"[{self.name}] send failed: {e}", ok=False)
            return False

    # ── Receive ─────────────────────────────────────────────────────────────

    def recv(self, timeout: int = 60) -> dict | None:
        """
        Poll /recv until a JSON message arrives or timeout expires.
        AXL returns 200+body when a message is available, otherwise empty/204.
        Returns {from_peer_id: str, data: dict} or None on timeout.
        """
        deadline = time.time() + timeout
        log("axl", f"[{self.name}] listening… (timeout={timeout}s)")
        while time.time() < deadline:
            try:
                r = requests.get(f"{self.url}/recv", timeout=5)
                if r.status_code == 200 and r.content.strip():
                    from_peer = r.headers.get("X-From-Peer-Id", "unknown")
                    data = json.loads(r.content.decode("utf-8"))
                    log("axl", f"[{self.name}] ← {len(r.content)}B from {from_peer[:14]}…")
                    return {"from_peer_id": from_peer, "data": data}
            except (requests.exceptions.RequestException, json.JSONDecodeError):
                pass
            time.sleep(0.8)
        log("axl", f"[{self.name}] recv timeout", ok=False)
        return None

    def wait_ready(self, retries: int = 15) -> bool:
        """Block until AXL node responds to /topology."""
        for i in range(retries):
            try:
                r = requests.get(f"{self.url}/topology", timeout=3)
                if r.status_code == 200:
                    self.peer_id()
                    return True
            except Exception:
                pass
            time.sleep(1)
        return False
