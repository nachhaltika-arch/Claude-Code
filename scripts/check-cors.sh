#!/bin/bash
# Steht die Verbindung Browser -> Backend? (BUCH-09)
#
#     bash scripts/check-cors.sh https://meine-seite.netlify.app
#     bash scripts/check-cors.sh https://meine-seite.netlify.app https://kompagnon-backend-staging.onrender.com
#
# **Warum ein Skript und kein Blick ins Log.** Fehlt die Erlaubnis, haelt der
# Browser die Anfrage an, bevor sie ankommt: Im Render-Log steht nichts, in
# Stripe nichts, in der Datenbank nichts. Der einzige Ort, an dem die Wahrheit
# steht, ist die Browserkonsole — oder dieser Aufruf.
#
# **Die Standardadresse ist Frankfurt.** In der Auftragsdatei BUCH-09 steht
# `claude-code-znq2.onrender.com`; dieser Dienst liegt in Oregon, ist seit dem
# Umzug (L-34) suspendiert und antwortet mit 503. Wer dagegen prueft, misst
# einen Ausfall, den es nicht gibt.
set -u

HERKUNFT="${1:-}"
API="${2:-https://api.kompagnon.group}"

if [ -z "$HERKUNFT" ]; then
  echo "Aufruf: bash scripts/check-cors.sh <https://herkunft> [https://backend]" >&2
  exit 2
fi

case "$HERKUNFT" in
  */) echo "WARNUNG: Schraegstrich am Ende — der Browser vergleicht zeichengenau und trifft nie." >&2 ;;
esac

echo "Herkunft: $HERKUNFT"
echo "Backend:  $API"
echo
echo "--- Preflight (OPTIONS /api/book/checkout) ---"
kopf=$(curl -s -i -X OPTIONS "$API/api/book/checkout" \
  -H "Origin: $HERKUNFT" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type")

echo "$kopf" | grep -i "^HTTP/\|^access-control" || true

# **Die Zeile, auf die es ankommt.** Fehlt `access-control-allow-origin`
# vollstaendig, greift CORS nicht — und alles Weitere ist vergeblich.
if echo "$kopf" | grep -qi "^access-control-allow-origin"; then
  echo "OK: Der Preflight traegt access-control-allow-origin."
else
  echo "FEHLT: keine access-control-allow-origin-Zeile. Nicht weitermachen." >&2
  ausgang=1
fi

echo
echo "--- Auskunft (GET /api/health/cors) ---"
curl -s "$API/api/health/cors" -H "Origin: $HERKUNFT"
echo

exit "${ausgang:-0}"
