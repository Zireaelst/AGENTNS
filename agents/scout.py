"""
agents/scout.py
Scout Agent (scout.agentns.eth)
  • Loops every SCOUT_INTERVAL seconds (default 30)
  • Fetches real ETH price from CoinGecko API
  • Calculates imbalance signal + confidence
  • Resolves strategy.agentns.eth via ENS (no central registry)
  • Sends task to Strategy via AXL (P2P encrypted)

Run: python -m agents.scout
"""

import os, sys, json, time, signal, requests
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from dotenv import load_dotenv
load_dotenv()

from utils.axl_client  import AXLClient
from utils.ens_resolver import get_resolver
from utils.logger       import log, phase, banner

AXL_PORT       = int(os.getenv("SCOUT_AXL_PORT", "9002"))
STRATEGY_ENS   = "strategy.agentns.eth"
SCAN_INTERVAL  = int(os.getenv("SCOUT_INTERVAL", "30"))
MIN_CONFIDENCE = float(os.getenv("MIN_CONFIDENCE", "0.6"))

# Graceful shutdown
_running = True
signal.signal(signal.SIGINT,  lambda *_: globals().update(_running=False))
signal.signal(signal.SIGTERM, lambda *_: globals().update(_running=False))


# ── Market scanning ──────────────────────────────────────────────────────────

def fetch_opportunity() -> dict:
    """
    Fetch real ETH/USDC price from CoinGecko and derive an opportunity signal.
    Falls back to simulated data if API is unavailable.
    """
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "ethereum,usd-coin", "vs_currencies": "usd"},
            timeout=8,
        )
        r.raise_for_status()
        data     = r.json()
        eth_usd  = data["ethereum"]["usd"]
        usdc_usd = data["usd-coin"]["usd"]

        # Simple imbalance: how far USDC drifted from $1 peg relative to ETH
        peg_drift   = abs(usdc_usd - 1.0)
        price_score = min(peg_drift * 50, 0.95)           # scale to 0-0.95
        vol_bump    = 0.05 if eth_usd > 2000 else 0.0     # bonus if ETH active
        confidence  = round(min(price_score + vol_bump + 0.65, 0.99), 2)

        return {
            "type":       "defi_opportunity",
            "signal":     f"ETH/USDC pool opportunity — ETH=${eth_usd:,.0f}, USDC peg drift={peg_drift:.4f}",
            "confidence": confidence,
            "token_in":   "USDC",
            "token_out":  "ETH",
            "amount":     "500",
            "eth_price":  eth_usd,
            "usdc_price": usdc_usd,
            "source":     "coingecko_live",
            "timestamp":  int(time.time()),
        }
    except Exception as e:
        log("scout", f"CoinGecko unavailable ({e}) — using simulated signal", ok=False)
        return {
            "type":       "defi_opportunity",
            "signal":     "ETH/USDC pool imbalance detected (simulated)",
            "confidence": 0.87,
            "token_in":   "USDC",
            "token_out":  "ETH",
            "amount":     "500",
            "source":     "simulated",
            "timestamp":  int(time.time()),
        }


# ── Main ─────────────────────────────────────────────────────────────────────

def run_cycle(axl: AXLClient, resolver, cycle: int) -> bool:
    """Single scan-dispatch cycle. Returns True if task was sent."""

    phase(f"Scout Cycle #{cycle} — Scanning Market")

    # 1. Fetch opportunity
    opp = fetch_opportunity()
    log("scout", f"Signal:     {opp['signal']}")
    log("scout", f"Confidence: {opp['confidence']} (min={MIN_CONFIDENCE})")

    if opp["confidence"] < MIN_CONFIDENCE:
        log("scout", f"Confidence too low — skipping", ok=False)
        return False

    # 2. Resolve Strategy via ENS (core feature — no central registry)
    phase("ENS Discovery → strategy.agentns.eth")
    strategy = resolver.resolve(STRATEGY_ENS)
    if not strategy:
        log("scout", f"Cannot resolve {STRATEGY_ENS}", ok=False)
        return False

    log("scout", f"Resolved:   {STRATEGY_ENS}")
    log("scout", f"peer_id:    {strategy['peer_id'][:20]}…")
    log("scout", f"caps:       {strategy['capabilities']}")
    log("scout", f"reputation: {strategy['reputation']}")

    # 3. Build task envelope
    task = {
        "type":          "task",
        "from":          "scout.agentns.eth",
        "from_peer_id":  axl.peer_id(),
        "opportunity":   opp,
        "timestamp":     int(time.time()),
    }

    # 4. Send via AXL (encrypted P2P — no server, no broker)
    phase("AXL → Dispatch to Strategy (P2P encrypted)")
    ok = axl.send(strategy["peer_id"], task)
    if ok:
        log("scout", "Task dispatched via AXL ✓")
    else:
        log("scout", "AXL send failed", ok=False)
        return False

    # 5. Wait for ack
    log("scout", "Waiting for ack from Strategy…")
    ack = axl.recv(timeout=20)
    if ack:
        log("scout", f"Got ack: {ack['data'].get('status', '?')}")
    else:
        log("scout", "No ack (strategy may still be processing)", ok=False)

    return True


def main():
    banner("SCOUT AGENT — scout.agentns.eth",
           "Scan → ENS discover → AXL dispatch")

    axl = AXLClient(AXL_PORT, "scout")
    log("scout", f"Connecting to AXL node on port {AXL_PORT}…")
    if not axl.wait_ready():
        log("scout", "AXL node not available — run setup/1_run_axl_nodes.sh", ok=False)
        sys.exit(1)
    log("scout", f"AXL ready. peer_id={axl.peer_id()[:20]}…")

    resolver = get_resolver()
    cycle    = 0

    while _running:
        cycle += 1
        try:
            run_cycle(axl, resolver, cycle)
        except Exception as e:
            log("scout", f"Cycle error: {e}", ok=False)

        if _running:
            log("scout", f"Next scan in {SCAN_INTERVAL}s… (Ctrl+C to stop)")
            for _ in range(SCAN_INTERVAL):
                if not _running:
                    break
                time.sleep(1)

    log("scout", "Shutting down gracefully ✓")


if __name__ == "__main__":
    main()
