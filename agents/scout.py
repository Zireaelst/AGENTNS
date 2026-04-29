"""
agents/scout.py
Scout Agent — Discovers opportunities, finds peer agents via ENS,
initiates the workflow by messaging Strategy agent via AXL.

KEY: Scout does NOT hardcode who to talk to.
     It queries ENS for the best agent with "analyze" capability.

Upgraded with:
  - Real CoinGecko price-based opportunity detection (GAP 4)
  - Persistent daemon loop with LOOP_INTERVAL (GAP 3)

Run: python -m agents.scout
"""

import os
import sys
import json
import time
import uuid
import requests as http_requests
import anthropic
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.axl_client import AXLClient
from utils.ens_resolver import get_resolver
from utils.message import create_message, serialize, MSG_TASK, MSG_ACK
from utils.logger import log, separator, phase, detail, success, info

# ─── Config ─────────────────────────────────────────────────────
AXL_PORT       = int(os.getenv("SCOUT_AXL_PORT", "9002"))
ENS_PARENT     = os.getenv("ENS_PARENT", "agentns.eth")
ANTHROPIC_KEY  = os.getenv("ANTHROPIC_API_KEY")
LOOP_INTERVAL  = int(os.getenv("LOOP_INTERVAL", "30"))

# Expected ETH/USDC ratio for imbalance scoring
EXPECTED_ETH_PRICE = 2500.0


def _hardcoded_opportunity() -> dict:
    """Fallback hardcoded opportunity for when real data sources fail."""
    return {
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


def fetch_real_opportunity() -> dict:
    """
    Fetch live ETH and USDC prices from CoinGecko, compute an
    imbalance score against EXPECTED_ETH_PRICE, and return a
    real opportunity dict. Falls back to hardcoded data on error.
    """
    try:
        eth_resp = http_requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "ethereum", "vs_currencies": "usd"},
            timeout=10,
        )
        eth_resp.raise_for_status()
        eth_price = eth_resp.json()["ethereum"]["usd"]

        usdc_resp = http_requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "usd-coin", "vs_currencies": "usd"},
            timeout=10,
        )
        usdc_resp.raise_for_status()
        usdc_price = usdc_resp.json()["usd-coin"]["usd"]

        imbalance_score = abs(eth_price - EXPECTED_ETH_PRICE) / EXPECTED_ETH_PRICE
        confidence = min(imbalance_score * 10, 0.99)
        profit_bps = max(int(imbalance_score * 1000), 5)

        return {
            "type": "defi_opportunity",
            "signal": f"ETH=${eth_price:,.0f} (USDC=${usdc_price:.4f}) — pool imbalance on Uniswap v3",
            "pool": "0x8ad599c3A0ff1De082011EFDDc58f1908eb6e6D8",
            "confidence": round(confidence, 2),
            "token_in": "USDC",
            "token_out": "ETH",
            "amount": "500",
            "estimated_profit_bps": profit_bps,
            "eth_price": eth_price,
            "usdc_price": usdc_price,
            "timestamp": int(time.time()),
        }

    except Exception as e:
        log("scout", f"CoinGecko API failed ({e}) — using hardcoded data", "yellow")
        return _hardcoded_opportunity()


def detect_opportunity() -> dict:
    """
    Detect a DeFi opportunity. Uses live CoinGecko prices when
    available, falls back to hardcoded data in mock mode or on error.
    """
    demo_mode = os.getenv("DEMO_MODE", "mock")
    if demo_mode == "mock":
        return _hardcoded_opportunity()
    return fetch_real_opportunity()


def analyze_with_llm(opportunity: dict) -> str:
    """Use Claude to generate a structured task description."""
    if not ANTHROPIC_KEY:
        return json.dumps({
            "task": "analyze_and_execute",
            "opportunity": opportunity,
            "priority": "high",
            "from_agent": f"scout.{ENS_PARENT}",
        })

    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": (
                f"You are a scout agent in a DeFi swarm. "
                f"Summarize this opportunity as a JSON task for a strategy agent. "
                f"Be concise. Opportunity: {json.dumps(opportunity)}"
            )
        }]
    )
    return response.content[0].text


def _run_scout_cycle(axl, our_peer_id, cycle: int):
    """Execute a single scout scan-discover-send cycle."""
    trace_id = str(uuid.uuid4())[:8]
    my_name = f"scout.{ENS_PARENT}"

    separator(f"SCOUT CYCLE #{cycle} (trace: {trace_id})")

    # 1. Scan for opportunity
    log("scout", f"Scanning for opportunity...", "cyan")
    opportunity = detect_opportunity()
    log("scout", f"🎯 Opportunity: {opportunity['signal']}", "yellow")
    log("scout", f"   Confidence: {opportunity['confidence']*100:.0f}%", "yellow")
    log("scout", f"   Est. profit: {opportunity['estimated_profit_bps']} bps", "yellow")

    # 2. Discover agents via ENS — DYNAMIC, NOT HARDCODED
    separator("ENS Discovery")
    resolver = get_resolver()

    log("scout", f"Querying {ENS_PARENT} registry...", "yellow")
    all_agents = resolver.discover_agents(ENS_PARENT)
    log("scout", f"Registry has {len(all_agents)} active agent(s):", "cyan")
    for agent in all_agents:
        log("scout", f"  • {agent['name']} → caps: {agent['capabilities']}, rep: {agent['reputation']}", "cyan")

    # Find best agent with "analyze" capability
    log("scout", "Finding best agent with 'analyze' capability...", "yellow")
    strategy = resolver.find_best_agent(ENS_PARENT, capability="analyze")

    if not strategy:
        log("scout", "No suitable analyst agent found in ENS — skipping cycle", "red")
        return

    log("scout", f"Selected: {strategy['name']}", "green")
    log("scout", f"  peer_id:      {strategy['peer_id'][:20]}...", "green")
    log("scout", f"  capabilities: {strategy['capabilities']}", "green")
    log("scout", f"  reputation:   {strategy['reputation']}/5.0", "green")

    # 3. Build structured task message
    msg = create_message(
        msg_type=MSG_TASK,
        from_agent=my_name,
        to_agent=strategy["name"],
        payload={
            "task": "analyze_and_decide",
            "from_peer_id": our_peer_id,
            "opportunity": opportunity,
            "priority": "high",
        },
        trace_id=trace_id,
    )
    log("scout", f"Message ready: type={msg['type']}, trace={msg['trace_id']}", "cyan")

    # 4. Send to Strategy via AXL (P2P encrypted, zero server)
    separator("Sending to Strategy via AXL (P2P)")
    success_sent = axl.send(strategy["peer_id"], serialize(msg))

    if success_sent:
        log("scout", "Task dispatched to Strategy agent ✓", "green")
        log("scout", "Flow: ENS registry → capability filter → peer_id → AXL P2P", "cyan")
    else:
        log("scout", "Failed to dispatch task", "red")
        return

    # 5. Wait for acknowledgement
    ack_msg, ack_peer = axl.recv_message(timeout=20)
    if ack_msg:
        log("scout", f"Got ack from {ack_msg.get('from', 'unknown')}: {ack_msg.get('type', '?')}", "green")


def main():
    """Scout agent main loop — scans for opportunities on an interval."""
    separator("SCOUT AGENT STARTING")
    log("scout", f"AXL port: {AXL_PORT} | loop interval: {LOOP_INTERVAL}s", "cyan")

    # Connect to our AXL node
    axl = AXLClient(port=AXL_PORT, agent_name="scout")
    our_peer_id = axl.get_peer_id()
    log("scout", f"My peer_id: {our_peer_id[:20]}...", "cyan")

    cycle = 0
    try:
        while True:
            cycle += 1
            log("scout", f"[SCOUT] Cycle #{cycle} — scanning...", "cyan")
            _run_scout_cycle(axl, our_peer_id, cycle)
            log("scout", f"Sleeping {LOOP_INTERVAL}s before next scan...", "cyan")
            time.sleep(LOOP_INTERVAL)
    except KeyboardInterrupt:
        log("scout", "[SCOUT] Shutting down gracefully", "yellow")
        sys.exit(0)


if __name__ == "__main__":
    main()
