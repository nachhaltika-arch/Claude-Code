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

if [ "$#" -eq 0 ]; then
  echo "Aufruf: bash scripts/ci-retry.sh <befehl> [argumente…]" >&2
  exit 2
fi

for attempt in $(seq 1 "$ATTEMPTS"); do
  # Der Status muss IM else-Zweig gelesen werden: nach einem abgeschlossenen
  # `if` ohne passenden Zweig steht in $? eine 0, nicht der Fehlercode.
  if "$@"; then
    exit 0
  else
    status=$?
  fi

  if [ "$attempt" -ge "$ATTEMPTS" ]; then
    echo "::error::Nach $ATTEMPTS Versuchen fehlgeschlagen (Exit $status): $*" >&2
    exit "$status"
  fi

  echo "::warning::Versuch $attempt fehlgeschlagen (Exit $status): $* — nächster Versuch in ${DELAY_SECONDS}s" >&2
  sleep "$DELAY_SECONDS"
done
