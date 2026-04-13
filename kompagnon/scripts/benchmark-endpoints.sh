#!/usr/bin/env bash
#
# KOMPAGNON Backend Endpoint-Benchmark
#
# Misst Antwortzeiten + Response-Groesse aller wichtigen GET-Endpoints.
# Loggt sich einmal ein (Cookie-Jar) und fuehrt dann eine kurze Liste von
# Requests durch — jeweils zwei Mal (erster Call = cold, zweiter = warm),
# sortiert nach der warmen Laufzeit.
#
# Usage:
#   ./benchmark-endpoints.sh                          # prompts for creds
#   KOMPAGNON_EMAIL=... KOMPAGNON_PASSWORD=... ./benchmark-endpoints.sh
#   API_BASE_URL=http://localhost:8000 ./benchmark-endpoints.sh
#
# Abhaengigkeiten: curl, bash
set -u

API_BASE_URL="${API_BASE_URL:-https://claude-code-znq2.onrender.com}"
COOKIE_JAR="$(mktemp /tmp/kompagnon-bench.XXXXXX)"
trap 'rm -f "$COOKIE_JAR"' EXIT

if [ -t 1 ]; then
  G="\033[32m"; R="\033[31m"; Y="\033[33m"; B="\033[36m"; DIM="\033[2m"; N="\033[0m"
else
  G=""; R=""; Y=""; B=""; DIM=""; N=""
fi

# Endpoints zum Messen. Sortiert nach Wichtigkeit fuer das Dashboard/UI.
# Format: "<GET|POST> <path> <kurz-name>"
ENDPOINTS=(
  "GET /api/health                       Health-Check"
  "GET /api/auth/me                      Auth-Me"
  "GET /api/dashboard/kpis                Dashboard-KPIs"
  "GET /api/dashboard/alerts              Dashboard-Alerts"
  "GET /api/dashboard/projects-by-phase   Dashboard-Projects-By-Phase"
  "GET /api/audit/recent                  Audit-Recent"
  "GET /api/leads/?limit=500              Leads-Liste"
  "GET /api/projects/?limit=200           Projects-Liste"
  "GET /api/usercards/                    Usercards-Liste"
  "GET /api/admin/users                   Admin-Users"
  "GET /api/deals/                        Deals-Liste"
  "GET /api/campaigns/stats               Campaign-Stats"
  "GET /api/products/                     Products-Liste"
  "GET /api/newsletter/                   Newsletter-Liste"
  "GET /api/messages/1                    Messages-Lead-1"
  "GET /api/briefings/1                   Briefing-Lead-1"
  "GET /api/leads/1/profile               Lead-1-Profile"
  "GET /api/leads/1/full                  Lead-1-Full"
  "GET /api/projects/1                    Project-1-Detail"
  "GET /api/projects/1/margin             Project-1-Margin"
  "GET /api/projects/1/screenshots        Project-1-Screenshots"
)

printf "${B}KOMPAGNON Endpoint-Benchmark${N}\n"
printf "${DIM}  Server: %s${N}\n\n" "$API_BASE_URL"

# ── Credentials ──
EMAIL="${KOMPAGNON_EMAIL:-}"
if [ -z "$EMAIL" ]; then
  printf "E-Mail: "; read -r EMAIL
fi
PASSWORD="${KOMPAGNON_PASSWORD:-}"
if [ -z "$PASSWORD" ]; then
  printf "Passwort: "; read -rs PASSWORD; echo
fi

# ── Login ──
printf "${B}→${N} Login... "
LOGIN_RESP=$(curl -sS -c "$COOKIE_JAR" -X POST "$API_BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")
if ! echo "$LOGIN_RESP" | grep -q '"access_token"'; then
  if echo "$LOGIN_RESP" | grep -q '"require_2fa"'; then
    printf "${Y}!${N} 2FA erforderlich\n"
    TEMP_TOKEN=$(echo "$LOGIN_RESP" | sed -n 's/.*"temp_token":"\([^"]*\)".*/\1/p')
    printf "TOTP-Code: "; read -r TOTP
    LOGIN_RESP=$(curl -sS -c "$COOKIE_JAR" -X POST "$API_BASE_URL/api/auth/login/2fa" \
      -H "Content-Type: application/json" \
      -d "{\"temp_token\":\"$TEMP_TOKEN\",\"totp_code\":\"$TOTP\"}")
    if ! echo "$LOGIN_RESP" | grep -q '"access_token"'; then
      printf "${R}✗${N} 2FA abgelehnt\n"
      exit 1
    fi
  else
    printf "${R}✗${N} Login abgelehnt\n"
    echo "Response: $LOGIN_RESP"
    exit 1
  fi
fi
printf "${G}✓${N} Cookie gesetzt\n\n"

# ── Warmup (1 Call auf Health um Render-Cold-Start zu vermeiden) ──
curl -sS -o /dev/null -b "$COOKIE_JAR" "$API_BASE_URL/api/health" > /dev/null 2>&1 || true

# ── Bench-Durchlauf ──
printf "${B}→${N} Messung laeuft (%d Endpoints × 2 Calls, cold + warm)...\n\n" "${#ENDPOINTS[@]}"

# Tab-getrennte Ergebnisse fuer spaeteres Sortieren
RESULTS_FILE="$(mktemp /tmp/kompagnon-bench-results.XXXXXX)"
trap 'rm -f "$COOKIE_JAR" "$RESULTS_FILE"' EXIT

for entry in "${ENDPOINTS[@]}"; do
  # Parse "METHOD PATH NAME"
  method=$(echo "$entry" | awk '{print $1}')
  path=$(echo "$entry"   | awk '{print $2}')
  name=$(echo "$entry"   | awk '{for(i=3;i<=NF;i++) printf "%s ", $i; print ""}' | sed 's/ *$//')

  # Cold call
  cold=$(curl -sS -o /dev/null -b "$COOKIE_JAR" \
    -w "%{http_code} %{time_total} %{size_download}" \
    -X "$method" "$API_BASE_URL$path" 2>/dev/null)
  cold_code=$(echo "$cold" | awk '{print $1}')
  cold_time=$(echo "$cold" | awk '{print $2}')
  cold_size=$(echo "$cold" | awk '{print $3}')

  # Warm call (gleiche URL, direkt danach)
  warm=$(curl -sS -o /dev/null -b "$COOKIE_JAR" \
    -w "%{http_code} %{time_total} %{size_download}" \
    -X "$method" "$API_BASE_URL$path" 2>/dev/null)
  warm_code=$(echo "$warm" | awk '{print $1}')
  warm_time=$(echo "$warm" | awk '{print $2}')
  warm_size=$(echo "$warm" | awk '{print $3}')

  # Sekunden → Millisekunden
  cold_ms=$(awk "BEGIN{printf \"%.0f\", $cold_time * 1000}")
  warm_ms=$(awk "BEGIN{printf \"%.0f\", $warm_time * 1000}")

  # In Datei fuer spaeteres Sortieren
  printf "%06d\t%s\t%s\t%s\t%s\t%s\t%s\n" \
    "$warm_ms" "$name" "$method" "$path" "$warm_code" "$cold_ms" "$warm_size" >> "$RESULTS_FILE"

  # Live-Ausgabe (farbig nach Schwellwerten)
  if [ "$warm_code" -ge 400 ] 2>/dev/null; then
    color="$R"
  elif [ "$warm_ms" -gt 1000 ] 2>/dev/null; then
    color="$R"
  elif [ "$warm_ms" -gt 300 ] 2>/dev/null; then
    color="$Y"
  else
    color="$G"
  fi
  printf "  %b%5d ms%b  %3s  %-32s  cold=%4d ms  size=%7s b\n" \
    "$color" "$warm_ms" "$N" "$warm_code" "$name" "$cold_ms" "$warm_size"
done

# ── Sortierung nach Dauer (langsamste zuerst) ──
echo
printf "${B}═══ Ergebnis sortiert nach warmer Laufzeit ═══${N}\n\n"
printf "  ${DIM}%5s  %4s  %-32s  %9s  %7s  %s${N}\n" "WARM" "HTTP" "NAME" "COLD" "SIZE" "PATH"
printf "  ${DIM}─────  ────  ────────────────────────────────  ─────────  ───────  ─────────────────${N}\n"
sort -rn "$RESULTS_FILE" | while IFS=$'\t' read -r warm name method path code cold size; do
  warm_int=$(echo "$warm" | sed 's/^0*//')
  [ -z "$warm_int" ] && warm_int=0
  if [ "$code" -ge 400 ] 2>/dev/null; then
    color="$R"
  elif [ "$warm_int" -gt 1000 ] 2>/dev/null; then
    color="$R"
  elif [ "$warm_int" -gt 300 ] 2>/dev/null; then
    color="$Y"
  else
    color="$G"
  fi
  printf "  %b%5d${N}  %4s  %-32s  %6d ms  %7s  %s\n" \
    "$color" "$warm_int" "$code" "$name" "$cold" "$size" "$path"
done
echo

# ── Zusammenfassung ──
echo
printf "${B}═══ Zusammenfassung ═══${N}\n"
total=$(wc -l < "$RESULTS_FILE")
fast=$(awk -F'\t' '$1 <= 300 && $5 < 400' "$RESULTS_FILE" | wc -l)
med=$(awk -F'\t'  '$1 > 300 && $1 <= 1000 && $5 < 400' "$RESULTS_FILE" | wc -l)
slow=$(awk -F'\t' '$1 > 1000 && $5 < 400' "$RESULTS_FILE" | wc -l)
errors=$(awk -F'\t' '$5 >= 400' "$RESULTS_FILE" | wc -l)

printf "  ${G}✓${N} Schnell (<300 ms):   %d/%d\n" "$fast" "$total"
printf "  ${Y}~${N} Mittel (300-1000 ms): %d/%d\n" "$med" "$total"
printf "  ${R}✗${N} Langsam (>1000 ms):  %d/%d\n" "$slow" "$total"
printf "  ${R}!${N} Errors (>=400):       %d/%d\n" "$errors" "$total"
echo
