# AGENTNS — Decentralized Multi-Agent System

> AI agents that discover each other via ENS, communicate via Gensyn AXL, execute via KeeperHub.
> No central registry. No servers. Just P2P.

## Architecture

```
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

Flow:
1. Scout detects opportunity → resolves strategy.agentns.eth via ENS
2. Gets strategy's AXL peer ID from text record
3. Sends task via AXL (P2P encrypted, no server)
4. Strategy analyzes → resolves executor.agentns.eth
5. Sends execution order via AXL
6. Executor submits to KeeperHub → onchain tx confirmed
```

## Project Structure

```
agentns/
├── README.md
├── .env.example
├── requirements.txt
├── package.json                 # for ENS scripts
│
├── setup/
│   ├── 1_run_axl_nodes.sh       # Start 3 AXL nodes
│   ├── 2_register_ens.js        # Create subnames + set text records
│   └── 3_export_keys.sh         # Export peer IDs to .env
│
├── agents/
│   ├── scout.py                 # Finds opportunities, triggers flow
│   ├── strategy.py              # Analyzes task, decides action
│   └── executor.py              # Executes onchain via KeeperHub
│
├── utils/
│   ├── axl_client.py            # AXL HTTP wrapper
│   ├── ens_resolver.py          # ENS text record reader (web3.py)
│   └── logger.py                # Colored terminal output
│
└── demo.sh                      # One-command demo runner
```

## Quick Start

```bash
# 1. Clone AXL + build binary
git clone https://github.com/gensyn-ai/axl.git
cd axl && go build -o node ./cmd/node/ && cd ..

# 2. Install deps
pip install -r requirements.txt
npm install

# 3. Configure
cp .env.example .env
# Fill in PRIVATE_KEY, RPC_URL (Sepolia)

# 4. Start AXL nodes (3 terminals)
bash setup/1_run_axl_nodes.sh

# 5. Register ENS subnames + set text records
node setup/2_register_ens.js

# 6. Export AXL peer IDs to .env
bash setup/3_export_keys.sh

# 7. Run demo
bash demo.sh
```

## Prize Tracks

| Sponsor | Track | Integration |
|---|---|---|
| ENS | AI Agents for ENS | Discovery via subnames + text records |
| ENS | Most Creative Use | AXL peer IDs stored in text records — P2P mesh via DNS |
| Gensyn | Best AXL Application | Full P2P agent comms, 3 separate nodes |
| KeeperHub | Best Innovative Use | Autonomous agent → guaranteed onchain execution |
