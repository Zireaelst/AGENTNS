# AGENTNS — Hackathon Submission Guide

## Prize Targets

| Partner | Track | Your Integration | Max Prize |
|---|---|---|---|
| **ENS** | AI Agents for ENS | Agents discovered via subname text records | $1,250 |
| **ENS** | Most Creative Use | AXL peer IDs stored in ENS — DNS as P2P mesh directory | $1,250 |
| **Gensyn** | Best AXL Application | 3 separate AXL nodes, real P2P inter-agent comms | $2,500 |
| **KeeperHub** | Best Innovative Use | Autonomous agent pipeline → guaranteed onchain tx | $2,500 |
| **KeeperHub** | Feedback Bounty | Docs gaps + UX friction report | $250 |
| **Total** | | | **~$7,750** |

---

## 3-Minute Demo Script

### [00:00 — 00:30] Hook — The Problem

> "AI agents today rely on centralized APIs, shared databases, and cloud infrastructure.
> If the server goes down, the agent stops.
> AGENTNS changes this: a swarm of agents that discovers each other via ENS
> and communicates directly P2P — no servers, no coordinators."

**Show:** Architecture diagram from README

---

### [00:30 — 01:00] ENS Discovery

> "Each agent has an ENS subname on Sepolia."

```bash
# Show in browser: app.ens.domains/scout.agentns.eth
# Click "Text Records" → show axl-peer-id, capabilities, reputation
```

> "When Scout needs Strategy, it doesn't query a database.
> It resolves strategy.agentns.eth and reads the AXL peer ID directly from ENS.
> This is the only 'registry' — fully decentralized, censorship resistant."

**Show:** ENS app with text records visible

---

### [01:00 — 02:00] Live Demo — Run the Agents

```bash
# Terminal 1: Start AXL nodes (if not running)
bash setup/1_run_axl_nodes.sh

# Terminal 2: Run demo (tmux split view)
bash demo.sh --tmux
```

**Walk through the logs as they appear:**

1. `[SCOUT]` Opportunity detected
2. `[SCOUT]` Resolving `strategy.agentns.eth` via ENS...
3. `[SCOUT]` Got peer_id → sending via AXL (P2P encrypted)
4. `[STRATEGY]` Received task from Scout
5. `[STRATEGY]` Claude analyzing opportunity...
6. `[STRATEGY]` Decision: APPROVE → resolving `executor.agentns.eth`
7. `[STRATEGY]` Sending execution order via AXL
8. `[EXECUTOR]` Received order from Strategy
9. `[EXECUTOR]` Submitting to KeeperHub...
10. `[EXECUTOR]` ✓ ONCHAIN — tx_hash: 0x...

---

### [02:00 — 02:30] Bonus Features

**Reputation System:**
> "After each collaboration, agents update each other's reputation in ENS text records.
> Bad actors lose reputation — good agents get more tasks. All onchain, no central authority."

**Dynamic Discovery:**
> "New agents can join the swarm just by registering a subname and setting their AXL peer ID.
> Existing agents will automatically discover them on the next resolution cycle."

---

### [02:30 — 03:00] Closing

> "AGENTNS is the first system where:
> - Agent identity is ENS (not a database)
> - Agent communication is AXL (not a message broker)
> - Agent execution is KeeperHub (not a raw RPC call)
> 
> Every component is decentralized. This is what agentic infrastructure looks like in 2026."

---

## Submission Checklist

### General
- [ ] Project name: AGENTNS
- [ ] Description: Decentralized multi-agent swarm using ENS discovery + Gensyn AXL P2P comms + KeeperHub execution
- [ ] Public GitHub repo with README
- [ ] Demo video < 3 mins
- [ ] Live demo link (deploy to Railway/Render if possible)
- [ ] Team contacts

### ENS Requirements
- [ ] ENS subnames visible on app.ens.domains
- [ ] Text records: `axl-peer-id`, `capabilities`, `reputation`
- [ ] Explain: ENS enables discovery AND is the identity mechanism
- [ ] "Most Creative": AXL peer IDs stored in text records = DNS-as-mesh-directory

### Gensyn Requirements
- [ ] 3 separate AXL nodes (separate processes, different ports)
- [ ] Communication via AXL only (not in-process)
- [ ] Show cross-node messages in logs
- [ ] Architecture diagram

### KeeperHub Requirements
- [ ] Working demo with KeeperHub execution
- [ ] Explain: autonomous agents → KeeperHub → guaranteed tx
- [ ] FEEDBACK.md with honest DX notes (qualifies for $250 bounty)

---

## FEEDBACK.md Template (KeeperHub Bounty)

```markdown
# KeeperHub Builder Feedback

## What Worked Well
- MCP server integration was straightforward
- API response format is clean

## UX Friction
- [Specific thing that slowed you down]
- [Specific thing that was confusing]

## Documentation Gaps
- [Page/section where you got stuck]
- [Missing example that would have helped]

## Bugs Found
- [Reproducible bug with steps]

## Feature Requests
- [Specific feature that would have made your build faster]
```

---

## Architecture Diagram (for submission)

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENTNS SYSTEM                           │
│                                                             │
│  ① ENS Sepolia — Decentralized Identity + Discovery        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ scout.agentns.eth    → axl-peer-id, capabilities     │  │
│  │ strategy.agentns.eth → axl-peer-id, capabilities     │  │
│  │ executor.agentns.eth → axl-peer-id, capabilities     │  │
│  └───────────────────────────────────────────────────────┘  │
│       ↑ resolve()                    ↑ resolve()            │
│                                                             │
│  ② Gensyn AXL — Encrypted P2P Mesh (no server)            │
│  ┌──────────┐   AXL msg    ┌──────────┐   AXL msg          │
│  │  Scout   │ ──────────▶ │ Strategy │ ──────────▶        │
│  │  :9002   │             │  :9012   │                     │
│  └──────────┘             └──────────┘                     │
│                                     │                       │
│                              ┌──────▼───┐                   │
│                              │ Executor │                   │
│                              │  :9022   │                   │
│                              └──────────┘                   │
│                                     │                       │
│  ③ KeeperHub — Guaranteed Onchain Execution                │
│                              ┌──────▼───────────────────┐  │
│                              │ MEV Protection           │  │
│                              │ Retry Logic              │  │
│                              │ Gas Optimization         │  │
│                              │ Full Audit Trail         │  │
│                              └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```
