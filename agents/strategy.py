"""
agents/strategy.py
Strategy Agent — Receives task from Scout, analyzes with LLM,
resolves Executor via ENS, sends execution order via AXL.

KEY: Strategy discovers Executor dynamically via ENS capability search.
     Decision reasoning is displayed step-by-step for demo clarity.

Upgraded with:
  - Persistent daemon loop (GAP 3)

Run: python -m agents.strategy
"""

import os
import sys
import json
import anthropic
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.axl_client import AXLClient
from utils.ens_resolver import get_resolver
from utils.message import (
    create_message, parse_message, serialize, format_summary,
    MSG_DECISION, MSG_ACK,
)
from utils.logger import log, separator, detail, success, info

# ─── Config ─────────────────────────────────────────────────────
AXL_PORT       = int(os.getenv("STRATEGY_AXL_PORT", "9012"))
ENS_PARENT     = os.getenv("ENS_PARENT", "agentns.eth")
ANTHROPIC_KEY  = os.getenv("ANTHROPIC_API_KEY")

SYSTEM_PROMPT = """You are a DeFi strategy agent in a multi-agent swarm.
You receive market opportunities from scout agents and decide whether to act.

Rules:
- If confidence > 0.8: approve execution
- If confidence 0.5-0.8: approve with reduced amount (50%)
- If confidence < 0.5: reject

Respond ONLY with valid JSON:
{
  "decision": "approve" | "reject" | "approve_partial",
  "reason": "brief explanation",
  "action": {
    "type": "swap",
    "token_in": "...",
    "token_out": "...",
    "amount": "...",
    "slippage": "0.5"
  }
}"""


def decide_with_llm(task: dict) -> dict:
    """Use Claude to analyze the opportunity and decide."""
    if not ANTHROPIC_KEY:
        confidence = task.get("opportunity", {}).get("confidence", 0)
        amount = task.get("opportunity", {}).get("amount", "100")

        if confidence > 0.8:
            decision = "approve"
            final_amount = amount
        elif confidence >= 0.5:
            decision = "approve_partial"
            final_amount = str(int(float(amount) * 0.5))
        else:
            decision = "reject"
            final_amount = "0"

        return {
            "decision": decision,
            "reason": f"Confidence {confidence*100:.0f}% — {'exceeds' if confidence > 0.8 else 'below'} 80% threshold. Pool fundamentals strong.",
            "risk_level": "LOW" if confidence > 0.7 else "MEDIUM" if confidence > 0.5 else "HIGH",
            "action": {
                "type": "swap",
                "token_in": task.get("opportunity", {}).get("token_in", "USDC"),
                "token_out": task.get("opportunity", {}).get("token_out", "ETH"),
                "amount": final_amount,
                "slippage": "0.5",
            }
        }

    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=400,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Analyze this opportunity and decide: {json.dumps(task, indent=2)}"
        }]
    )
    raw = response.content[0].text.strip()
    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw)


def display_reasoning(opportunity: dict, decision: dict):
    """Show step-by-step decision reasoning — makes demo impressive."""
    separator("Decision Reasoning")
    confidence = opportunity.get("confidence", 0)
    signal = opportunity.get("signal", "Unknown")
    token_in = opportunity.get("token_in", "?")
    token_out = opportunity.get("token_out", "?")
    amount = decision.get("action", {}).get("amount", "?")
    risk = decision.get("risk_level", "UNKNOWN")

    log("strategy", f"Signal:       {signal}", "magenta")
    log("strategy", f"Confidence:   {confidence*100:.0f}% {'✓' if confidence > 0.8 else '△' if confidence > 0.5 else '✗'}", "magenta")
    log("strategy", f"Threshold:    80% for full approval", "magenta")
    log("strategy", f"Risk level:   {risk}", "green" if risk == "LOW" else "yellow" if risk == "MEDIUM" else "red")
    log("strategy", f"Pair:         {token_in}/{token_out}", "magenta")
    log("strategy", f"Size:         {amount} {token_in}", "magenta")
    log("strategy", f"Slippage:     {decision.get('action', {}).get('slippage', '?')}%", "magenta")

    verdict = decision["decision"]
    if verdict == "approve":
        log("strategy", f"Verdict:      APPROVE ✓ (full amount)", "green")
    elif verdict == "approve_partial":
        log("strategy", f"Verdict:      APPROVE PARTIAL △ (reduced size)", "yellow")
    else:
        log("strategy", f"Verdict:      REJECT ✗", "red")
    log("strategy", f"Reason:       {decision.get('reason', '')}", "magenta")


def _handle_strategy_cycle(axl, our_peer_id, my_name, cycle: int):
    """Handle a single strategy receive-analyze-forward cycle."""
    # 1. Wait for task from Scout
    separator(f"Cycle #{cycle} — Waiting for task from Scout (AXL)")
    incoming_msg, from_peer = axl.recv_message(timeout=60)
    if not incoming_msg:
        log("strategy", "No task received this cycle", "yellow")
        return

    trace_id = incoming_msg.get("trace_id", "unknown")
    log("strategy", f"Received task (trace: {trace_id})", "green")

    task = incoming_msg.get("payload", incoming_msg)
    opportunity = task.get("opportunity", {})
    log("strategy", f"Task type: {task.get('task')}", "magenta")
    log("strategy", f"Signal: {opportunity.get('signal', 'N/A')}", "magenta")
    log("strategy", f"From: {incoming_msg.get('from', 'unknown')}", "magenta")

    # 2. Send ack back to Scout
    from_peer_id = task.get("from_peer_id", from_peer)
    if from_peer_id:
        ack = create_message(MSG_ACK, my_name, incoming_msg.get("from", ""), {"status": "received"}, trace_id)
        axl.send(from_peer_id, serialize(ack))

    # 3. Analyze with LLM
    separator("Analysis & Decision")
    log("strategy", "Analyzing opportunity...", "magenta")
    decision = decide_with_llm(task)

    # 4. Display reasoning (key demo moment)
    display_reasoning(opportunity, decision)

    if decision["decision"] == "reject":
        log("strategy", "Task rejected. No execution needed.", "yellow")
        return

    # 5. Discover Executor via ENS — DYNAMIC CAPABILITY SEARCH
    separator("Discovering Executor via ENS")
    resolver = get_resolver()
    log("strategy", "Finding best agent with 'execute' capability...", "yellow")
    executor = resolver.find_best_agent(ENS_PARENT, capability="execute")

    if not executor:
        log("strategy", "No suitable executor found in ENS", "red")
        return

    log("strategy", f"Selected: {executor['name']}", "green")
    log("strategy", f"  capabilities: {executor['capabilities']}", "green")
    log("strategy", f"  reputation:   {executor['reputation']}/5.0", "green")

    # 6. Build execution order with standard envelope
    execution_msg = create_message(
        msg_type=MSG_DECISION,
        from_agent=my_name,
        to_agent=executor["name"],
        payload={
            "order_type": "swap_execution",
            "decision": decision,
            "original_task_from": incoming_msg.get("from"),
            "from_peer_id": our_peer_id,
            "chain_id": 1,
        },
        trace_id=trace_id,
    )

    # 7. Send to Executor via AXL
    separator("Sending execution order to Executor (AXL)")
    sent = axl.send(executor["peer_id"], serialize(execution_msg))

    if sent:
        log("strategy", "Execution order dispatched ✓", "green")
        log("strategy", f"Pipeline: scout → strategy → executor (trace: {trace_id})", "cyan")
        resolver.update_reputation(incoming_msg.get("from", ""), 0.05)
    else:
        log("strategy", "Failed to reach Executor", "red")

    separator("STRATEGY CYCLE DONE")


def main():
    """Strategy agent main loop — listens for tasks indefinitely."""
    my_name = f"strategy.{ENS_PARENT}"

    separator("STRATEGY AGENT STARTING")
    log("strategy", f"AXL port: {AXL_PORT}", "magenta")

    # Connect to AXL node
    axl = AXLClient(port=AXL_PORT, agent_name="strategy")
    our_peer_id = axl.get_peer_id()
    log("strategy", f"My peer_id: {our_peer_id[:20]}...", "magenta")

    cycle = 0
    try:
        while True:
            cycle += 1
            log("strategy", f"[STRATEGY] Cycle #{cycle} — listening...", "magenta")
            _handle_strategy_cycle(axl, our_peer_id, my_name, cycle)
    except KeyboardInterrupt:
        log("strategy", "[STRATEGY] Shutting down gracefully", "yellow")
        sys.exit(0)


if __name__ == "__main__":
    main()
