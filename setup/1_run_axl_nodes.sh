#!/bin/bash
# setup/1_run_axl_nodes.sh
# Builds AXL binary and starts 3 nodes (scout/strategy/executor).
# Run from the agentns/ project root: bash setup/1_run_axl_nodes.sh
set -e
C='\033[96m'; G='\033[92m'; Y='\033[93m'; R='\033[91m'; B='\033[1m'; N='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AXL_DIR="${AXL_DIR:-$PROJECT_ROOT/../axl}"
KEYS_DIR="$PROJECT_ROOT/keys"
LOGS_DIR="$PROJECT_ROOT/logs"
mkdir -p "$KEYS_DIR" "$LOGS_DIR"

echo -e "\n${B}${C}══════════════════════════════════════${N}"
echo -e "${B}${C}  AGENTNS — AXL Node Launcher${N}"
echo -e "${B}${C}══════════════════════════════════════${N}\n"

# ── Build AXL binary ─────────────────────────────────────────────
if [ ! -f "$AXL_DIR/node" ]; then
  echo -e "${Y}Building AXL binary from $AXL_DIR …${N}"
  if [ ! -d "$AXL_DIR" ]; then
    echo -e "${R}AXL repo not found at $AXL_DIR${N}"
    echo -e "Run: git clone https://github.com/gensyn-ai/axl.git $AXL_DIR"
    exit 1
  fi
  cd "$AXL_DIR"
  # Go 1.26 compatibility (from official docs)
  if go version | grep -q "go1.26"; then
    GOTOOLCHAIN=go1.25.5 go build -o node ./cmd/node/
  else
    go build -o node ./cmd/node/
  fi
  cd "$PROJECT_ROOT"
  echo -e "${G}✓ AXL binary built${N}"
else
  echo -e "${G}✓ AXL binary exists${N}"
fi

# ── Generate keypairs ────────────────────────────────────────────
gen_key() {
  local name="$1"
  local file="$KEYS_DIR/${name}.pem"
  [ -f "$file" ] && echo -e "${G}✓ Key exists: ${name}${N}" && return
  # macOS: use brew openssl; Linux: use system openssl
  if /opt/homebrew/opt/openssl/bin/openssl version &>/dev/null 2>&1; then
    /opt/homebrew/opt/openssl/bin/openssl genpkey -algorithm ed25519 -out "$file" 2>/dev/null
  else
    openssl genpkey -algorithm ed25519 -out "$file"
  fi
  echo -e "${G}✓ Key generated: ${name}${N}"
}
gen_key scout
gen_key strategy
gen_key executor

# ── Write node configs ────────────────────────────────────────────
write_config() {
  local name="$1" api_port="$2" tcp_port="$3" peer="$4"
  local peers_json=""
  [ -n "$peer" ] && peers_json="\"tcp://127.0.0.1:${peer}\""
  cat > "$KEYS_DIR/${name}.json" <<EOF
{
  "PrivateKeyPath": "$KEYS_DIR/${name}.pem",
  "api_port": ${api_port},
  "Listen": ["tcp://127.0.0.1:${tcp_port}"],
  "Peers": [${peers_json}]
}
EOF
  echo -e "${G}✓ Config: ${name} api=:${api_port} tcp=:${tcp_port}${N}"
}
# Scout is the bootstrap peer; strategy+executor connect to it
write_config scout    9002 7700 ""
write_config strategy 9012 7701 7700
write_config executor 9022 7702 7700

# ── Kill any running nodes ────────────────────────────────────────
echo -e "\n${Y}Stopping old nodes…${N}"
for f in "$LOGS_DIR"/*.pid; do
  [ -f "$f" ] && kill "$(cat "$f")" 2>/dev/null || true
done
sleep 1

# ── Start nodes ───────────────────────────────────────────────────
start_node() {
  local name="$1"
  "$AXL_DIR/node" -config "$KEYS_DIR/${name}.json" > "$LOGS_DIR/${name}.log" 2>&1 &
  echo $! > "$LOGS_DIR/${name}.pid"
  echo -e "${G}✓ ${name} started (PID=$!, log=logs/${name}.log)${N}"
}
echo -e "\n${B}Starting nodes…${N}"
start_node scout
sleep 1
start_node strategy
sleep 1
start_node executor
sleep 3

# ── Verify ────────────────────────────────────────────────────────
echo -e "\n${B}Verifying…${N}"
verify() {
  local name="$1" port="$2"
  local key
  key=$(curl -s "http://127.0.0.1:${port}/topology" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['our_public_key'])" 2>/dev/null) || true
  if [ -n "$key" ]; then
    echo -e "${G}✓ ${name}: ${key:0:16}…${N}"
  else
    echo -e "${Y}⚠ ${name}: not ready yet — check logs/${name}.log${N}"
  fi
}
verify scout    9002
verify strategy 9012
verify executor 9022

echo -e "\n${B}${G}══════════════════════════════════════${N}"
echo -e "${B}${G}  All nodes started ✓${N}"
echo -e "${B}${G}══════════════════════════════════════${N}"
echo -e "\nNext: ${C}bash setup/3_export_keys.sh${N}\n"
