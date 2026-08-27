#!/usr/bin/env bash
#
# KOMPAGNON — Frontend bauen und dabei „kaputt" von „unsauber" trennen
#
#   bash scripts/frontend-bauen.sh
#
# Warum es dieses Skript gibt (L-102, gefunden am 23.08.2026, belegt am
# 24.08.2026):
#
# Die CI setzt `CI: false` fuer den Bau. Das ist Absicht — mit `CI: true`
# macht react-scripts jede Lint-Warnung zum Fehler, und es gibt 53
# `no-unused-vars`. Der Job waere dauerhaft rot, ohne dass etwas kaputt ist.
#
# Der Preis dafuer war unsichtbar: **Ein nicht aufloesbarer dynamischer Import
# in einem `try`-Block ist fuer Webpack nur eine Warnung.** Webpack nimmt an,
# der `catch` fange das zur Laufzeit ab — also „Compiled with warnings",
# Rueckgabewert 0, Bundle gebaut, Job gruen.
#
# Am 22.08. ist genau das passiert. Beim Aufteilen von `ProzessFlow.jsx`
# (Commit 23f5ec2) wanderte `marketing.jsx` einen Ordner tiefer, der relative
# Pfad `'../grapesjs/handwerk-blocks'` blieb stehen und zeigte ins Leere.
# Lauf 32596544696 auf `staging`: **success** — mit „Module not found" im
# Protokoll. Die Design-Erzeugung im Prozessflow war seither tot und meldete
# der Oberflaeche nur „Fehler".
#
# Nachgestellt statt geraten: Derselbe Import ohne `try` faellt mit
# „Failed to compile" und Rueckgabewert 1 durch. Erst der `try`-Block macht
# daraus eine Warnung. Das ist der Unterschied, den dieses Skript schliesst.
#
# Der Schnitt ist bewusst klein: Es hebt die Latte nicht fuer alles, sondern
# nur fuer die Warnungen, die ein **gebrochenes Modul** melden. Beide Muster
# kommen im sauberen Baum null Mal vor — am 24.08.2026 nachgezaehlt.

set -uo pipefail

# Muster, die ein gebrochenes Modul melden — nicht bloss einen Schoenheitsfehler:
#
#   „Module not found"  — der Pfad zeigt ins Leere (der Fall vom 22.08.)
#   „was not found in"  — die Datei gibt es, den benannten Export nicht
#
# Beides bedeutet: Ein Import laeuft zur Laufzeit ins Leere. Lint-Warnungen
# (`no-unused-vars`, `react-hooks/exhaustive-deps` …) bleiben Warnungen.
readonly BRUCHMUSTER='Module not found|was not found in'

protokoll="$(mktemp)"
trap 'rm -f "$protokoll"' EXIT

npm run build 2>&1 | tee "$protokoll"
readonly BAU_STATUS="${PIPESTATUS[0]}"

if [ "$BAU_STATUS" -ne 0 ]; then
  exit "$BAU_STATUS"
fi

if grep -qE "$BRUCHMUSTER" "$protokoll"; then
  echo ""
  echo "::error::Der Bau ist durchgelaufen, aber mindestens ein Import zeigt ins Leere (L-102)."
  echo "Der Rueckgabewert war 0, weil Webpack ein nicht aufloesbares import() im try-Block"
  echo "nur als Warnung meldet. Zur Laufzeit scheitert es trotzdem. Betroffen:"
  echo ""
  grep -nE "$BRUCHMUSTER" "$protokoll"
  exit 1
fi

echo ""
echo "Bau sauber: kein gebrochener Import im Protokoll."
