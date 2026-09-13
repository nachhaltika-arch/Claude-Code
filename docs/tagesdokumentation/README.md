# Tagesdokumentation

Ein Eintrag je Arbeitstag, benannt nach dem Datum: `JJJJ-MM-TT.md`.

**Ab dem 12.09.2026 kommt jede neue Tagesdokumentation hierher** (Entscheidung
David, 12.09.2026). Vorher lagen sie als `docs/stand-JJJJ-MM-TT.md` direkt in
`docs/`.

## Die fünfzehn älteren bleiben, wo sie sind

`docs/stand-2026-08-08.md` bis `docs/stand-2026-09-08.md` werden **nicht**
umgezogen, und das ist kein Aufschieben:

* Die Spalte „Beleg" im Lagebild verweist auf sie, und `lagebild-bauen.py`
  erkennt einen Tagesbericht daran, dass `stand-` im Beleg steht
  (`scripts/lagebild-bauen.py`, `_herkunft`). Ein Umzug ohne Nacharbeit
  verwandelt fünfzehn Herkunftsangaben in „unbekannt".
* Sechs weitere Dateien verlinken sie mit Pfad.

Ein Umzug ist damit keine Dateiverschiebung, sondern eine Änderung an der
Herkunftserkennung des Lagebilds. Das ist machbar, aber es ist eigene Arbeit
und gehört nicht in den Nebensatz einer Ordneranlage.

## Was hineingehört

Was ein Tagesbericht leisten soll, steht in den bestehenden: **nicht** eine
Liste der Commits — die steht im Verlauf —, sondern das Muster des Tages, die
Funde samt Beleg, die **eigenen Fehler**, und was danach bei David liegt.

Die Zahlen darin werden gemessen, nicht geschätzt.
