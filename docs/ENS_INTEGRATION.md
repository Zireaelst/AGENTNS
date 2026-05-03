# ENS Integration & Identity Mechanics

AGENTNS leverages the Ethereum Name Service (ENS) not just for human-readable addresses, but as a **decentralized service registry**. 

Rather than relying on a centralized database to map agent capabilities and network routing, we store this critical information natively on the Sepolia blockchain using **ENS Text Records**.

## 1. Architectural Flow

When an agent needs to communicate with another agent in the swarm, it performs the following steps:
1. **Resolution**: Queries the Web3 RPC for the target subname (e.g., `strategy.agentns.eth`).
2. **Text Record Extraction**: Fetches specific text records (`axl-peer-id`, `capabilities`, `reputation`).
3. **Routing**: Uses the `axl-peer-id` to send an end-to-end encrypted message via the Gensyn AXL mesh.

## 2. Mathematical Mechanics

### ENS Namehash Computation
To query ENS text records via Web3, the human-readable string must be converted into a cryptographic hash (EIP-137).
```python
# Instead of relying on deprecated libraries, we compute the namehash natively:
from ens.utils import raw_name_to_hash
node_hash = raw_name_to_hash("strategy.agentns.eth")
```
This node hash is then passed to the ENS Public Resolver contract on Sepolia to read or write text records.

### Reputation Scoring & Nonce Management
Our agents update each other's reputations dynamically after successful transactions.

**The Math:**
```python
new_rep = round(min(current_reputation + 0.1, 5.0), 1)
```
The reputation is capped at a maximum score of `5.0`.

**The Nonce Collision Problem & Solution:**
When multiple agents attempt to write reputation scores to the same ENS parent domain within the same block, they risk encountering the `replacement transaction underpriced` error. This occurs when two transactions attempt to use the same `nonce`.

We solved this by fetching the `pending` transaction count, ensuring that consecutive rapid transactions are queued sequentially rather than colliding:
```python
# Fetching the pending nonce prevents collisions in rapid-fire agent updates
nonce = w3.eth.get_transaction_count(account.address, 'pending')
```

## 3. Setup Instructions (Sepolia)

To configure your own agents to use ENS discovery:

### Prerequisites
1. Get Sepolia ETH from [Alchemy Faucet](https://sepoliafaucet.com) or [Chainlink Faucet](https://faucets.chain.link/sepolia).
2. Register a base domain (e.g., `agentns.eth`) at [sepolia.app.ens.domains](https://sepolia.app.ens.domains).

### Configuration
1. Open `.env` and configure your keys:
```bash
PRIVATE_KEY=0xYOUR_WALLET_PRIVATE_KEY
WALLET_ADDRESS=0xYOUR_WALLET_ADDRESS
RPC_URL=https://ethereum-sepolia-rpc.publicnode.com
ENS_PARENT=yourdomain.eth
```

### Deploying Subnames
We use `viem` to programmatically deploy subnames and populate their text records. Run:
```bash
npm install
node setup/2_register_ens.js
```

This script will submit transactions to create:
- `scout.yourdomain.eth`
- `strategy.yourdomain.eth`
- `executor.yourdomain.eth`

And set the necessary `axl-peer-id` records for the AXL mesh network to function.
