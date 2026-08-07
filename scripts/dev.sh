#!/usr/bin/env bash
#
# KOMPAGNON — lokale Entwicklungsumgebung
#
#   bash scripts/dev.sh              Backend + Frontend starten
#   bash scripts/dev.sh --seed       zusätzlich Checklisten + Component-Library seeden
#   bash scripts/dev.sh --reset-db   lokale Datenbank verwerfen und neu anlegen
#   bash scripts/dev.sh --backend    nur Backend
#   bash scripts/dev.sh --frontend   nur Frontend
#   bash scripts/dev.sh --remote-db  Sperre gegen entfernte Datenbank aufheben
#
# Alles läuft gegen eine LOKALE Postgres. Zeigt die vorhandene .env auf eine
# entfernte Datenbank, bricht das Skript ab (Ausnahme: --remote-db).

set -euo pipefail

# ── Konstanten ───────────────────────────────────────────────────────────────
readonly REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly BACKEND_DIR="$REPO_ROOT/kompagnon/backend"
readonly FRONTEND_DIR="$REPO_ROOT/kompagnon/frontend"
readonly DB_NAME="kompagnon_local"
readonly BACKEND_PORT=8000
readonly FRONTEND_PORT=3000
readonly REQUIRED_PYTHON="python3.11"
readonly EXPECTED_NODE_MAJOR=18

RUN_BACKEND=true
RUN_FRONTEND=true
DO_SEED=false
DO_RESET_DB=false

# ── Ausgabe ──────────────────────────────────────────────────────────────────
info()  { printf '\033[0;36m▸\033[0m %s\n' "$1"; }
ok()    { printf '\033[0;32m✓\033[0m %s\n' "$1"; }
warn()  { printf '\033[0;33m!\033[0m %s\n' "$1"; }
fail()  { printf '\033[0;31m✗\033[0m %s\n' "$1" >&2; exit 1; }

# ── Argumente ────────────────────────────────────────────────────────────────
for arg in "$@"; do
  case "$arg" in
    --seed)     DO_SEED=true ;;
    --reset-db) DO_RESET_DB=true ;;
    --backend)  RUN_FRONTEND=false ;;
    --frontend) RUN_BACKEND=false ;;
    --remote-db) ALLOW_REMOTE_DB=true ;;
    -h|--help)  sed -n '3,13p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *)          fail "Unbekannte Option: $arg (siehe --help)" ;;
  esac
done

# ── Voraussetzungen ──────────────────────────────────────────────────────────
check_prerequisites() {
  info "Voraussetzungen prüfen"

  command -v "$REQUIRED_PYTHON" >/dev/null 2>&1 \
    || fail "$REQUIRED_PYTHON fehlt. Installieren mit: brew install python@3.11"

  command -v node >/dev/null 2>&1 \
    || fail "Node fehlt. Installieren mit: brew install node"

  local node_major
  node_major="$(node --version | sed 's/^v//' | cut -d. -f1)"
  if [ "$node_major" != "$EXPECTED_NODE_MAJOR" ]; then
    warn "Node $node_major lokal, aber $EXPECTED_NODE_MAJOR in CI und auf Render."
    warn "Build-Unterschiede sind möglich — im Zweifel gilt das Ergebnis der CI."
  fi

  command -v psql >/dev/null 2>&1 \
    || fail "Postgres fehlt. Installieren mit: brew install postgresql@16"

  pg_isready -q 2>/dev/null \
    || fail "Postgres läuft nicht. Starten mit: brew services start postgresql@16"

  ok "Python, Node und Postgres bereit"
}

# ── Datenbank ────────────────────────────────────────────────────────────────
setup_database() {
  if [ "$DO_RESET_DB" = true ]; then
    warn "Lokale Datenbank '$DB_NAME' wird verworfen"
    dropdb --if-exists "$DB_NAME"
  fi

  if psql -lqt | cut -d\| -f1 | grep -qw "$DB_NAME"; then
    ok "Datenbank '$DB_NAME' vorhanden"
    return
  fi

  info "Datenbank '$DB_NAME' anlegen"
  createdb "$DB_NAME"
  ok "Datenbank '$DB_NAME' angelegt (Schema entsteht beim Backend-Start)"
}

# ── Backend-Umgebung ─────────────────────────────────────────────────────────
#
# Schutz: eine vorhandene .env kann noch auf Render zeigen (so war der bisherige
# Ablauf laut docs/local-dev-with-render-db.md). Dann liefen lokale Änderungen
# und Migrationen gegen eine echte Datenbank. Das wird hier hart unterbunden.
assert_local_database() {
  local env_file="$1"
  local db_url
  db_url="$(grep -E '^DATABASE_URL=' "$env_file" | head -1 | cut -d= -f2-)"

  if [ -z "$db_url" ]; then
    fail "In $env_file fehlt DATABASE_URL."
  fi

  case "$db_url" in
    *localhost*|*127.0.0.1*)
      return 0
      ;;
  esac

  if [ "${ALLOW_REMOTE_DB:-false}" = "true" ]; then
    warn "DATABASE_URL zeigt NICHT auf localhost — Start nur wegen --remote-db erlaubt."
    warn "Schemaänderungen und Migrationen wirken auf die entfernte Datenbank."
    return 0
  fi

  printf '\n'
  fail "$(cat <<EOF
DATABASE_URL in $env_file zeigt auf eine entfernte Datenbank.

Beim Start würden Migrationen gegen diese Datenbank laufen. Für lokale
Entwicklung bitte in $env_file eintragen:

  DATABASE_URL=postgresql://localhost:5432/$DB_NAME

Die bisherige Zeile vorher sichern, falls du sie noch brauchst.
Bewusst gegen die entfernte Datenbank arbeiten: bash scripts/dev.sh --remote-db
EOF
)"
}

setup_backend_env() {
  local env_file="$BACKEND_DIR/.env"

  if [ -f "$env_file" ]; then
    assert_local_database "$env_file"
    ok "Backend-.env vorhanden, zeigt auf die lokale Datenbank"
    return
  fi

  info "Backend-.env aus Vorlage erzeugen"
  local secret
  secret="$(openssl rand -hex 32)"

  sed \
    -e "s|^DATABASE_URL=.*|DATABASE_URL=postgresql://localhost:5432/$DB_NAME|" \
    -e "s|^SECRET_KEY=.*|SECRET_KEY=$secret|" \
    "$BACKEND_DIR/.env.example" > "$env_file"

  ok "Backend-.env erzeugt (Schlüssel für externe Dienste bei Bedarf nachtragen)"
}

setup_backend_deps() {
  if [ ! -d "$BACKEND_DIR/venv" ]; then
    info "Virtuelle Umgebung anlegen"
    "$REQUIRED_PYTHON" -m venv "$BACKEND_DIR/venv"
  fi

  info "Backend-Abhängigkeiten prüfen"
  "$BACKEND_DIR/venv/bin/pip" install --quiet --upgrade pip
  "$BACKEND_DIR/venv/bin/pip" install --quiet -r "$BACKEND_DIR/requirements.txt"
  ok "Backend-Abhängigkeiten aktuell"
}

# ── Frontend-Umgebung ────────────────────────────────────────────────────────
setup_frontend_env() {
  local env_file="$FRONTEND_DIR/.env.local"

  if [ ! -f "$env_file" ]; then
    info "Frontend-.env.local erzeugen"
    printf 'REACT_APP_API_URL=http://localhost:%s\n' "$BACKEND_PORT" > "$env_file"
  fi
  ok "Frontend zeigt auf http://localhost:$BACKEND_PORT"

  if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    info "Frontend-Abhängigkeiten installieren (dauert beim ersten Mal einige Minuten)"
    (cd "$FRONTEND_DIR" && npm ci --legacy-peer-deps)
  fi
  ok "Frontend-Abhängigkeiten vorhanden"
}

# ── Seeds ────────────────────────────────────────────────────────────────────
run_seeds() {
  info "Seed-Daten einspielen"
  (cd "$BACKEND_DIR" && ./venv/bin/python seed_checklists.py)
  (cd "$BACKEND_DIR" && ./venv/bin/python -m seeds.seed_component_library)
  ok "Checklisten und Component-Library eingespielt"
}

# ── Start ────────────────────────────────────────────────────────────────────
BACKEND_PID=""
FRONTEND_PID=""

shutdown() {
  printf '\n'
  info "Beenden"
  [ -n "$BACKEND_PID" ]  && kill "$BACKEND_PID"  2>/dev/null || true
  [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null || true
  wait 2>/dev/null || true
  ok "Gestoppt"
}
trap shutdown INT TERM

start_services() {
  if [ "$RUN_BACKEND" = true ]; then
    info "Backend startet auf http://localhost:$BACKEND_PORT (Doku: /docs)"
    (cd "$BACKEND_DIR" && ./venv/bin/uvicorn main:app --reload --port "$BACKEND_PORT") &
    BACKEND_PID=$!
  fi

  if [ "$RUN_FRONTEND" = true ]; then
    info "Frontend startet auf http://localhost:$FRONTEND_PORT"
    (cd "$FRONTEND_DIR" && npm start) &
    FRONTEND_PID=$!
  fi

  printf '\n'
  ok "Läuft. Beenden mit Strg+C."
  wait
}

# ── Ablauf ───────────────────────────────────────────────────────────────────
check_prerequisites

if [ "$RUN_BACKEND" = true ]; then
  setup_database
  setup_backend_env
  setup_backend_deps
  [ "$DO_SEED" = true ] && run_seeds
fi

[ "$RUN_FRONTEND" = true ] && setup_frontend_env

start_services
