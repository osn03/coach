#!/usr/bin/env bash
# One-command setup for the Adaptive Endurance Coach (macOS / Linux).
#
#   ./setup.sh
#
# What it does (safe to re-run; re-running also updates the installed skill):
#   1. Installs uv if missing (uv also fetches Python 3.12 automatically)
#   2. Installs the Intervals.icu MCP server's dependencies
#   3. Asks for your Intervals.icu API key + athlete ID, tests them, writes intervals-mcp-server/.env
#   4. Copies the coaching skill to ~/.claude/skills/
#   5. Registers the MCP server with Claude Code (if installed), else prints the Claude Desktop config
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_DIR="$ROOT/intervals-mcp-server"
SKILL_SRC="$ROOT/adaptive-endurance-coach/skills/adaptive-endurance-coach"
SKILLS_DIR="$HOME/.claude/skills"
ENV_FILE="$SERVER_DIR/.env"

step() { printf '\n\033[36m==> %s\033[0m\n' "$1"; }
ok()   { printf '    \033[32m%s\033[0m\n' "$1"; }
warn() { printf '    \033[33m%s\033[0m\n' "$1"; }

# --- 1. uv -------------------------------------------------------------------
step "Checking for uv"
if ! command -v uv >/dev/null 2>&1; then
  warn "uv not found - installing it"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
  command -v uv >/dev/null 2>&1 || { echo "uv installed but not on PATH. Open a new terminal and re-run."; exit 1; }
fi
UV="$(command -v uv)"
ok "uv: $UV"

# --- 2. server dependencies --------------------------------------------------
step "Installing MCP server dependencies (uv sync)"
(cd "$SERVER_DIR" && "$UV" sync --python 3.12)
ok "Dependencies installed"

# --- 3. credentials ----------------------------------------------------------
step "Intervals.icu credentials"
write_env=1
if [ -f "$ENV_FILE" ]; then
  read -r -p "    intervals-mcp-server/.env already exists. Keep it? [Y/n] " ans
  if [ -z "$ans" ] || [[ "$ans" =~ ^[Yy] ]]; then write_env=0; ok "Keeping existing .env"; fi
fi
if [ "$write_env" = 1 ]; then
  echo "    Find both at https://intervals.icu/settings -> Developer Settings."
  while :; do
    read -r -p "    Athlete ID (e.g. i123456): " ATHLETE_ID
    ATHLETE_ID="$(echo "$ATHLETE_ID" | tr -d '[:space:]')"
    [[ "$ATHLETE_ID" =~ ^[0-9]+$ ]] && ATHLETE_ID="i$ATHLETE_ID"
    [[ "$ATHLETE_ID" =~ ^i[0-9]+$ ]] && break
  done
  read -r -s -p "    API key (input hidden): " API_KEY; echo
  API_KEY="$(echo "$API_KEY" | tr -d '[:space:]')"

  code=$(curl -s -o /dev/null -w '%{http_code}' -u "API_KEY:$API_KEY" \
         "https://intervals.icu/api/v1/athlete/$ATHLETE_ID" || echo 000)
  if [ "$code" = 200 ]; then
    ok "Credentials verified with Intervals.icu"
  else
    warn "Could not verify credentials (HTTP $code)."
    read -r -p "    Save them anyway? [y/N] " ans
    [[ "$ans" =~ ^[Yy] ]] || { echo "Aborted. Check the API key and athlete ID and re-run."; exit 1; }
  fi
  umask 077
  printf '# Intervals.icu credentials - never commit this file (it is gitignored)\nAPI_KEY=%s\nATHLETE_ID=%s\n' \
    "$API_KEY" "$ATHLETE_ID" > "$ENV_FILE"
  ok "Wrote $ENV_FILE"
fi

# --- 4. skill ----------------------------------------------------------------
step "Installing the coaching skill"
mkdir -p "$SKILLS_DIR"
rm -rf "$SKILLS_DIR/adaptive-endurance-coach"
cp -R "$SKILL_SRC" "$SKILLS_DIR/adaptive-endurance-coach"
ok "Installed to $SKILLS_DIR/adaptive-endurance-coach (SKILL.md + references/)"

# --- 5. register MCP server --------------------------------------------------
step "Registering the Intervals.icu MCP server"
if command -v claude >/dev/null 2>&1; then
  claude mcp remove intervals --scope user >/dev/null 2>&1 || true
  if claude mcp add intervals --scope user -- "$UV" run --directory "$SERVER_DIR" python src/intervals_mcp_server/server.py; then
    ok "Registered 'intervals' with Claude Code (user scope)"
  else
    warn "claude mcp add failed - see the README for manual registration."
  fi
else
  warn "Claude Code CLI not found. For Claude Desktop, add this to claude_desktop_config.json under \"mcpServers\":"
  cat <<EOF
  "intervals": {
    "command": "$UV",
    "args": ["run", "--directory", "$SERVER_DIR", "python", "src/intervals_mcp_server/server.py"]
  }
EOF
fi

printf "\n\033[32mDone. Restart Claude, then say: 'I want to start training for <your goal>'.\033[0m\n"
