#!/usr/bin/env bash
#
# KOMPAGNON — Wiederholung für netzabhängige CI-Schritte
#
#   bash scripts/ci-retry.sh npm ci --legacy-peer-deps
#   bash scripts/ci-retry.sh pip install -r requirements.txt
#   CI_RETRY_ATTEMPTS=5 bash scripts/ci-retry.sh <befehl>
#
# Warum: Am 07.08. wurde ein Produktiv-Deploy übersprungen, weil `npm ci` mit
# `ETIMEDOUT` abbrach — ein Aussetzer der Registry, kein Codefehler. Jeder
# Schritt, der etwas aus dem Netz holt (npm, pip, Playwright-Browser,
# GitHub-Releases), kann daran scheitern.
#
# NUR für Installationen und Downloads verwenden — NIE für Tests. Ein
# wiederholter Test verdeckt Flakiness, statt sie zu zeigen.

set -uo pipefail

readonly ATTEMPTS="${CI_RETRY_ATTEMPTS:-3}"
readonly DELAY_SECONDS="${CI_RETRY_DELAY_SECONDS:-15}"
readonly TIMEOUT_SECONDS="${CI_RETRY_TIMEOUT_SECONDS:-600}"

# Warum eine Zeitgrenze je Versuch: Am 17.08. hing
# `npx playwright install --with-deps chromium` und lief sechs Stunden bis in
# GitHubs Notbremse. Ein Versuch, der nicht mehr antwortet, ist genauso
# gescheitert wie einer mit Fehlercode — nur teurer. Wird er abgebrochen,
# greift die normale Wiederholung.
#
# `timeout` gehoert zu den coreutils und fehlt auf macOS; dort laeuft der
# Befehl ohne Grenze weiter, statt die lokale Nutzung zu blockieren.
if command -v timeout > /dev/null 2>&1; then
  ZEITGRENZE=(timeout "$TIMEOUT_SECONDS")
elif command -v gtimeout > /dev/null 2>&1; then
  ZEITGRENZE=(gtimeout "$TIMEOUT_SECONDS")
else
  # `env` als wirkungsloser Vorspann: Ein leeres Feld waere unter bash 3.2
  # (macOS) mit `set -u` ein Fehler, kein leerer Aufruf.
  ZEITGRENZE=(env)
  echo "::warning::Kein timeout gefunden — Versuche laufen ohne Zeitgrenze" >&2
fi
readonly ZEITGRENZE

if [ "$#" -eq 0 ]; then
  echo "Aufruf: bash scripts/ci-retry.sh <befehl> [argumente…]" >&2
  exit 2
fi

for attempt in $(seq 1 "$ATTEMPTS"); do
  # Der Status muss IM else-Zweig gelesen werden: nach einem abgeschlossenen
  # `if` ohne passenden Zweig steht in $? eine 0, nicht der Fehlercode.
  if "${ZEITGRENZE[@]}" "$@"; then
    exit 0
  else
    status=$?
  fi

  # 124 ist der Abbruch durch `timeout` — deutlich benennen, sonst sucht man
  # den Fehler im Befehl statt in der Wartezeit.
  if [ "$status" -eq 124 ]; then
    grund="Zeitgrenze von ${TIMEOUT_SECONDS}s überschritten"
  else
    grund="Exit $status"
  fi

  if [ "$attempt" -ge "$ATTEMPTS" ]; then
    echo "::error::Nach $ATTEMPTS Versuchen fehlgeschlagen ($grund): $*" >&2
    exit "$status"
  fi

  echo "::warning::Versuch $attempt fehlgeschlagen ($grund): $* — nächster Versuch in ${DELAY_SECONDS}s" >&2
  sleep "$DELAY_SECONDS"
done
