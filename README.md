# AGENTNS — Decentralized Multi-Agent System

> AI agents that discover each other via ENS, communicate via Gensyn AXL, execute via KeeperHub.
> No central registry. No servers. Just P2P.

## System Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                        AGENTNS SYSTEM                           │
│                                                                 │
│  ENS Sepolia (Identity + Discovery)                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  scout.agentns.eth     → axl-peer-id: <pubkey_A>        │   │
│  │                          capabilities: "scan,discover"  │   │
│  │  strategy.agentns.eth  → axl-peer-id: <pubkey_B>        │   │
│  │                          capabilities: "analyze,decide" │   │
│  │  executor.agentns.eth  → axl-peer-id: <pubkey_C>        │   │
│  │                          capabilities: "execute,submit" │   │
│  └──────────────────────────────────────────────────────────┘   │
│            ▲ resolve                   ▲ resolve                │
│            │                          │                         │
│  ┌─────────┴──────┐         ┌─────────┴──────┐                  │
│  │  Scout Agent   │──AXL──▶│Strategy Agent  │                  │
│  │  :9002         │◀──AXL──│  :9012         │                  │
│  └────────────────┘         └───────┬────────┘                  │
│                                     │ AXL                       │
│                             ┌───────▼────────┐                  │
│                             │Executor Agent  │──▶ KeeperHub    │
│                             │  :9022         │    (onchain)    │
│                             └────────────────┘                  │
└─────────────────────────────────────────────────────────────────┘
```

## Deep-Dive Documentation & Mathematics

To understand the core mechanisms, cryptography, and fallback mathematics behind AGENTNS, please refer to our detailed documentation suite:

- 📖 **[ENS Integration & Identity Mechanics](docs/ENS_INTEGRATION.md)**
  *Explains the EIP-137 namehash mapping, text records bypass, and the `pending` nonce mechanic used to calculate and update cross-agent reputation without transaction collision.*
- 🌐 **[Gensyn AXL Mesh Network](docs/AXL_MESH_NETWORK.md)**
  *Explains the Ed25519 Peer ID cryptography, macOS port mapping logic (`7700-7702`), and secure JSON envelope routing over bare TCP.*
- 🧠 **[KeeperHub & LLM Orchestration](docs/KEEPERHUB_EXECUTION.md)**
  *Explains the mathematical fallback protection for LLM rate-limits and the gas projection algorithm used by KeeperHub to prevent MEV extraction.*
- 🔗 **[Proof of Work (On-Chain Traces)](docs/PROOF_OF_WORK.md)**
  *Live transaction links and execution traces proving the system runs natively on the Ethereum Sepolia Testnet.*

## Quick Start (V2 - Live Mode)

```bash
# 1. Clone AXL + build binary
git clone https://github.com/gensyn-ai/axl.git
cd axl && go build -o node ./cmd/node/ && cd ..

# 2. Setup Virtual Environment
python3 -m venv venv
source venv/bin/activate

# 3. Install deps
pip install -r requirements.txt
npm install

# 4. Configure
cp .env.example .env
# Fill in PRIVATE_KEY, RPC_URL (Sepolia), and set DEMO_MODE=real

# 5. Start AXL nodes (3 nodes)
bash setup/1_run_axl_nodes.sh

# 6. Register ENS subnames + set text records
node setup/2_register_ens.js

# 7. Export AXL peer IDs to .env
bash setup/3_export_keys.sh

# 8. Install tmux (Mac Users)
brew install tmux

# 9. Run the Live Demo (Matrix Style)
bash demo.sh --tmux
```

## Prize Tracks

| Sponsor | Track | Integration |
|---|---|---|
| ENS | AI Agents for ENS | Discovery via subnames + text records |
| ENS | Most Creative Use | AXL peer IDs stored in text records — P2P mesh via DNS |
| Gensyn | Best AXL Application | Full P2P agent comms, 3 separate nodes |
| KeeperHub | Best Innovative Use | Autonomous agent → guaranteed onchain execution |
