"""
agents/strategy.py
Strategy Agent (strategy.agentns.eth)
  • Daemon loop — continuously listens for tasks via AXL
  • Uses LLM (Gemini/OpenRouter/Claude/Ollama) to analyze opportunities
  • Falls back to rule-based decisions if no LLM available
  • Resolves executor.agentns.eth via ENS
  • Forwards execution order to Executor via AXL

Run: python -m agents.strategy
"""

import os, sys, json, time, signal
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from dotenv import load_dotenv
load_dotenv()

from utils.axl_client  import AXLClient
from utils.ens_resolver import get_resolver
from utils.logger       import log, phase, banner
from utils.llm_client   import chat, is_available, get_active_provider

AXL_PORT     = int(os.getenv("STRATEGY_AXL_PORT", "9012"))
EXECUTOR_ENS = "executor.agentns.eth"

_running = True
signal.signal(signal.SIGINT,  lambda *_: globals().update(_running=False))
signal.signal(signal.SIGTERM, lambda *_: globals().update(_running=False))

DECISION_SYSTEM = """You are a DeFi risk-management agent in a decentralized swarm.
Evaluate the opportunity and decide whether to execute it.

Rules:
- confidence > 0.85 → approve full amount
- 0.65 ≤ confidence ≤ 0.85 → approve_partial (50% amount)  
- confidence < 0.65 → reject

Respond ONLY with valid JSON (no markdown, no preamble):
{
  "decision": "approve" | "approve_partial" | "reject",
  "reason": "one sentence",
  "action": {
    "type": "swap",
    "token_in": "...",
    "token_out": "...",
    "amount": "...",
    "slippage": "0.5"
  }
}"""


def _extract_json_from_response(raw: str) -> dict:
    """Extract JSON from LLM response, handling markdown fences."""
    import re
    text = raw.strip()
    # Strip markdown fences
    if text.startswith("```"):
        text = "\n".join(text.split("\n")[1:])
        if text.endswith("```"):
            text = text[:-3]
        elif "```" in text:
            text = text[:text.rfind("```")]
        text = text.strip()
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Try to find JSON object in text
    match = re.search(r'\{[^{}]*"decision"[^{}]*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    raise ValueError(f"Could not parse JSON from LLM response: {text[:200]}")


def _rule_based_decide(opportunity: dict) -> dict:
    """Deterministic rule-based fallback — always works, no API needed."""
    conf = opportunity.get("confidence", 0)
    if conf > 0.85:
        decision, amount = "approve",         opportunity.get("amount", "500")
    elif conf >= 0.65:
        decision, amount = "approve_partial",  str(int(float(opportunity.get("amount", "500")) * 0.5))
    else:
        decision, amount = "reject",           "0"
    return {
        "decision": decision,
        "reason":   f"Rule-based: confidence={conf}",
        "action": {
            "type":      "swap",
            "token_in":  opportunity.get("token_in",  "USDC"),
            "token_out": opportunity.get("token_out", "ETH"),
            "amount":    amount,
            "slippage":  "0.5",
        }
    }


def decide(opportunity: dict) -> dict:
    """
    Use LLM to analyze opportunity.
    Tries: Google Gemini → OpenRouter → Anthropic → Ollama → Rule-based.
    """
    if not is_available():
        log("strategy", "No LLM available — using rule-based decision")
        return _rule_based_decide(opportunity)

    try:
        provider = get_active_provider()
        log("strategy", f"Analyzing with {provider.upper()}…")
        raw = chat(
            system=DECISION_SYSTEM,
            user=json.dumps(opportunity, indent=2),
            max_tokens=512,
        )
        return _extract_json_from_response(raw)
    except Exception as e:
        log("strategy", f"LLM failed ({e}) — falling back to rule-based", ok=False)
        return _rule_based_decide(opportunity)


def process_task(axl: AXLClient, resolver, msg: dict) -> None:
    """Handle one incoming task from Scout."""
    from_peer = msg["from_peer_id"]
    task      = msg["data"]
    opp       = task.get("opportunity", {})

    log("strategy", f"Task from {task.get('from', from_peer[:14])}")
    log("strategy", f"Signal: {opp.get('signal','?')}")
    log("strategy", f"Confidence: {opp.get('confidence')}")

    # Ack immediately
    axl.send(from_peer, {"type": "ack", "status": "received", "from": "strategy.agentns.eth"})

    # LLM decision
    provider = get_active_provider()
    phase(f"LLM Analysis ({provider.upper()})")
    result = decide(opp)
    log("strategy", f"Decision: {result['decision'].upper()}")
    log("strategy", f"Reason:   {result['reason']}")

    if result["decision"] == "reject":
        log("strategy", "Opportunity rejected — no execution needed", ok=False)
        return

    # Resolve Executor via ENS
    phase("ENS Discovery → executor.agentns.eth")
    executor = resolver.resolve(EXECUTOR_ENS)
    if not executor:
        log("strategy", f"Cannot resolve {EXECUTOR_ENS}", ok=False)
        return

    log("strategy", f"Resolved:   {EXECUTOR_ENS}")
    log("strategy", f"peer_id:    {executor['peer_id'][:20]}…")
    log("strategy", f"reputation: {executor['reputation']}")

    # Forward execution order via AXL
    phase("AXL → Dispatch to Executor (P2P encrypted)")
    order = {
        "type":           "execution_order",
        "from":           "strategy.agentns.eth",
        "from_peer_id":   axl.peer_id(),
        "decision":       result,
        "original_from":  task.get("from"),
        "timestamp":      int(time.time()),
    }
    ok = axl.send(executor["peer_id"], order)
    if ok:
        log("strategy", "Execution order dispatched ✓")
    else:
        log("strategy", "AXL send to executor failed", ok=False)


def main():
    provider = get_active_provider()
    banner("STRATEGY AGENT — strategy.agentns.eth",
           f"LLM={provider} → ENS discover → AXL forward")

    axl = AXLClient(AXL_PORT, "strategy")
    log("strategy", f"Connecting to AXL node on port {AXL_PORT}…")
    if not axl.wait_ready():
        log("strategy", "AXL node not available", ok=False)
        sys.exit(1)
    log("strategy", f"AXL ready. peer_id={axl.peer_id()[:20]}…")

    resolver = get_resolver()
    cycle    = 0

    log("strategy", "Listening for tasks… (Ctrl+C to stop)")

    while _running:
        cycle += 1
        log("strategy", f"Cycle #{cycle} — waiting for AXL message…")
        msg = axl.recv(timeout=120)
        if not msg:
            if _running:
                log("strategy", "No message in 120s, still listening…", ok=False)
            continue
        # Skip acks sent from ourselves
        if msg["data"].get("type") == "ack":
            continue
        try:
            process_task(axl, resolver, msg)
        except Exception as e:
            log("strategy", f"Error processing task: {e}", ok=False)

    log("strategy", "Shutting down gracefully ✓")


if __name__ == "__main__":
    main()
