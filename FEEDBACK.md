# KeeperHub Builder Feedback — AGENTNS Hackathon

> Required for the KeeperHub $250 feedback bounty.
> Fill in during integration — honest and specific.

## What Worked Well

- MCP server endpoint (`https://app.keeperhub.com/mcp`) connected cleanly
  via the `anthropic-beta: mcp-client-1` header pattern
- `ai_generate_workflow` tool reduced boilerplate significantly — 
  one natural language call vs. manually constructing nodes/edges
- `execute_workflow` + `get_execution_status` polling loop was intuitive
- The `web3/write-contract` action schema was well documented

## UX / DX Friction

<!-- Fill during integration — example below -->
- [ ] OAuth flow in headless environments required workaround (had to use API key header instead)
- [ ] `list_action_schemas` response could include example configs inline to save a round-trip
- [ ] `get_execution_logs` format for failed txs was inconsistent between retried and non-retried jobs

## Documentation Gaps

- [ ] `anthropic-beta: mcp-client-1` header requirement not mentioned in MCP docs
- [ ] No example showing `ai_generate_workflow` → `execute_workflow` full round-trip
- [ ] Sepolia testnet support not clearly called out in Web3 actions docs
  (is `"11155111"` accepted as network string?)

## Reproducible Bugs

<!-- Add during integration with exact steps to reproduce -->
- [ ] Bug 1: [step 1] → [step 2] → [unexpected result]

## Feature Requests

- Streaming execution logs (SSE or websocket) instead of polling `get_execution_status`
- `ai_generate_workflow` option to constrain to specific action types 
  (e.g. `allowed_actions: ["web3/write-contract"]`)
- Direct x402 micropayment integration: agent pays KeeperHub per execution
  without needing pre-funded org account
- Webhook trigger that agents can POST to directly (without a workflow ID)

## Summary

Overall integration experience: **Good**. The MCP abstraction is genuinely
useful for agentic workflows — a Python executor agent calling Claude which 
uses KeeperHub MCP tools creates a clean separation of concerns.

The main friction point was bootstrapping (auth + first workflow creation).
Once past that, the execution loop was reliable and the audit trail was excellent.
