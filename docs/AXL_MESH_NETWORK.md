# Gensyn AXL Mesh Network Mechanics

AGENTNS operates without a centralized server for agent-to-agent communication. Instead, it relies on **Gensyn AXL**, a peer-to-peer (P2P) networking layer that provides direct, encrypted communication between distributed agents.

## 1. P2P Topology & Identity

Each AXL node generates a unique identity using the **Ed25519** cryptographic signature scheme. 

**Mathematical Mechanics:**
- A Private Key is generated locally for each node.
- The corresponding Public Key (64-character hex string) acts as the **Peer ID** (e.g., `f04a3b306381fbc7adb6f92b4e84f1c...`).
- This Peer ID is mathematically bound to the node and is what we store inside the **ENS Text Records** for discovery.

## 2. macOS Port Collision Avoidance

By default, Gensyn AXL attempts to bind to Port `7000`. However, macOS uses Port `7000` for the `AirPlay Receiver (ControlCenter)`.

To resolve this and ensure clean local demoing, our AXL nodes are configured (`setup/1_run_axl_nodes.sh`) to map out separate local TCP ports:

| Agent | HTTP API Port | P2P Listener Port |
|---|---|---|
| Scout | `9002` | `7700` |
| Strategy | `9012` | `7701` |
| Executor | `9022` | `7702` |

## 3. TCP Protocol Mapping

Local AXL nodes default to expecting TLS (`tls://`) for their listeners. Because generating valid SSL/TLS certificates for `localhost` creates friction during development and hackathons, we configure the nodes to communicate over bare TCP.

**Configuration Override (`node-config.json`):**
```json
{
  "Listen": ["/ip4/127.0.0.1/tcp/7700"],
  "Peers": [
     "tcp://127.0.0.1:7700",
     "tcp://127.0.0.1:7701",
     "tcp://127.0.0.1:7702"
  ]
}
```
This guarantees nodes correctly discover peers in the local environment without TLS handshake failures.

## 4. Message Routing & JSON Envelopes

The official AXL HTTP Interface accepts and returns **raw bytes**. 

To provide structured communication between the Python agents, the `axl_client.py` wrapper serializes structured dictionaries into JSON byte arrays.

**The Routing Flow:**
1. **Scout** resolves the Strategy's `axl-peer-id` from ENS.
2. Scout packages the payload: `{"type": "opportunity", "data": {...}}`.
3. Scout triggers `POST /send` to its local AXL node on port `9002`, providing the destination Peer ID via the `X-Destination-Peer-Id` HTTP header.
4. The AXL mesh routes the bytes directly to the Strategy node via Port `7701`.
5. **Strategy** polls `GET /recv` on port `9012`, decodes the bytes from JSON, and verifies the sender using the `X-From-Peer-Id` header.
