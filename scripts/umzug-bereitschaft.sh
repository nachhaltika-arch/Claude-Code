#!/usr/bin/env bash
#
# KOMPAGNON — Ist der Frankfurter Dienst bereit, die Domain zu übernehmen?
#
#   Aufruf:  scripts/umzug-bereitschaft.sh [dienst-adresse] [referenz-adresse]
#   Vorgabe: https://kompagnon-backend-fra.onrender.com
#            https://kompagnon-backend-staging.onrender.com (die Referenz)
#
# **Warum es das gibt.** Am 21.08.2026 fiel eine Reihenfolge-Falle auf, die von
# außen wie Gesundheit aussieht: Frankfurt hat Auto-Deploy **Off**, und die CI
# deployt nach `RENDER_SERVICE_BACKEND_PROD` — das stand auf Oregon. Ein Merge
# nach `main` erreicht Frankfurt also gar nicht. Wer danach die Domain umhängt,
# schaltet die 55 am 19.08. geschlossenen Routen wieder scharf. `/health`
# antwortet dabei weiter in 0,17 s, und `/openapi.json` ist byte-identisch:
# **Die beiden Prüfungen, die man zuerst macht, sagen genau hier nichts.**
#
# Der einzige Unterschied, der ohne Zugangsdaten messbar ist, liegt in der
# Laufzeit: Der Zugriffsschutz hängt an `dependencies=` der Router, nicht an
# einem Pfad. Deshalb prüft dieses Skript nicht, ob Routen *existieren*,
# sondern was sie **antworten, wenn niemand angemeldet ist**.
#
# Beendet sich mit 0 nur, wenn jede Prüfung hält. Ein Fehlschlag nennt die
# Prüfung, den erwarteten und den erhaltenen Wert — nicht nur „fehlgeschlagen".

set -uo pipefail

DIENST="${1:-https://kompagnon-backend-fra.onrender.com}"

# Die Vollstaendigkeit wird **gegen einen laufenden Dienst** gemessen, nicht
# gegen eine Zahl im Skript. Eine feste Zahl veraltet mit dem naechsten Merge:
# am 21.08. trug Frankfurt 401 Routen und Staging bereits 404 — fuenf neue
# (Modulzuweisung, Fehlerprotokoll) und zwei entfallene (`/api/courses/*` aus
# der Kurs-Zusammenfuehrung). Eine hart notierte 401 haette hier den Falschen
# beschuldigt.
REFERENZ="${2:-https://kompagnon-backend-staging.onrender.com}"

# Bewusst großzügig: Ein kalt gestarteter Render-Dienst braucht beim ersten
# Aufruf länger als im Betrieb. Zu knapp gesetzt misst man den Kaltstart und
# hält ihn für einen Ausfall.
TIMEOUT_SEKUNDEN=60
GESUND_MAX_SEKUNDEN=2.0

fehler=0

melde_ok()    { printf '  \033[32m✓\033[0m %s\n' "$1"; }
melde_fehler() { printf '  \033[31m✗\033[0m %s\n' "$1"; fehler=$((fehler + 1)); }

# Ruft einen Pfad ohne jede Anmeldung auf und vergleicht den Statuscode.
pruefe_status() {
  local pfad="$1" erwartet="$2" warum="$3" ist
  ist="$(curl -s -o /dev/null -w '%{http_code}' --max-time "$TIMEOUT_SEKUNDEN" "$DIENST$pfad")"

  if [ "$ist" = "$erwartet" ]; then
    melde_ok "$pfad → $ist ($warum)"
  else
    melde_fehler "$pfad → $ist, erwartet $erwartet ($warum)"
  fi
}

echo "▸ Dienst:   $DIENST"
echo "▸ Referenz: $REFERENZ"
echo

# ---------------------------------------------------------------------------
echo "1 · Läuft er überhaupt, und ist der Start durchgelaufen?"
# ---------------------------------------------------------------------------
gesundheit="$(curl -s --max-time "$TIMEOUT_SEKUNDEN" -w '\n%{time_total}' "$DIENST/health")"
dauer="$(printf '%s' "$gesundheit" | tail -1)"
rumpf="$(printf '%s' "$gesundheit" | sed '$d')"

if [ -z "$rumpf" ]; then
  melde_fehler "/health antwortet nicht — alles Weitere wäre Raten"
  echo
  echo "✗ 1 Prüfung fehlgeschlagen. Die Domain bleibt, wo sie ist."
  exit 1
fi

lies() { printf '%s' "$rumpf" | python3 -c "
import json,sys
try: print(json.load(sys.stdin).get('$1', '—'))
except Exception: print('—')
"; }

[ "$(lies status)" = "ok" ]              && melde_ok "status: ok"                   || melde_fehler "status: $(lies status), erwartet ok"
[ "$(lies database)" = "connected" ]     && melde_ok "database: connected"           || melde_fehler "database: $(lies database), erwartet connected"
[ "$(lies startup_complete)" = "True" ]  && melde_ok "startup_complete"              || melde_fehler "startup_complete: $(lies startup_complete)"
[ "$(lies scheduler_running)" = "True" ] && melde_ok "scheduler_running"             || melde_fehler "scheduler_running: $(lies scheduler_running)"

fehlend="$(lies startup_missing)"
[ "$fehlend" = "[]" ] && melde_ok "startup_missing leer" \
                      || melde_fehler "startup_missing: $fehlend — Startphasen sind ausgefallen (L-41)"

if awk -v d="$dauer" -v m="$GESUND_MAX_SEKUNDEN" 'BEGIN{exit !(d<m)}'; then
  melde_ok "/health in ${dauer}s"
else
  melde_fehler "/health in ${dauer}s, erwartet unter ${GESUND_MAX_SEKUNDEN}s — das ist Oregons Wert"
fi

# ---------------------------------------------------------------------------
echo
echo "2 · Trägt er den aktuellen Stand? (der Punkt, an dem /health lügt)"
# ---------------------------------------------------------------------------
pruefe_status /api/dashboard/kpis 401 "Marge und Kundennamen — vor dem 19.08. offen"
pruefe_status /api/webhooks/log   401 "Webhook-Protokoll — vor dem 19.08. offen"
pruefe_status /api/leads/         401 "Betriebsliste"

# **Bewusst nicht geprüft: `/api/audit/{id}` (L-52).** Der Versuch stand hier
# und bestand — aber aus dem falschen Grund: Auf dem alten Stand antwortet die
# Route 404, weil es das Audit **nicht gibt**, nicht weil sie geschützt wäre.
# Eine Prüfung, die aus dem falschen Grund grün wird, ist schlechter als keine.
# Datenabhängige Pfade taugen hier ohnehin nicht: Frankfurt und Oregon teilen
# die Produktivdaten, die Referenz Staging hat eigene.

# ---------------------------------------------------------------------------
echo
echo "3 · Ist die Anwendung vollständig, und antwortet das Öffentliche noch?"
# ---------------------------------------------------------------------------
pfade() {
  curl -s --max-time "$TIMEOUT_SEKUNDEN" "$1/openapi.json" \
    | python3 -c "import json,sys; print('\n'.join(sorted(json.load(sys.stdin)['paths'])))" 2>/dev/null
}

pfade "$DIENST"   > /tmp/kompagnon-pfade-dienst.txt
pfade "$REFERENZ" > /tmp/kompagnon-pfade-referenz.txt

anzahl_dienst=$(wc -l < /tmp/kompagnon-pfade-dienst.txt | tr -d ' ')
anzahl_referenz=$(wc -l < /tmp/kompagnon-pfade-referenz.txt | tr -d ' ')

if [ "$anzahl_referenz" = "0" ]; then
  # Nicht als Fehlschlag zaehlen: Dann ist die Referenz kaputt, nicht der Dienst.
  printf '  \033[33m!\033[0m Referenz %s antwortet nicht — Vollstaendigkeit ungeprueft\n' "$REFERENZ"
elif [ "$anzahl_dienst" = "$anzahl_referenz" ] \
  && diff -q /tmp/kompagnon-pfade-dienst.txt /tmp/kompagnon-pfade-referenz.txt >/dev/null; then
  melde_ok "$anzahl_dienst Routen, deckungsgleich mit der Referenz"
else
  melde_fehler "$anzahl_dienst Routen gegen $anzahl_referenz der Referenz — Abweichung:"
  diff /tmp/kompagnon-pfade-referenz.txt /tmp/kompagnon-pfade-dienst.txt \
    | grep -E '^[<>]' | sed 's/^</      fehlt:      /; s/^>/      zusaetzlich:/'
fi

pruefe_status /api/widget/config 200 "das Widget auf Kundenseiten muss weiter antworten"

# ---------------------------------------------------------------------------
echo
if [ "$fehler" -eq 0 ]; then
  echo "✓ Alle Prüfungen halten. Der Dienst kann die Domain übernehmen."
  exit 0
fi

echo "✗ $fehler Prüfung(en) fehlgeschlagen. Die Domain bleibt, wo sie ist."
echo
echo "  Häufigster Grund: Auto-Deploy ist Off und der Dienst wurde seit dem"
echo "  letzten Merge nach \`main\` nie neu gebaut. Dann im Render-Dashboard"
echo "  einmal \"Manual Deploy → Deploy latest commit\" auslösen und erneut messen."
exit 1
