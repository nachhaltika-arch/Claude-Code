#!/usr/bin/env bash
# ============================================================================
# Claude Code Setup für KOMPAGNON — neuer Rechner (Mac/Linux)
# ============================================================================
# Verwendung:
#   bash scripts/setup-claude-code.sh
#
# Voraussetzungen:
#   - Node.js >= 18 (brew install node)
#   - jq (brew install jq)
#   - GitHub Personal Access Token (Classic, scope: repo, workflow)
#   - Render API Token (https://dashboard.render.com/u/settings#api-keys)
# ============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_DIR="$REPO_ROOT/.claude-config"
CLAUDE_HOME="$HOME/.claude"

color_info()  { printf "\033[1;34m[INFO]\033[0m %s\n" "$*"; }
color_ok()    { printf "\033[1;32m[OK]\033[0m %s\n" "$*"; }
color_warn()  { printf "\033[1;33m[WARN]\033[0m %s\n" "$*"; }
color_error() { printf "\033[1;31m[ERROR]\033[0m %s\n" "$*"; exit 1; }

# ----------------------------------------------------------------------------
# 1) Prerequisites
# ----------------------------------------------------------------------------
color_info "Prüfe Voraussetzungen..."

command -v node >/dev/null 2>&1 || color_error "node fehlt. Installiere via 'brew install node' (>= 18)."
command -v npm >/dev/null 2>&1  || color_error "npm fehlt."
command -v jq >/dev/null 2>&1   || color_error "jq fehlt. Installiere via 'brew install jq'."

NODE_MAJOR=$(node -v | sed -E 's/^v([0-9]+).*/\1/')
[ "$NODE_MAJOR" -ge 18 ] || color_error "Node $NODE_MAJOR ist zu alt, brauche >= 18."

color_ok "Node $(node -v), npm $(npm -v), jq vorhanden."

# ----------------------------------------------------------------------------
# 2) Claude Code CLI installieren
# ----------------------------------------------------------------------------
if command -v claude >/dev/null 2>&1; then
  color_ok "Claude Code CLI bereits installiert: $(claude --version 2>/dev/null || echo unknown)"
else
  color_info "Installiere Claude Code CLI global..."
  npm install -g @anthropic-ai/claude-code
  color_ok "Claude Code CLI installiert."
fi

# ----------------------------------------------------------------------------
# 3) Claude-Home aufsetzen
# ----------------------------------------------------------------------------
mkdir -p "$CLAUDE_HOME/agents" "$CLAUDE_HOME/rules/common" "$CLAUDE_HOME/rules/typescript"

color_info "Kopiere Custom-Agents..."
cp "$CONFIG_DIR/agents/"*.md "$CLAUDE_HOME/agents/"
color_ok "$(ls "$CLAUDE_HOME/agents/" | wc -l) Agents kopiert."

color_info "Kopiere Rules..."
cp "$CONFIG_DIR/rules/common/"*.md "$CLAUDE_HOME/rules/common/"
cp "$CONFIG_DIR/rules/typescript/"*.md "$CLAUDE_HOME/rules/typescript/"
color_ok "10 common + 5 typescript Rules kopiert."

# ----------------------------------------------------------------------------
# 4) Settings (idempotent — überschreibt nicht falls bereits manuell editiert)
# ----------------------------------------------------------------------------
if [ -f "$CLAUDE_HOME/settings.json" ]; then
  color_warn "$CLAUDE_HOME/settings.json existiert bereits, überspringe (manuell gemerged falls nötig)."
else
  cp "$CONFIG_DIR/settings.json.template" "$CLAUDE_HOME/settings.json"
  color_ok "settings.json erstellt."
fi

if [ -f "$CLAUDE_HOME/settings.local.json" ]; then
  color_warn "$CLAUDE_HOME/settings.local.json existiert bereits, überspringe."
else
  cp "$CONFIG_DIR/settings.local.json.template" "$CLAUDE_HOME/settings.local.json"
  color_ok "settings.local.json erstellt."
fi

# ----------------------------------------------------------------------------
# 5) Tokens für MCP-Server (interaktiv)
# ----------------------------------------------------------------------------
color_info "MCP-Tokens werden in ~/.claude.json gespeichert (NICHT im Repo)."

GH_TOKEN="${GITHUB_PERSONAL_ACCESS_TOKEN:-}"
RND_TOKEN="${RENDER_API_TOKEN:-}"

if [ -z "$GH_TOKEN" ]; then
  printf "GitHub Personal Access Token (ghp_...): "
  read -rs GH_TOKEN
  printf "\n"
fi

if [ -z "$RND_TOKEN" ]; then
  printf "Render API Token (rnd_...): "
  read -rs RND_TOKEN
  printf "\n"
fi

[ -z "$GH_TOKEN" ] && color_error "GITHUB_PERSONAL_ACCESS_TOKEN ist leer."
[ -z "$RND_TOKEN" ] && color_error "RENDER_API_TOKEN ist leer."

# ----------------------------------------------------------------------------
# 6) MCP-Server eintragen via claude mcp add
# ----------------------------------------------------------------------------
color_info "Registriere MCP-Server..."

# Render (HTTP-MCP)
claude mcp add render --transport http --header "Authorization=Bearer $RND_TOKEN" https://mcp.render.com/mcp || true

# GitHub (stdio-MCP)
claude mcp add github --env "GITHUB_PERSONAL_ACCESS_TOKEN=$GH_TOKEN" -- npx -y @modelcontextprotocol/server-github || true

color_ok "MCP-Server eingetragen (Render + GitHub)."

# ----------------------------------------------------------------------------
# 7) Plugins installieren
# ----------------------------------------------------------------------------
color_info "Installiere Plugins (claude-mem, context-mode, last30days-skill)..."

claude plugin marketplace add github:thedotmack/claude-mem || true
claude plugin install claude-mem@thedotmack || true

claude plugin marketplace add github:mksglu/context-mode || true
claude plugin install context-mode@context-mode || true

claude plugin marketplace add github:mvanhorn/last30days-skill || true
claude plugin install last30days@last30days-skill || true

color_ok "Plugins installiert."

# ----------------------------------------------------------------------------
# 8) Memory-Sync via Symlink (Repo ist Single Source of Truth)
# ----------------------------------------------------------------------------
color_info "Verlinke Memory-Verzeichnis (~/.claude/projects/.../memory/ → repo)..."

REPO_REAL_PATH="$(cd "$REPO_ROOT" && pwd)"
# Encoding: Mac-Pfad / → -, Spaces → -, Sonderzeichen → -
ENCODED_PATH="$(echo "$REPO_REAL_PATH" | sed 's|/|-|g; s| |-|g; s|[^A-Za-z0-9_-]|-|g')"
PROJECT_MEMORY_DIR="$CLAUDE_HOME/projects/$ENCODED_PATH"
mkdir -p "$PROJECT_MEMORY_DIR"

if [ -L "$PROJECT_MEMORY_DIR/memory" ]; then
  color_ok "memory/ ist bereits Symlink — überspringe."
elif [ -d "$PROJECT_MEMORY_DIR/memory" ]; then
  color_warn "memory/ existiert als regulärer Ordner. Backup nach memory.bak.$(date +%s) und ersetze durch Symlink."
  mv "$PROJECT_MEMORY_DIR/memory" "$PROJECT_MEMORY_DIR/memory.bak.$(date +%s)"
  ln -s "$REPO_REAL_PATH/.claude-config/memory" "$PROJECT_MEMORY_DIR/memory"
  color_ok "Symlink erstellt."
else
  ln -s "$REPO_REAL_PATH/.claude-config/memory" "$PROJECT_MEMORY_DIR/memory"
  color_ok "Memory-Symlink: $PROJECT_MEMORY_DIR/memory → $REPO_REAL_PATH/.claude-config/memory"
fi

color_info "Memory-Files sichtbar:"
ls "$PROJECT_MEMORY_DIR/memory/" 2>/dev/null | head -5

# ----------------------------------------------------------------------------
# 9) Authentifizierung (manuell)
# ----------------------------------------------------------------------------
color_warn "Letzter Schritt: 'claude auth' manuell ausführen für Anthropic-Login (OAuth-Browser-Flow)."
color_warn "Render-MCP, GitHub-MCP, Plugins und Memory-Sync sind eingerichtet."

# ----------------------------------------------------------------------------
# 10) Verify
# ----------------------------------------------------------------------------
color_info "Verifiziere..."
claude mcp list || true

color_ok "Setup abgeschlossen. Starte 'claude' im Repo-Root."
color_ok "Memory wird automatisch über Git synchronisiert — committe + pushe Änderungen in .claude-config/memory/ damit sie auf andere Rechner kommen."
