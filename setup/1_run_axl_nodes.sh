#!/bin/bash
# setup/1_run_axl_nodes.sh
# Starts 3 AXL nodes locally — one per agent.
# Each node gets its own keypair, config, and port.
#
# Ports:
#   Scout    → api:9002 tcp:7000
#   Strategy → api:9012 tcp:7001
#   Executor → api:9022 tcp:7002
#
# Run from agentns/ root: bash setup/1_run_axl_nodes.sh

set -e

AXL_DIR="${AXL_DIR:-../axl}"
KEYS_DIR="./keys"
LOGS_DIR="./logs"

# ─── Colors ──────────────────────────────────────────────────────
CYAN='\033[96m'
GREEN='\033[92m'
YELLOW='\033[93m'
RESET='\033[0m'
BOLD='\033[1m'

echo ""
echo -e "${BOLD}${CYAN}─────────────────────────────────────${RESET}"
echo -e "${BOLD}${CYAN}  AGENTNS — AXL Node Launcher${RESET}"
echo -e "${BOLD}${CYAN}─────────────────────────────────────${RESET}"
echo ""

# ─── Check AXL binary ────────────────────────────────────────────
if [ ! -f "$AXL_DIR/node" ]; then
  echo -e "${YELLOW}Building AXL binary...${RESET}"
  cd "$AXL_DIR"
  go build -o node ./cmd/node/
  cd -
  echo -e "${GREEN}✓ AXL binary built${RESET}"
fi

mkdir -p "$KEYS_DIR" "$LOGS_DIR"

# ─── Generate keys if needed ─────────────────────────────────────
generate_key() {
  local name=$1
  local keyfile="$KEYS_DIR/${name}-private.pem"
  if [ ! -f "$keyfile" ]; then
    echo -e "${YELLOW}Generating key for ${name}...${RESET}"
    # Try Homebrew openssl first (macOS), then system openssl
    if command -v /opt/homebrew/opt/openssl/bin/openssl &>/dev/null; then
      /opt/homebrew/opt/openssl/bin/openssl genpkey -algorithm ed25519 -out "$keyfile" 2>/dev/null
    else
      openssl genpkey -algorithm ed25519 -out "$keyfile" 2>/dev/null
    fi
    echo -e "${GREEN}✓ Key saved: ${keyfile}${RESET}"
  else
    echo -e "${GREEN}✓ Key exists: ${keyfile}${RESET}"
  fi
}

generate_key "scout"
generate_key "strategy"
generate_key "executor"

# ─── Create configs ──────────────────────────────────────────────
create_config() {
  local name=$1
  local api_port=$2
  local tcp_port=$3
  local peers=$4
  local config_file="$KEYS_DIR/${name}-config.json"

  cat > "$config_file" <<EOF
{
  "PrivateKeyPath": "../../agentns/${KEYS_DIR}/${name}-private.pem",
  "api_port": ${api_port},
  "tcp_port": ${tcp_port},
  "Peers": [${peers}]
}
EOF
  echo -e "${GREEN}✓ Config: ${config_file}${RESET}"
}

# Nodes connect to each other
create_config "scout"    9002 7000 ""
create_config "strategy" 9012 7001 '"tls://127.0.0.1:7000"'
create_config "executor" 9022 7002 '"tls://127.0.0.1:7000"'

# ─── Kill existing nodes ──────────────────────────────────────────
echo ""
echo -e "${YELLOW}Stopping any existing AXL nodes...${RESET}"
pkill -f "node.*agentns" 2>/dev/null || true
sleep 1

# ─── Start nodes ─────────────────────────────────────────────────
start_node() {
  local name=$1
  local config="$KEYS_DIR/${name}-config.json"
  local log_file="$LOGS_DIR/${name}.log"

  "$AXL_DIR/node" -config "$config" > "$log_file" 2>&1 &
  local pid=$!
  echo $pid > "$LOGS_DIR/${name}.pid"
  echo -e "${GREEN}✓ ${name} node started (PID: ${pid}, log: ${log_file})${RESET}"
}

echo ""
echo -e "${BOLD}Starting AXL nodes...${RESET}"
start_node "scout"
sleep 1
start_node "strategy"
sleep 1
start_node "executor"
sleep 2

# ─── Verify ──────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}Verifying nodes...${RESET}"
verify_node() {
  local name=$1
  local port=$2
  local key
  key=$(curl -s "http://127.0.0.1:${port}/topology" | python3 -c "import sys,json; print(json.load(sys.stdin)['our_public_key'])" 2>/dev/null)
  if [ -n "$key" ]; then
    echo -e "${GREEN}✓ ${name}: ${key:0:16}...${RESET}"
  else
    echo -e "${YELLOW}⚠ ${name}: node not ready yet (check logs/${name}.log)${RESET}"
  fi
}

verify_node "scout"    9002
verify_node "strategy" 9012
verify_node "executor" 9022

echo ""
echo -e "${BOLD}${GREEN}─────────────────────────────────────${RESET}"
echo -e "${BOLD}${GREEN}  All nodes running ✓${RESET}"
echo -e "${BOLD}${GREEN}─────────────────────────────────────${RESET}"
echo ""
echo -e "Next: ${CYAN}bash setup/3_export_keys.sh${RESET}"
echo ""
