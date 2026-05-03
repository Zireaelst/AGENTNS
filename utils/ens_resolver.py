"""
utils/ens_resolver.py
Read agent profiles from ENS text records.

Real mode (DEMO_MODE=real):
  Uses web3.py to call ENS Public Resolver on Sepolia.
  Reads text records: axl-peer-id, capabilities, reputation

Mock mode (DEMO_MODE=mock):
  Returns profiles built from .env PEER_IDs.
  Used for local testing before ENS is deployed.

Text records written by setup/2_register_ens.js:
  axl-peer-id   → 64-char hex public key from AXL node
  capabilities  → comma-separated: "scan,discover"
  reputation    → float string: "4.8"
"""

import os
from utils.logger import log

# ENS Public Resolver on Sepolia
_RESOLVER_ADDR = "0x8FADE66B79cC9f707aB26799354482EB93a5B7dD"
_RESOLVER_ABI  = [{"name":"text","type":"function","stateMutability":"view",
                   "inputs":[{"name":"node","type":"bytes32"},{"name":"key","type":"string"}],
                   "outputs":[{"name":"","type":"string"}]}]

# Module-level export for backward compat (demo_runner.py, agentns_cli.py)
ENS_PARENT = os.getenv("ENS_PARENT", "agentns.eth")


class ENSResolver:
    """Live resolver — reads Sepolia ENS text records via RPC."""

    def __init__(self):
        from web3 import Web3
        from ens.utils import raw_name_to_hash as compute_namehash
        rpc = os.environ["RPC_URL"]
        self.w3 = Web3(Web3.HTTPProvider(rpc))
        self._nh  = compute_namehash
        self._res = self.w3.eth.contract(address=_RESOLVER_ADDR, abi=_RESOLVER_ABI)
        self._cache: dict[str, dict] = {}

    def _node(self, name: str) -> bytes:
        return bytes.fromhex(self._nh(name).hex())

    def _txt(self, name: str, key: str) -> str:
        return self._res.functions.text(self._node(name), key).call()

    def resolve(self, ens_name: str) -> dict | None:
        if ens_name in self._cache:
            return self._cache[ens_name]
        log("ens", f"Resolving {ens_name} on Sepolia…")
        try:
            peer_id = self._txt(ens_name, "axl-peer-id")
            if not peer_id:
                log("ens", f"No axl-peer-id for {ens_name}", ok=False)
                return None
            caps       = [c.strip() for c in (self._txt(ens_name, "capabilities") or "").split(",") if c]
            reputation = float(self._txt(ens_name, "reputation") or "0")
            profile = {"name": ens_name, "peer_id": peer_id, "capabilities": caps,
                       "reputation": reputation, "status": "active"}
            self._cache[ens_name] = profile
            log("ens", f"✓ {ens_name} → {peer_id[:14]}… caps={caps} rep={reputation}")
            return profile
        except Exception as e:
            log("ens", f"resolve failed for {ens_name}: {e}", ok=False)
            return None

    # V1 compat alias
    resolve_agent = resolve

    def update_reputation(self, ens_name: str, new_score_or_delta: float) -> dict | str | None:
        """Write updated reputation score back to ENS text record (needs wallet).
        Accepts either absolute score (V2) or small delta (V1 compat)."""
        # If it looks like a delta (<1), treat as delta
        if new_score_or_delta < 1.0:
            profile = self.resolve(ens_name)
            if profile:
                new_score = round(min(profile["reputation"] + new_score_or_delta, 5.0), 2)
            else:
                return None
        else:
            new_score = new_score_or_delta

        from web3 import Web3
        pkey = os.getenv("PRIVATE_KEY")
        if not pkey:
            log("ens", "No PRIVATE_KEY — skipping reputation write", ok=False)
            return None
        abi = [{"name":"setText","type":"function","stateMutability":"nonpayable",
                "inputs":[{"name":"node","type":"bytes32"},
                           {"name":"key","type":"string"},
                           {"name":"value","type":"string"}],
                "outputs":[]}]
        contract = self.w3.eth.contract(address=_RESOLVER_ADDR, abi=abi)
        account  = self.w3.eth.account.from_key(pkey)
        nonce    = self.w3.eth.get_transaction_count(account.address, 'pending')
        tx = contract.functions.setText(
            self._node(ens_name), "reputation", str(new_score)
        ).build_transaction({
            "chainId": 11155111,
            "from":    account.address,
            "nonce":   nonce,
            "gas":     80000,
            "gasPrice": self.w3.eth.gas_price,
        })
        signed = self.w3.eth.account.sign_transaction(tx, pkey)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction).hex()
        self.w3.eth.wait_for_transaction_receipt(tx_hash)
        if ens_name in self._cache:
            self._cache[ens_name]["reputation"] = new_score
        log("ens", f"Reputation updated: {ens_name} → {new_score} | tx={tx_hash[:14]}…")
        return tx_hash

    # V1 compat methods
    def get_peer_id(self, ens_name: str) -> str | None:
        p = self.resolve(ens_name)
        return p["peer_id"] if p else None

    def get_capabilities(self, ens_name: str) -> list[str]:
        p = self.resolve(ens_name)
        return p["capabilities"] if p else []

    def get_text(self, ens_name: str, key: str) -> str | None:
        try:
            return self._txt(ens_name, key)
        except Exception:
            return None

    def get_registry(self, parent_name: str = None) -> list[str]:
        parent = parent_name or ENS_PARENT
        reg = self.get_text(parent, "registry")
        if not reg:
            return []
        labels = [l.strip() for l in reg.split(",") if l.strip()]
        return [f"{label}.{parent}" for label in labels]

    def discover_agents(self, parent_name: str = None, capability: str = None) -> list[dict]:
        parent = parent_name or ENS_PARENT
        subnames = self.get_registry(parent)
        agents = []
        for name in subnames:
            profile = self.resolve(name)
            if profile and profile.get("status") == "active":
                if capability is None or capability in profile["capabilities"]:
                    agents.append(profile)
        return sorted(agents, key=lambda a: a["reputation"], reverse=True)

    def find_best_agent(self, parent_name=None, capability=None, min_reputation=3.0):
        candidates = self.discover_agents(parent_name, capability)
        qualified = [a for a in candidates if a["reputation"] >= min_reputation]
        if qualified:
            return qualified[0]
        return None


class MockENSResolver:
    """
    Mock resolver for local dev — reads peer IDs from .env.
    Identical interface to ENSResolver.
    """
    def __init__(self):
        self._parent = ENS_PARENT
        self._db = {
            f"scout.{self._parent}": {
                "name": f"scout.{self._parent}",
                "peer_id": os.environ.get("SCOUT_PEER_ID", "MOCK_SCOUT_PEER_ID_" + "a" * 40),
                "capabilities": ["scan", "discover", "monitor"],
                "reputation": 4.8,
                "status": "active",
            },
            f"strategy.{self._parent}": {
                "name": f"strategy.{self._parent}",
                "peer_id": os.environ.get("STRATEGY_PEER_ID", "MOCK_STRATEGY_PEER_ID_" + "b" * 40),
                "capabilities": ["analyze", "decide", "risk-assess"],
                "reputation": 4.9,
                "status": "active",
            },
            f"executor.{self._parent}": {
                "name": f"executor.{self._parent}",
                "peer_id": os.environ.get("EXECUTOR_PEER_ID", "MOCK_EXECUTOR_PEER_ID_" + "c" * 40),
                "capabilities": ["execute", "submit", "swap"],
                "reputation": 5.0,
                "status": "active",
            },
        }
        self._registry = {
            self._parent: {"registry": "scout,strategy,executor"}
        }

    def resolve(self, ens_name: str) -> dict | None:
        log("ens", f"[MOCK] {ens_name}…")
        p = self._db.get(ens_name)
        if p:
            log("ens", f"[MOCK] ✓ {ens_name} → {p['peer_id'][:14]}…")
        else:
            log("ens", f"[MOCK] not found: {ens_name}", ok=False)
        return p

    # V1 compat alias
    resolve_agent = resolve

    def update_reputation(self, ens_name: str, new_score_or_delta: float) -> dict | str | None:
        """Accept either absolute score (V2) or small delta (V1 compat)."""
        if new_score_or_delta < 1.0:
            # V1 delta mode
            if ens_name in self._db:
                old = self._db[ens_name]["reputation"]
                new = min(5.0, round(old + new_score_or_delta, 2))
                self._db[ens_name]["reputation"] = new
                tx_hash = f"0x{'f' * 8}{hash(ens_name) % 10**8:08d}"
                log("ens", f"[MOCK] reputation {ens_name}: {old} → {new} (tx: {tx_hash[:18]}…)")
                return {"old": old, "new": new, "tx_hash": tx_hash}
        else:
            # V2 absolute mode
            if ens_name in self._db:
                self._db[ens_name]["reputation"] = new_score_or_delta
            log("ens", f"[MOCK] reputation {ens_name} → {new_score_or_delta}")
        return None

    def get_peer_id(self, ens_name: str) -> str | None:
        agent = self._db.get(ens_name)
        return agent["peer_id"] if agent else None

    def get_capabilities(self, ens_name: str) -> list[str]:
        agent = self._db.get(ens_name)
        return agent["capabilities"] if agent else []

    def get_text(self, ens_name: str, key: str) -> str | None:
        if ens_name in self._registry:
            return self._registry[ens_name].get(key)
        agent = self._db.get(ens_name)
        if not agent:
            return None
        if key == "axl-peer-id":
            return agent["peer_id"]
        elif key == "capabilities":
            return ",".join(agent["capabilities"])
        elif key == "reputation":
            return str(agent["reputation"])
        elif key == "status":
            return agent.get("status", "active")
        return None

    def get_registry(self, parent_name: str = None) -> list[str]:
        parent = parent_name or self._parent
        registry_str = self._registry.get(parent, {}).get("registry", "")
        if not registry_str:
            return []
        labels = [l.strip() for l in registry_str.split(",") if l.strip()]
        return [f"{label}.{parent}" for label in labels]

    def discover_agents(self, parent_name: str = None, capability: str = None) -> list[dict]:
        parent = parent_name or self._parent
        log("ens", f"[MOCK] Querying {parent} registry…")
        subnames = self.get_registry(parent)
        agents = []
        for name in subnames:
            profile = self._db.get(name)
            if profile and profile.get("status") == "active":
                if capability is None or capability in profile["capabilities"]:
                    agents.append(profile)
        result = sorted(agents, key=lambda a: a["reputation"], reverse=True)
        log("ens", f"[MOCK] Found {len(result)} agent(s)" + (f" with '{capability}'" if capability else ""))
        return result

    def find_best_agent(self, parent_name=None, capability=None, min_reputation=3.0):
        candidates = self.discover_agents(parent_name, capability)
        qualified = [a for a in candidates if a["reputation"] >= min_reputation]
        if qualified:
            best = qualified[0]
            log("ens", f"[MOCK] Best for '{capability}': {best['name']} (rep: {best['reputation']})")
            return best
        log("ens", f"[MOCK] No agent for capability '{capability}'", ok=False)
        return None


def get_resolver() -> ENSResolver | MockENSResolver:
    """Factory: returns live or mock resolver based on DEMO_MODE env var."""
    if os.environ.get("DEMO_MODE", "mock") == "real":
        return ENSResolver()
    return MockENSResolver()
