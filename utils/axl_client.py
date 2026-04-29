"""
utils/axl_client.py
Minimal wrapper around Gensyn AXL HTTP interface.
Upgraded with message envelope support.

AXL API (from docs):
  POST /send   + header X-Destination-Peer-Id  → send message
  GET  /recv                                    → receive latest message
  GET  /topology                                → our public key + IPv6
"""

import requests
import time
import json
from utils.logger import log
from utils.message import create_message, parse_message, serialize, format_summary


class AXLClient:
    def __init__(self, port: int = 9002, agent_name: str = "agent"):
        self.base = f"http://127.0.0.1:{port}"
        self.agent_name = agent_name

    def get_peer_id(self) -> str:
        """Get our own public key from the running AXL node."""
        resp = requests.get(f"{self.base}/topology", timeout=5)
        resp.raise_for_status()
        key = resp.json()["our_public_key"]
        log(self.agent_name, f"AXL node up → peer_id: {key[:16]}...", "cyan")
        return key

    def send(self, destination_peer_id: str, message: str) -> bool:
        """Send a raw message to another AXL peer."""
        try:
            resp = requests.post(
                f"{self.base}/send",
                headers={"X-Destination-Peer-Id": destination_peer_id},
                data=message.encode("utf-8"),
                timeout=10,
            )
            resp.raise_for_status()
            log(self.agent_name, f"→ Sent to {destination_peer_id[:12]}... ✓", "green")
            return True
        except Exception as e:
            log(self.agent_name, f"✗ Send failed: {e}", "red")
            return False

    def send_message(
        self,
        destination_peer_id: str,
        msg_type: str,
        from_agent: str,
        to_agent: str,
        payload: dict,
        trace_id: str | None = None,
    ) -> bool:
        """
        Send a structured message using the AGENTNS envelope.
        Wraps payload in standard format with trace_id.
        """
        msg = create_message(msg_type, from_agent, to_agent, payload, trace_id)
        log(self.agent_name, f"Sending: {format_summary(msg)}", "cyan")
        return self.send(destination_peer_id, serialize(msg))

    def recv(self, timeout: int = 30) -> dict | None:
        """
        Poll /recv until a message arrives or timeout.
        Returns dict: {from_peer_id, message}
        """
        deadline = time.time() + timeout
        log(self.agent_name, "Waiting for message...", "yellow")
        while time.time() < deadline:
            try:
                resp = requests.get(f"{self.base}/recv", timeout=5)
                if resp.status_code == 200 and resp.content:
                    from_peer = resp.headers.get("X-From-Peer-Id", "unknown")
                    body = resp.content.decode("utf-8")
                    log(self.agent_name, f"← Received from {from_peer[:12]}...", "green")
                    return {"from_peer_id": from_peer, "message": body}
            except Exception:
                pass
            time.sleep(1)
        log(self.agent_name, "Timeout waiting for message", "red")
        return None

    def recv_message(self, timeout: int = 30) -> tuple[dict | None, str | None]:
        """
        Receive and parse a structured AGENTNS message.
        Returns: (parsed_message_dict, from_peer_id) or (None, None)
        """
        raw = self.recv(timeout)
        if not raw:
            return None, None
        msg = parse_message(raw["message"])
        if msg:
            log(self.agent_name, f"Message: {format_summary(msg)}", "green")
        return msg, raw["from_peer_id"]
