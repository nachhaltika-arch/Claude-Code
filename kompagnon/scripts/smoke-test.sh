#!/usr/bin/env bash
#
# KOMPAGNON Backend Smoke-Test
#
# Prueft den kompletten Authentifizierungs-Flow gegen die Render-Deployment:
#   1. Health-Check
#   2. Login (inkl. 2FA falls noetig)
#   3. Authentifizierter Request (/api/auth/me)
#   4. Ziel-Endpoint (/api/pages/1/editor) — konfigurierbar via TARGET_PATH
#   5. Logout
#   6. Revokations-Verifikation (alter Cookie muss jetzt 401 liefern)
#
# Usage:
#   ./smoke-test.sh
#   KOMPAGNON_EMAIL=admin@kompagnon.de KOMPAGNON_PASSWORD=... ./smoke-test.sh
#   API_BASE_URL=http://localhost:8000 ./smoke-test.sh
#   TARGET_PATH=/api/leads/ ./smoke-test.sh
#
# Abhaengigkeiten: curl, bash, optional jq (fuer schoenere JSON-Ausgabe)

set -u

# ── Konfiguration ─────────────────────────────────────────────────
API_BASE_URL="${API_BASE_URL:-https://claude-code-znq2.onrender.com}"
TARGET_PATH="${TARGET_PATH:-/api/pages/1/editor}"

COOKIE_JAR="$(mktemp /tmp/kompagnon-cookies.XXXXXX)"
COOKIE_JAR_PRESERVED="${COOKIE_JAR}.preserved"
trap 'rm -f "$COOKIE_JAR" "$COOKIE_JAR_PRESERVED"' EXIT

# ── Ausgabe-Helper ────────────────────────────────────────────────
if [ -t 1 ]; then
  G="\033[32m"; R="\033[31m"; Y="\033[33m"; B="\033[36m"; DIM="\033[2m"; N="\033[0m"
else
  G=""; R=""; Y=""; B=""; DIM=""; N=""
fi

ok()    { printf "${G}✓${N} %s\n" "$*"; }
fail()  { printf "${R}✗${N} %s\n" "$*"; }
info()  { printf "${B}→${N} %s\n" "$*"; }
note()  { printf "${Y}!${N} %s\n" "$*"; }
dim()   { printf "${DIM}  %s${N}\n" "$*"; }

json_field() {
  local field="$1"
  if command -v jq >/dev/null 2>&1; then
    jq -r ".${field} // empty" 2>/dev/null
  else
    grep -oE "\"${field}\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" \
      | head -1 | sed 's/^[^:]*:[[:space:]]*"//; s/"$//'
  fi
}

json_bool() {
  local field="$1"
  if command -v jq >/dev/null 2>&1; then
    jq -r ".${field} // false" 2>/dev/null
  else
    grep -oE "\"${field}\"[[:space:]]*:[[:space:]]*(true|false)" \
      | head -1 | grep -oE '(true|false)'
  fi
}

# ── Start ─────────────────────────────────────────────────────────
printf "${B}KOMPAGNON Smoke-Test${N}\n"
dim  "Server:       $API_BASE_URL"
dim  "Target-Path:  $TARGET_PATH"
dim  "Cookie-Jar:   $COOKIE_JAR"
echo

# ── Credentials abfragen ──────────────────────────────────────────
EMAIL="${KOMPAGNON_EMAIL:-}"
if [ -z "$EMAIL" ]; then
  printf "E-Mail: "
  read -r EMAIL
fi

PASSWORD="${KOMPAGNON_PASSWORD:-}"
if [ -z "$PASSWORD" ]; then
  printf "Passwort: "
  read -rs PASSWORD
  echo
fi
echo

# ── 1. Health-Check ───────────────────────────────────────────────
info "1/6  Health-Check"
HEALTH_CODE=$(curl -sS -m 10 -o /dev/null -w "%{http_code}" "$API_BASE_URL/health" 2>&1 || echo "000")
case "$HEALTH_CODE" in
  200) ok "Server antwortet ($HEALTH_CODE)" ;;
  404) ok "Server antwortet (404 — /health Route nicht vorhanden, aber Server erreichbar)" ;;
  000) fail "Server nicht erreichbar (Timeout oder DNS)" ; exit 1 ;;
  5*)  fail "Server-Fehler HTTP $HEALTH_CODE" ; exit 1 ;;
  *)   note "Ungewoehnlicher Status $HEALTH_CODE — weitermachen" ;;
esac
echo

# ── 2. Login ──────────────────────────────────────────────────────
info "2/6  Login"
LOGIN_RESP=$(curl -sS -c "$COOKIE_JAR" -X POST "$API_BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")
LOGIN_CODE=$?

if [ "$LOGIN_CODE" -ne 0 ]; then
  fail "Login-Request fehlgeschlagen (curl exit=$LOGIN_CODE)"
  exit 1
fi

# Fehler-Pfad erkennen
if echo "$LOGIN_RESP" | grep -q '"detail"' && ! echo "$LOGIN_RESP" | grep -q '"access_token"'; then
  if ! echo "$LOGIN_RESP" | grep -q '"require_2fa"'; then
    fail "Login abgelehnt"
    dim "Response: $LOGIN_RESP"
    exit 1
  fi
fi

# 2FA-Branch
REQUIRE_2FA=$(echo "$LOGIN_RESP" | json_bool require_2fa)
if [ "$REQUIRE_2FA" = "true" ]; then
  TEMP_TOKEN=$(echo "$LOGIN_RESP" | json_field temp_token)
  note "2FA erforderlich"
  printf "    6-stelliger TOTP-Code: "
  read -r TOTP

  LOGIN_RESP=$(curl -sS -c "$COOKIE_JAR" -X POST "$API_BASE_URL/api/auth/login/2fa" \
    -H "Content-Type: application/json" \
    -d "{\"temp_token\":\"$TEMP_TOKEN\",\"totp_code\":\"$TOTP\"}")

  if ! echo "$LOGIN_RESP" | grep -q '"access_token"'; then
    fail "2FA abgelehnt"
    dim "Response: $LOGIN_RESP"
    exit 1
  fi
  ok "2FA-Verifikation erfolgreich"
fi

# Cookie-Jar pruefen
if [ ! -s "$COOKIE_JAR" ] || ! grep -q "access_token" "$COOKIE_JAR" 2>/dev/null; then
  fail "Kein access_token Cookie gesetzt"
  dim "Response: $LOGIN_RESP"
  exit 1
fi
ok "access_token Cookie gesetzt"

# HttpOnly-Flag verifizieren (Netscape-Format: #HttpOnly_-Prefix)
if grep -qE "^#HttpOnly.*access_token" "$COOKIE_JAR" 2>/dev/null; then
  ok "HttpOnly-Flag gesetzt"
else
  note "HttpOnly-Flag nicht erkannt (evtl. anderes Cookie-Jar-Format)"
fi
echo

# ── 3. /api/auth/me ───────────────────────────────────────────────
info "3/6  Authentifizierter Request → /api/auth/me"
ME_RESP=$(curl -sS -b "$COOKIE_JAR" -w $'\n%{http_code}' "$API_BASE_URL/api/auth/me")
ME_CODE=$(printf '%s\n' "$ME_RESP" | tail -1)
ME_BODY=$(printf '%s\n' "$ME_RESP" | sed '$d')

if [ "$ME_CODE" = "200" ]; then
  ok "Authentifiziert (HTTP 200)"
  USER_EMAIL=$(echo "$ME_BODY" | json_field email)
  USER_ROLE=$(echo "$ME_BODY" | json_field role)
  [ -n "$USER_EMAIL" ] && dim "User: $USER_EMAIL (role=$USER_ROLE)"
else
  fail "/api/auth/me liefert HTTP $ME_CODE"
  dim "Body: $ME_BODY"
  exit 1
fi
echo

# ── 4. Ziel-Endpoint ──────────────────────────────────────────────
info "4/6  Ziel-Endpoint → $TARGET_PATH"
TARGET_RESP=$(curl -sS -b "$COOKIE_JAR" -w $'\n%{http_code}' "$API_BASE_URL$TARGET_PATH")
TARGET_CODE=$(printf '%s\n' "$TARGET_RESP" | tail -1)
TARGET_BODY=$(printf '%s\n' "$TARGET_RESP" | sed '$d')

case "$TARGET_CODE" in
  200)       ok "HTTP 200 — Endpoint liefert Daten" ;;
  204)       ok "HTTP 204 — No Content" ;;
  404)       note "HTTP 404 — Ressource nicht gefunden (Auth ist okay, Zielobjekt existiert nicht)" ;;
  401)       fail "HTTP 401 — Cookie wurde nicht akzeptiert" ; exit 1 ;;
  403)       fail "HTTP 403 — Keine Berechtigung fuer $TARGET_PATH" ; exit 1 ;;
  429)       note "HTTP 429 — Rate-Limit aktiv" ;;
  5*)        fail "HTTP $TARGET_CODE — Server-Fehler" ; dim "$TARGET_BODY" ; exit 1 ;;
  *)         note "HTTP $TARGET_CODE (unerwartet)" ;;
esac
echo

# ── 5. Logout ─────────────────────────────────────────────────────
info "5/6  Logout"
# Cookie-Jar VOR Logout preservieren, damit wir den alten Token
# in Schritt 6 erneut einreichen koennen (Blacklist-Verifikation)
cp "$COOKIE_JAR" "$COOKIE_JAR_PRESERVED"

LOGOUT_RESP=$(curl -sS -b "$COOKIE_JAR" -c "$COOKIE_JAR" -w $'\n%{http_code}' \
  -X POST "$API_BASE_URL/api/auth/logout")
LOGOUT_CODE=$(printf '%s\n' "$LOGOUT_RESP" | tail -1)

if [ "$LOGOUT_CODE" = "200" ]; then
  ok "Logout erfolgreich"
else
  fail "Logout HTTP $LOGOUT_CODE"
fi
echo

# ── 6. Revokations-Verifikation ───────────────────────────────────
info "6/6  Revokation pruefen (alter Cookie gegen Blacklist)"
# Wichtig: preservierten Jar nutzen, nicht den jetzt-geloeschten.
REVOKE_RESP=$(curl -sS -b "$COOKIE_JAR_PRESERVED" -w $'\n%{http_code}' "$API_BASE_URL/api/auth/me")
REVOKE_CODE=$(printf '%s\n' "$REVOKE_RESP" | tail -1)

if [ "$REVOKE_CODE" = "401" ]; then
  ok "Alter Cookie wird abgelehnt (HTTP 401) — Blacklist funktioniert"
else
  fail "Erwartete HTTP 401, bekam $REVOKE_CODE"
  note "Moegliche Ursachen: Token-Revokation broken ODER Deploy noch nicht live"
  dim "Body: $(printf '%s\n' "$REVOKE_RESP" | sed '$d')"
fi
echo

printf "${G}${N} Smoke-Test abgeschlossen\n"
