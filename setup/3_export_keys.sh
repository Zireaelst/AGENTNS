#!/bin/bash
# setup/3_export_keys.sh
# Reads AXL peer IDs from running nodes and writes them to .env
# Run after 1_run_axl_nodes.sh

GREEN='\033[92m'
CYAN='\033[96m'
RESET='\033[0m'
BOLD='\033[1m'

echo ""
echo -e "${BOLD}${CYAN}Exporting AXL peer IDs to .env...${RESET}"
echo ""

get_peer_id() {
  local name=$1
  local port=$2
  curl -s "http://127.0.0.1:${port}/topology" | python3 -c "import sys,json; print(json.load(sys.stdin)['our_public_key'])" 2>/dev/null
}

SCOUT_KEY=$(get_peer_id "scout" 9002)
STRATEGY_KEY=$(get_peer_id "strategy" 9012)
EXECUTOR_KEY=$(get_peer_id "executor" 9022)

if [ -z "$SCOUT_KEY" ] || [ -z "$STRATEGY_KEY" ] || [ -z "$EXECUTOR_KEY" ]; then
  echo "ERROR: Could not read peer IDs. Are the AXL nodes running?"
  echo "Run: bash setup/1_run_axl_nodes.sh"
  exit 1
fi

# Update .env
sed -i.bak "s|^SCOUT_PEER_ID=.*|SCOUT_PEER_ID=${SCOUT_KEY}|" .env
sed -i.bak "s|^STRATEGY_PEER_ID=.*|STRATEGY_PEER_ID=${STRATEGY_KEY}|" .env
sed -i.bak "s|^EXECUTOR_PEER_ID=.*|EXECUTOR_PEER_ID=${EXECUTOR_KEY}|" .env

echo -e "${GREEN}✓ SCOUT_PEER_ID    = ${SCOUT_KEY:0:20}...${RESET}"
echo -e "${GREEN}✓ STRATEGY_PEER_ID = ${STRATEGY_KEY:0:20}...${RESET}"
echo -e "${GREEN}✓ EXECUTOR_PEER_ID = ${EXECUTOR_KEY:0:20}...${RESET}"
echo ""
echo -e "${BOLD}${GREEN}Peer IDs written to .env ✓${RESET}"
echo ""
echo "Next:"
echo "  DEMO_MODE=mock → bash demo.sh"
echo "  DEMO_MODE=real → node setup/2_register_ens.js && bash demo.sh"
