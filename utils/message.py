"""
utils/message.py
Standardized message envelope for inter-agent communication.
Every AXL message is wrapped in this schema for traceability and structure.
"""

import json
import time
import uuid


# ─── Message Types ───────────────────────────────────────────────
MSG_TASK       = "task"
MSG_DECISION   = "decision"
MSG_EXECUTION  = "execution"
MSG_ACK        = "ack"
MSG_ERROR      = "error"
MSG_REPUTATION = "reputation_update"

PROTOCOL_VERSION = "1.0"


def create_message(
    msg_type: str,
    from_agent: str,
    to_agent: str,
    payload: dict,
    trace_id: str | None = None,
) -> dict:
    """
    Create a standardized AGENTNS message.

    Args:
        msg_type:   One of task, decision, execution, ack, error
        from_agent: ENS name of sender (e.g. scout.agentns.eth)
        to_agent:   ENS name of recipient
        payload:    Message-specific data
        trace_id:   Pipeline trace ID (auto-generated if None)

    Returns:
        dict with standard envelope fields
    """
    return {
        "version": PROTOCOL_VERSION,
        "type": msg_type,
        "from": from_agent,
        "to": to_agent,
        "timestamp": int(time.time()),
        "trace_id": trace_id or str(uuid.uuid4())[:8],
        "payload": payload,
    }


def parse_message(raw: str) -> dict | None:
    """Parse a raw string into a message dict. Returns None on failure."""
    try:
        msg = json.loads(raw)
        if "version" in msg and "type" in msg and "payload" in msg:
            return msg
        # Legacy format — wrap in envelope
        return {
            "version": "0.9",
            "type": "legacy",
            "from": msg.get("from", "unknown"),
            "to": "unknown",
            "timestamp": msg.get("timestamp", int(time.time())),
            "trace_id": "legacy",
            "payload": msg,
        }
    except (json.JSONDecodeError, TypeError):
        return None


def serialize(msg: dict) -> str:
    """Serialize message to JSON string for AXL transport."""
    return json.dumps(msg, indent=2)


def format_summary(msg: dict) -> str:
    """Human-readable one-line summary of a message."""
    return (
        f"[{msg.get('type', '?').upper()}] "
        f"{msg.get('from', '?')} → {msg.get('to', '?')} "
        f"(trace: {msg.get('trace_id', '?')})"
    )
