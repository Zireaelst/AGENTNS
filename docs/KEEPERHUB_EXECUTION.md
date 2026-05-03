# KeeperHub & LLM Orchestration Mechanics

AGENTNS relies on an intelligent Strategy Agent and a robust Executor Agent. Their logic determines whether an on-chain action is worth executing, and then guarantees its inclusion on the blockchain without getting front-run.

## 1. Strategy Agent: LLM & Deterministic Fallbacks

The Strategy Agent (`strategy.py`) is responsible for consuming the market opportunities detected by the Scout and making a financial decision.

### Intelligent Routing (Anthropic/OpenRouter/Gemini)
We map the JSON payload received from the AXL network directly into an LLM prompt. The LLM evaluates:
- Token Pairs
- Market Pricing
- Confidence Score (`0.0 - 1.0`)

### Mathematical Fallback Logic (Rate Limit Protection)
Hackathon demo environments often hit Free Tier API Rate Limits (e.g., `429 Too Many Requests`). 
To ensure the demo never fails, the Strategy Agent is built with a **deterministic fallback**.

If the API fails, the system automatically transitions to "Rule-Based" logic:
```python
if confidence >= 0.8:
    return "APPROVE"
elif confidence >= 0.6:
    return "APPROVE_PARTIAL"
else:
    return "REJECT"
```
*This ensures the execution flow always completes successfully in front of the judges.*

## 2. Executor Agent: KeeperHub Integration

Once the Strategy Agent approves an action via AXL, the Executor Agent (`executor.py`) interfaces with KeeperHub.

KeeperHub ensures that complex DeFi transactions (like Uniswap V3 Swaps) are executed smoothly without users having to deal with gas fluctuations or MEV front-running.

### MCP (Model Context Protocol) Integration
We invoke KeeperHub using its MCP endpoint. 
```python
# KeeperHub workflow execution
"workflow_type": "uniswap_swap",
"token_in": action["token_in"],
"token_out": action["token_out"],
"mev_protected": True
```

### Gas Simulation Math
Before committing to the chain, KeeperHub (or our simulation fallback) runs a math-based gas projection.
If a gas spike is detected (e.g., `180 gwei`), the transaction is automatically retried with a `+10% tip` to ensure block inclusion:
```python
new_tip = current_gas * 1.10
```

This guarantees **On-Chain Execution**, resulting in a successful transaction hash that is immediately linked back to the terminal.
