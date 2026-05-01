#!/bin/bash
# setup/3_export_keys.sh — Read AXL peer IDs and write to .env
# Run after 1_run_axl_nodes.sh from the project root.
G='\033[92m'; Y='\033[93m'; R='\033[91m'; B='\033[1m'; N='\033[0m'
cd "$(dirname "$0")/.."

get_id() {
  local port="$1"
  curl -s "http://127.0.0.1:${port}/topology" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['our_public_key'])" 2>/dev/null
}

echo -e "\n${B}Reading AXL peer IDs…${N}"
SCOUT_KEY=$(get_id 9002)
STRAT_KEY=$(get_id 9012)
EXEC_KEY=$(get_id  9022)

if [ -z "$SCOUT_KEY" ] || [ -z "$STRAT_KEY" ] || [ -z "$EXEC_KEY" ]; then
  echo -e "${R}ERROR: One or more nodes not running.${N}"
  echo -e "Run: bash setup/1_run_axl_nodes.sh"
  exit 1
fi

[ ! -f .env ] && cp .env.example .env

update_env() {
  local key="$1" val="$2"
  if grep -q "^${key}=" .env; then
    sed -i.bak "s|^${key}=.*|${key}=${val}|" .env && rm -f .env.bak
  else
    echo "${key}=${val}" >> .env
  fi
}

update_env SCOUT_PEER_ID    "$SCOUT_KEY"
update_env STRATEGY_PEER_ID "$STRAT_KEY"
update_env EXECUTOR_PEER_ID "$EXEC_KEY"

echo -e "${G}✓ SCOUT_PEER_ID    = ${SCOUT_KEY:0:20}…${N}"
echo -e "${G}✓ STRATEGY_PEER_ID = ${STRAT_KEY:0:20}…${N}"
echo -e "${G}✓ EXECUTOR_PEER_ID = ${EXEC_KEY:0:20}…${N}"
echo -e "\n${B}${G}Peer IDs saved to .env ✓${N}"
echo -e "\nNext steps:"
echo -e "  Mock mode: ${Y}bash demo.sh${N}"
echo -e "  Real mode: ${Y}node setup/2_register_ens.js && DEMO_MODE=real bash demo.sh${N}\n"
