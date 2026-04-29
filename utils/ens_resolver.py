"""
utils/ens_resolver.py
ENS-based agent discovery and identity for AGENTNS.
Reads text records from Sepolia testnet — no wallet required (read-only).

Key innovation: ENS is the ONLY registry. Agents discover peers by:
  1. Reading the parent domain's "registry" text record → list of subnames
  2. Resolving each subname → peer_id, capabilities, reputation
  3. Filtering by capability + sorting by reputation → best agent found

Usage:
    resolver = get_resolver()
    agents   = resolver.discover_agents("agentns.eth")
    best     = resolver.find_best_agent("agentns.eth", capability="analyze")
    profile  = resolver.resolve_agent("scout.agentns.eth")
"""

import os
import json
from utils.logger import log, success, info, detail

# ─── ENS Config ──────────────────────────────────────────────────
ENS_PARENT = os.getenv("ENS_PARENT", "agentns.eth")

# ENS Public Resolver on Sepolia
ENS_PUBLIC_RESOLVER_SEPOLIA = "0x8FADE66B79cC9f707aB26799354482EB93a5B7dD"

# ABI for text() function only
RESOLVER_ABI = [
    {
        "inputs": [
            {"internalType": "bytes32", "name": "node", "type": "bytes32"},
            {"internalType": "string",  "name": "key",  "type": "string"},
        ],
        "name": "text",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function",
    }
]


# ═══════════════════════════════════════════════════════════════════
# REAL ENS RESOLVER — reads from Sepolia testnet
# ═══════════════════════════════════════════════════════════════════

class ENSResolver:
    def __init__(self):
        from web3 import Web3
        from eth_ens_namehash import compute_namehash

        rpc = os.getenv("RPC_URL", "https://rpc.ankr.com/eth_sepolia")
        self.w3 = Web3(Web3.HTTPProvider(rpc))
        self.resolver = self.w3.eth.contract(
            address=ENS_PUBLIC_RESOLVER_SEPOLIA,
            abi=RESOLVER_ABI,
        )
        self._namehash_fn = compute_namehash
        self._cache: dict[str, dict] = {}

    def _namehash(self, name: str) -> bytes:
        return bytes.fromhex(self._namehash_fn(name).hex())

    # ─── Core: Read any text record ──────────────────────────────

    def get_text(self, ens_name: str, key: str) -> str | None:
        """Generic text record reader."""
        try:
            node = self._namehash(ens_name)
            value = self.resolver.functions.text(node, key).call()
            return value if value else None
        except Exception as e:
            log("ens", f"Failed to read {key} from {ens_name}: {e}", "red")
            return None

    def get_peer_id(self, ens_name: str) -> str | None:
        """Get AXL peer ID stored in 'axl-peer-id' text record."""
        peer_id = self.get_text(ens_name, "axl-peer-id")
        if peer_id:
            log("ens", f"Resolved {ens_name} → peer_id: {peer_id[:16]}...", "cyan")
        return peer_id

    def get_capabilities(self, ens_name: str) -> list[str]:
        """Get capabilities list from 'capabilities' text record."""
        caps_str = self.get_text(ens_name, "capabilities")
        if caps_str:
            return [c.strip() for c in caps_str.split(",")]
        return []

    # ─── Agent Resolution ────────────────────────────────────────

    def resolve_agent(self, ens_name: str) -> dict | None:
        """
        Full agent profile from ENS text records.
        Returns: {name, peer_id, capabilities, reputation, status}
        """
        if ens_name in self._cache:
            log("ens", f"Cache hit: {ens_name}", "yellow")
            return self._cache[ens_name]

        log("ens", f"Resolving {ens_name}...", "yellow")
        peer_id = self.get_peer_id(ens_name)
        if not peer_id:
            log("ens", f"No axl-peer-id found for {ens_name}", "red")
            return None

        caps = self.get_capabilities(ens_name)
        reputation = float(self.get_text(ens_name, "reputation") or "0.0")
        status = self.get_text(ens_name, "status") or "active"

        profile = {
            "name": ens_name,
            "peer_id": peer_id,
            "capabilities": caps,
            "reputation": reputation,
            "status": status,
        }
        self._cache[ens_name] = profile
        log("ens", f"✓ {ens_name}: caps={caps}, rep={reputation}", "green")
        return profile

    # ─── Discovery: The ENS-native agent registry ────────────────

    def get_registry(self, parent_name: str = None) -> list[str]:
        """
        Read the 'registry' text record from parent domain.
        Returns list of full subnames, e.g. ["scout.agentns.eth", ...]
        """
        parent = parent_name or ENS_PARENT
        registry_str = self.get_text(parent, "registry")
        if not registry_str:
            return []
        labels = [l.strip() for l in registry_str.split(",") if l.strip()]
        return [f"{label}.{parent}" for label in labels]

    def discover_agents(self, parent_name: str = None, capability: str = None) -> list[dict]:
        """
        Discover all agents under a parent ENS domain.
        Optionally filter by capability.
        """
        parent = parent_name or ENS_PARENT
        subnames = self.get_registry(parent)
        agents = []
        for name in subnames:
            profile = self.resolve_agent(name)
            if profile and profile["status"] == "active":
                if capability is None or capability in profile["capabilities"]:
                    agents.append(profile)
        return sorted(agents, key=lambda a: a["reputation"], reverse=True)

    def find_best_agent(self, parent_name: str = None, capability: str = None, min_reputation: float = 3.0) -> dict | None:
        """
        Find the highest-reputation agent with a given capability.
        Skips agents below min_reputation threshold.
        """
        parent = parent_name or ENS_PARENT
        candidates = self.discover_agents(parent, capability)
        qualified = [a for a in candidates if a["reputation"] >= min_reputation]
        if qualified:
            best = qualified[0]  # already sorted by reputation desc
            log("ens", f"Best agent for '{capability}': {best['name']} (rep: {best['reputation']})", "green")
            return best
        log("ens", f"No agent found for capability '{capability}' with rep >= {min_reputation}", "red")
        return None


# ═══════════════════════════════════════════════════════════════════
# MOCK ENS RESOLVER — for demo without real ENS records
# Provides identical API with realistic mock data
# ═══════════════════════════════════════════════════════════════════

class MockENSResolver:
    """
    Demo-mode resolver — reads peer IDs from env, simulates ENS lookup.
    Provides full discovery API identical to the real resolver.
    """

    def __init__(self):
        self._parent = ENS_PARENT
        self.records = {
            f"scout.{self._parent}": {
                "name": f"scout.{self._parent}",
                "peer_id": os.getenv("SCOUT_PEER_ID", "MOCK_SCOUT_PEER_ID_" + "a" * 40),
                "capabilities": ["scan", "discover", "monitor"],
                "reputation": 4.8,
                "status": "active",
            },
            f"strategy.{self._parent}": {
                "name": f"strategy.{self._parent}",
                "peer_id": os.getenv("STRATEGY_PEER_ID", "MOCK_STRATEGY_PEER_ID_" + "b" * 40),
                "capabilities": ["analyze", "decide", "risk-assess"],
                "reputation": 4.9,
                "status": "active",
            },
            f"executor.{self._parent}": {
                "name": f"executor.{self._parent}",
                "peer_id": os.getenv("EXECUTOR_PEER_ID", "MOCK_EXECUTOR_PEER_ID_" + "c" * 40),
                "capabilities": ["execute", "submit", "swap"],
                "reputation": 5.0,
                "status": "active",
            },
        }
        # Parent domain registry
        self._registry = {
            self._parent: {
                "registry": "scout,strategy,executor",
                "protocol-version": "1.0",
            }
        }

    def get_text(self, ens_name: str, key: str) -> str | None:
        """Mock text record reader."""
        # Check parent domain records first
        if ens_name in self._registry:
            return self._registry[ens_name].get(key)
        # Check agent records
        agent = self.records.get(ens_name)
        if not agent:
            return None
        if key == "axl-peer-id":
            return agent["peer_id"]
        elif key == "capabilities":
            return ",".join(agent["capabilities"])
        elif key == "reputation":
            return str(agent["reputation"])
        elif key == "status":
            return agent["status"]
        return None

    def resolve_agent(self, ens_name: str) -> dict | None:
        """Resolve a single agent — mock version."""
        log("ens", f"Resolving {ens_name} via ENS...", "yellow")
        result = self.records.get(ens_name)
        if result:
            log("ens", f"✓ {ens_name} → peer_id: {result['peer_id'][:16]}...", "green")
        else:
            log("ens", f"✗ {ens_name} not found in ENS", "red")
        return result

    def get_peer_id(self, ens_name: str) -> str | None:
        agent = self.records.get(ens_name)
        return agent["peer_id"] if agent else None

    def get_capabilities(self, ens_name: str) -> list[str]:
        agent = self.records.get(ens_name)
        return agent["capabilities"] if agent else []

    # ─── Discovery API (identical to real resolver) ──────────────

    def get_registry(self, parent_name: str = None) -> list[str]:
        """Read the registry from parent domain — mock version."""
        parent = parent_name or self._parent
        registry_str = self._registry.get(parent, {}).get("registry", "")
        if not registry_str:
            return []
        labels = [l.strip() for l in registry_str.split(",") if l.strip()]
        return [f"{label}.{parent}" for label in labels]

    def discover_agents(self, parent_name: str = None, capability: str = None) -> list[dict]:
        """Discover all agents — mock version."""
        parent = parent_name or self._parent
        log("ens", f"Querying {parent} registry...", "yellow")
        subnames = self.get_registry(parent)
        agents = []
        for name in subnames:
            profile = self.records.get(name)
            if profile and profile.get("status") == "active":
                if capability is None or capability in profile["capabilities"]:
                    agents.append(profile)
        result = sorted(agents, key=lambda a: a["reputation"], reverse=True)
        log("ens", f"Found {len(result)} agent(s)" + (f" with '{capability}'" if capability else ""), "green")
        return result

    def find_best_agent(self, parent_name: str = None, capability: str = None, min_reputation: float = 3.0) -> dict | None:
        """Find best agent by capability + reputation — mock version."""
        parent = parent_name or self._parent
        candidates = self.discover_agents(parent, capability)
        qualified = [a for a in candidates if a["reputation"] >= min_reputation]
        if qualified:
            best = qualified[0]
            log("ens", f"Best agent for '{capability}': {best['name']} (rep: {best['reputation']})", "green")
            return best
        log("ens", f"No agent found for capability '{capability}'", "red")
        return None

    def update_reputation(self, ens_name: str, delta: float):
        """
        Update agent reputation after collaboration.
        In real mode: this would write to ENS (requires wallet tx).
        In mock: update local state + log the simulated tx.
        """
        if ens_name in self.records:
            old = self.records[ens_name]["reputation"]
            new = min(5.0, round(old + delta, 2))
            self.records[ens_name]["reputation"] = new
            tx_hash = f"0x{'f' * 8}{hash(ens_name) % 10**8:08d}"
            log("ens", f"Reputation updated: {ens_name} {old} → {new} (tx: {tx_hash[:18]}...)", "green")
            return {"old": old, "new": new, "tx_hash": tx_hash}
        return None


# ═══════════════════════════════════════════════════════════════════
# FACTORY
# ═══════════════════════════════════════════════════════════════════

def get_resolver():
    """Factory: returns real or mock resolver based on DEMO_MODE."""
    mode = os.getenv("DEMO_MODE", "mock")
    if mode == "mock":
        log("ens", "Using mock ENS resolver (DEMO_MODE=mock)", "yellow")
        return MockENSResolver()
    log("ens", "Using real ENS resolver (Sepolia)", "cyan")
    return ENSResolver()
