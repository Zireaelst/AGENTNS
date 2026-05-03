"""
agents/executor.py
Executor Agent (executor.agentns.eth)
  • Daemon loop — continuously listens for execution orders via AXL
  • Submits to KeeperHub via Anthropic MCP integration
  • Writes reputation back to ENS after success
  • Prints full audit trail

Run: python -m agents.executor
"""

import os, sys, json, time, signal
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from dotenv import load_dotenv
load_dotenv()

from utils.axl_client  import AXLClient
from utils.ens_resolver import get_resolver
from utils.keeperhub   import execute_via_keeperhub_mcp
from utils.logger       import log, phase, banner, table

AXL_PORT  = int(os.getenv("EXECUTOR_AXL_PORT", "9022"))
DEMO_MODE = os.getenv("DEMO_MODE", "mock")

_running = True
signal.signal(signal.SIGINT,  lambda *_: globals().update(_running=False))
signal.signal(signal.SIGTERM, lambda *_: globals().update(_running=False))


def process_order(axl: AXLClient, resolver, msg: dict, order_num: int) -> None:
    """Execute one approved order end-to-end."""
    order    = msg["data"]
    decision = order.get("decision", {})
    action   = decision.get("action", {})
    from_ens = order.get("original_from", "unknown")

    phase(f"Execution Order #{order_num}")
    log("executor", f"From:     {order.get('from','?')}")
    log("executor", f"Decision: {decision.get('decision','?').upper()}")
    log("executor", f"Action:   {action.get('type')} {action.get('amount')} "
                    f"{action.get('token_in')} → {action.get('token_out')}")

    if decision.get("decision") not in ("approve", "approve_partial"):
        log("executor", "Order not approved — nothing to do", ok=False)
        return

    # ── KeeperHub Execution ──────────────────────────────────────────────────
    phase("KeeperHub → Guaranteed Onchain Execution")
    log("executor", "Submitting to KeeperHub (MEV-protected, retry-enabled)…")

    result = execute_via_keeperhub_mcp(action, from_agent=from_ens)

    if result.get("status") != "success":
        log("executor", f"Execution FAILED: {result.get('error','unknown')}", ok=False)
        return

    log("executor", "✓ EXECUTED ONCHAIN")

    # ── Reputation update ────────────────────────────────────────────────────
    phase("ENS Reputation Write-back")
    strategy_ens = order.get("from", "strategy.agentns.eth")
    strategy     = resolver.resolve(strategy_ens)

    if strategy:
        new_rep = round(min(strategy["reputation"] + 0.1, 5.0), 1)
        tx      = resolver.update_reputation(strategy_ens, new_rep)
        log("executor", f"Reputation {strategy_ens}: {strategy['reputation']} → {new_rep}")
        if tx:
            tx_hash = tx.get("tx_hash") if isinstance(tx, dict) else tx
            log("executor", f"ENS tx: https://sepolia.etherscan.io/tx/{tx_hash}")

    if from_ens and from_ens != strategy_ens:
        scout = resolver.resolve(from_ens)
        if scout:
            new_rep = round(min(scout["reputation"] + 0.05, 5.0), 1)
            resolver.update_reputation(from_ens, new_rep)
            log("executor", f"Reputation {from_ens}: {scout['reputation']} → {new_rep}")

    # ── Audit trail ─────────────────────────────────────────────────────────
    phase("Audit Trail")
    table([
        ("Pipeline",      "scout → strategy → executor"),
        ("ENS discovery", "No central registry ✓"),
        ("AXL comms",     "End-to-end encrypted ✓"),
        ("Decision",      decision.get("decision", "?")),
        ("Reason",        decision.get("reason","?")[:35]),
        ("KeeperHub job", result.get("job_id","?")),
        ("Tx hash",       result.get("tx_hash","?")[:20] + "…"),
        ("MEV protected", str(result.get("mev_protected", True))),
        ("Gas used",      f"{result.get('gas_used', 0):,}"),
        ("Retries",       str(result.get("retries", 0))),
        ("Audit URL",     result.get("audit_url","?")[:35]),
    ])
    log("executor", "Pipeline complete ✓")


def main():
    banner("EXECUTOR AGENT — executor.agentns.eth",
           "Listen → KeeperHub execute → ENS reputation update")

    axl = AXLClient(AXL_PORT, "executor")
    log("executor", f"Connecting to AXL node on port {AXL_PORT}…")
    if not axl.wait_ready():
        log("executor", "AXL node not available", ok=False)
        sys.exit(1)
    log("executor", f"AXL ready. peer_id={axl.peer_id()[:20]}…")

    resolver  = get_resolver()
    order_num = 0

    log("executor", "Listening for execution orders… (Ctrl+C to stop)")

    while _running:
        msg = axl.recv(timeout=120)
        if not msg:
            if _running:
                log("executor", "No order in 120s, still listening…", ok=False)
            continue
        if msg["data"].get("type") == "ack":
            continue
        order_num += 1
        try:
            process_order(axl, resolver, msg, order_num)
        except Exception as e:
            log("executor", f"Error: {e}", ok=False)

    log("executor", "Shutting down gracefully ✓")


if __name__ == "__main__":
    main()
