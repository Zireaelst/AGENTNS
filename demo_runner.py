#!/usr/bin/env python3
"""
demo_runner.py
Single-process demo orchestrator for AGENTNS.
Runs the full pipeline sequentially with clean, phased output.

This simulates the full flow without needing 3 separate AXL nodes.
Perfect for recordings, presentations, and judge demos.

Usage:
    DEMO_MODE=mock python demo_runner.py
"""

import os
import sys
import json
import time
import uuid

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("DEMO_MODE", "mock")

from utils.ens_resolver import get_resolver, ENS_PARENT
from utils.message import create_message, serialize, MSG_TASK, MSG_DECISION, MSG_ACK
from utils.logger import (
    log, separator, phase, box, success, warn, info,
    error as log_error, result_block, COLORS,
)

C = COLORS
ENS_DOMAIN = os.getenv("ENS_PARENT", ENS_PARENT)


def main():
    trace_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    # ═══════════════════════════════════════════════════════════════
    # TITLE
    # ═══════════════════════════════════════════════════════════════
    box(
        "🟣 AGENTNS — Decentralized Agent Swarm Demo",
        "ENS Discovery + Gensyn AXL P2P + KeeperHub Execution",
    )
    print(f"\n  {C['dim']}Trace ID:   {trace_id}{C['reset']}")
    print(f"  {C['dim']}Mode:       {os.getenv('DEMO_MODE', 'mock')}{C['reset']}")
    print(f"  {C['dim']}Registry:   {ENS_DOMAIN}{C['reset']}")
    time.sleep(0.5)

    resolver = get_resolver()

    # ═══════════════════════════════════════════════════════════════
    # PHASE 1: DISCOVERY
    # ═══════════════════════════════════════════════════════════════
    phase(1, 5, "📛", "ENS Discovery — Querying decentralized registry")
    time.sleep(0.3)

    info(f"Reading registry from {ENS_DOMAIN}...")
    all_agents = resolver.discover_agents(ENS_DOMAIN)
    time.sleep(0.3)

    success(f"Found {len(all_agents)} registered agents:")
    for agent in all_agents:
        caps_str = ", ".join(agent["capabilities"])
        rep = agent["reputation"]
        rep_bar = "█" * int(rep) + "░" * (5 - int(rep))
        print(f"     {C['cyan']}•{C['reset']} {agent['name']:<30} "
              f"{C['dim']}caps:{C['reset']} [{caps_str}]  "
              f"{C['dim']}rep:{C['reset']} {rep_bar} {rep}/5.0")
    time.sleep(0.5)

    # ═══════════════════════════════════════════════════════════════
    # PHASE 2: SCOUT — Opportunity Detection
    # ═══════════════════════════════════════════════════════════════
    phase(2, 5, "🔍", "Scout — Opportunity Detection")
    time.sleep(0.3)

    opportunity = {
        "type": "defi_opportunity",
        "signal": "ETH/USDC pool imbalance detected on Uniswap v3",
        "pool": "0x8ad599c3A0ff1De082011EFDDc58f1908eb6e6D8",
        "confidence": 0.87,
        "token_in": "USDC",
        "token_out": "ETH",
        "amount": "500",
        "estimated_profit_bps": 42,
        "timestamp": int(time.time()),
    }

    log("scout", "Scanning DeFi pools...", "cyan")
    time.sleep(0.5)
    log("scout", f"🎯 Signal: {opportunity['signal']}", "yellow")
    log("scout", f"   Confidence: {opportunity['confidence']*100:.0f}% | Est. profit: {opportunity['estimated_profit_bps']} bps", "yellow")
    time.sleep(0.3)

    # Scout discovers Strategy via ENS
    log("scout", "Finding best agent with 'analyze' capability via ENS...", "cyan")
    time.sleep(0.3)
    strategy_agent = resolver.find_best_agent(ENS_DOMAIN, capability="analyze")
    log("scout", f"→ Selected: {strategy_agent['name']} (rep: {strategy_agent['reputation']}/5.0)", "green")
    time.sleep(0.3)

    # Build and "send" message
    task_msg = create_message(
        MSG_TASK, f"scout.{ENS_DOMAIN}", strategy_agent["name"],
        {"opportunity": opportunity, "priority": "high"},
        trace_id=trace_id,
    )
    log("scout", f"Sending task via AXL P2P → {strategy_agent['name']}", "cyan")
    time.sleep(0.3)
    success("Task dispatched via encrypted AXL channel ✓")
    time.sleep(0.5)

    # ═══════════════════════════════════════════════════════════════
    # PHASE 3: STRATEGY — Analysis & Decision
    # ═══════════════════════════════════════════════════════════════
    phase(3, 5, "🧠", "Strategy — Analysis & Decision")
    time.sleep(0.3)

    log("strategy", f"Received task from scout (trace: {trace_id})", "magenta")
    log("strategy", "Analyzing opportunity...", "magenta")
    time.sleep(0.8)

    # Decision reasoning display
    confidence = opportunity["confidence"]
    print(f"\n     {C['bold']}{C['magenta']}── Decision Reasoning ─────────────────────{C['reset']}")
    reasoning = [
        f"Signal:       {opportunity['signal']}",
        f"Confidence:   {confidence*100:.0f}% {'✓' if confidence > 0.8 else '△'} (threshold: 80%)",
        f"Risk level:   LOW (established pair, high liquidity)",
        f"Pair:         {opportunity['token_in']}/{opportunity['token_out']}",
        f"Amount:       {opportunity['amount']} {opportunity['token_in']} (full)",
        f"Slippage:     0.5%",
    ]
    for line in reasoning:
        print(f"     {C['magenta']}{line}{C['reset']}")
        time.sleep(0.15)

    print(f"     {C['bold']}{C['green']}Verdict:      APPROVE ✓{C['reset']}")
    print(f"     {C['magenta']}Reason:       Confidence 87% exceeds threshold. Pool fundamentals strong.{C['reset']}")
    print(f"     {C['bold']}{C['magenta']}───────────────────────────────────────────{C['reset']}")
    time.sleep(0.5)

    # Strategy discovers Executor via ENS
    log("strategy", "Finding best agent with 'execute' capability via ENS...", "magenta")
    time.sleep(0.3)
    executor_agent = resolver.find_best_agent(ENS_DOMAIN, capability="execute")
    log("strategy", f"→ Selected: {executor_agent['name']} (rep: {executor_agent['reputation']}/5.0)", "green")

    log("strategy", f"Sending execution order via AXL P2P → {executor_agent['name']}", "magenta")
    time.sleep(0.3)
    success("Execution order dispatched ✓")
    time.sleep(0.5)

    # ═══════════════════════════════════════════════════════════════
    # PHASE 4: EXECUTOR — KeeperHub Execution
    # ═══════════════════════════════════════════════════════════════
    phase(4, 5, "⚡", "Executor — KeeperHub Onchain Execution")
    time.sleep(0.3)

    log("executor", f"Received execution order (trace: {trace_id})", "green")
    log("executor", "Action: swap 500 USDC → ETH (slippage: 0.5%)", "green")
    log("executor", "Validating order... ✓", "green")
    time.sleep(0.3)

    # KeeperHub submission with retry
    log("executor", "Submitting to KeeperHub...", "green")
    log("executor", "Features: MEV protection, retry logic, gas optimization", "green")
    time.sleep(1.0)

    # Simulated failure → recovery
    warn("Attempt 1/3: Gas spike detected (base fee: 142 → 380 gwei)")
    log("executor", "KeeperHub auto-retry triggered — optimizing gas...", "yellow")
    time.sleep(1.0)

    log("executor", "Attempt 2/3: Resubmitting with optimized gas (28 gwei)...", "green")
    time.sleep(1.5)

    ts = int(time.time())
    tx_hash = f"0x{'a' * 12}{ts}"
    job_id = f"kh-{ts}"
    audit_url = f"https://app.keeperhub.com/jobs/{job_id}"

    print(f"\n     {C['bold']}{C['green']}✓ EXECUTED ONCHAIN{C['reset']}")
    results = [
        f"Job ID:     {job_id}",
        f"Tx Hash:    {tx_hash}",
        f"Attempts:   2 (retry recovered from gas spike)",
        f"Gas used:   142,000",
        f"Gas saved:  81% (optimized by KeeperHub)",
        f"MEV safe:   True",
        f"Audit:      {audit_url}",
    ]
    for line in results:
        print(f"     {C['green']}{line}{C['reset']}")
    time.sleep(0.5)

    # ═══════════════════════════════════════════════════════════════
    # PHASE 5: AUDIT TRAIL
    # ═══════════════════════════════════════════════════════════════
    phase(5, 5, "📊", "Audit Trail & Reputation Update")
    time.sleep(0.3)

    # Reputation updates
    log("ens", "Updating agent reputations via ENS...", "yellow")
    time.sleep(0.3)
    rep_updates = resolver.update_reputation(f"scout.{ENS_DOMAIN}", 0.05)
    rep_updates2 = resolver.update_reputation(f"strategy.{ENS_DOMAIN}", 0.05)

    # Final summary
    elapsed = time.time() - start_time

    print(f"\n     {C['bold']}{C['cyan']}── Pipeline Summary ─────────────────────────{C['reset']}")
    summary = [
        f"Trace ID:       {trace_id}",
        f"Pipeline:       scout → strategy → executor → chain",
        f"Discovery:      ENS text records (no central registry)",
        f"Communication:  Gensyn AXL P2P (encrypted, no server)",
        f"Execution:      KeeperHub (MEV-protected, auto-retry)",
        f"Time:           {elapsed:.1f}s",
    ]
    for line in summary:
        print(f"     {C['white']}{line}{C['reset']}")
    print(f"     {C['bold']}{C['cyan']}─────────────────────────────────────────────{C['reset']}")

    # Final box
    print(f"\n{C['bold']}{C['green']}╔{'═'*60}╗{C['reset']}")
    print(f"{C['bold']}{C['green']}║  AGENTNS Pipeline Complete ✓                               ║{C['reset']}")
    print(f"{C['bold']}{C['green']}║  Every component is decentralized. No servers. Just P2P.    ║{C['reset']}")
    print(f"{C['bold']}{C['green']}╚{'═'*60}╝{C['reset']}")
    print()


if __name__ == "__main__":
    main()
