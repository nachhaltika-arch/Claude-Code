#!/usr/bin/env bash
#
# KOMPAGNON — Push auf `staging`, aber nur wenn nichts mehr läuft.
#
# Aufgerufen aus `.claude/settings.json` nach jedem Bash-Schritt.
#
# **Warum es das gibt.** Die Regel dort pushte bisher bedingungslos: bei jedem
# Bash-Aufruf, sobald etwas unversandt war. Der Workflow hat aber
# `cancel-in-progress` — jeder neue Push bricht den laufenden Lauf ab. Am
# 18.08.2026 endeten zwei Läufe so, einer davon mitten in Playwright. Ein
# abgebrochener Lauf ist nicht rot, sondern grau: Er sagt gar nichts, und wer
# nur auf „nicht rot" schaut, hält den Stand für geprüft.
#
# Deshalb drei Bedingungen, jede einzeln begründet:
#
#   1. Wir stehen auf `staging` — sonst geht der Push woandershin.
#   2. Es gibt überhaupt etwas zu senden.
#   3. Für den Zweig läuft gerade kein Lauf. Sonst warten wir; der nächste
#      Bash-Schritt versucht es erneut, und irgendwann ist die Bahn frei.
#
# Kann der Zustand nicht ermittelt werden (kein `gh`, keine Anmeldung, kein
# Netz), wird gepusht statt zu blockieren — ein liegengebliebener Commit ist
# schlimmer als ein abgebrochener Lauf.

set -uo pipefail

wurzel="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
cd "$wurzel" || exit 0

zweig="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
[ "$zweig" = "staging" ] || exit 0

# Ohne Gegenstück gibt es keinen Vergleich — dann ist Pushen das Richtige.
if git rev-parse --abbrev-ref '@{u}' > /dev/null 2>&1; then
  offen="$(git rev-list --count '@{u}..HEAD' 2>/dev/null || echo 0)"
  [ "${offen:-0}" -gt 0 ] || exit 0
fi

if command -v gh > /dev/null 2>&1; then
  zustand="$(gh run list --branch staging --limit 1 --json status \
             --jq '.[0].status' 2>/dev/null || echo "unbekannt")"
  case "$zustand" in
    in_progress|queued|requested|waiting|pending)
      echo "CI läuft noch ($zustand) — Push wartet auf den nächsten Schritt."
      exit 0
      ;;
  esac
fi

git push origin staging 2>&1 | tail -3
