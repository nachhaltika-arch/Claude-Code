#!/usr/bin/env python3
"""Ein Audit gegen fremde Websites — und der Blick auf die **Erhebung**, nicht auf den Score.

**Wofuer (S8.5, § 9 Pruefpunkt 5).** Der Standard verspricht wiederholbare
Messung. Belegt ist das fuer *eine* fremde Seite (nachhaltika.de, K2). Der
erste Fremdlauf hat fuenf Erhebungsfehler freigelegt — darunter eine
Fehlerseite, die als Messung zaehlte, und `/llm.txt` statt `/llms.txt`. Beide
sind inzwischen behoben. Zwei weitere Klassenlaeufe sollen finden, was noch
niemand gesehen hat.

**Was es ausdruecklich NICHT erhebt (seit dem 28.08.2026 in der Ausgabe
getrennt).** Es ruft `collect_facts`, aber weder einen Bildschirmabzug noch
ein Sprachmodell — der echte Auditweg (`routers.audit._gather`) macht beides
parallel. Die sechs `Source.AI`-Kriterien fallen hier deshalb **bei jeder
Seite** aus. Bis sie getrennt wurden, standen sie in derselben Liste wie eine
echte Fehlmessung: Im Lauf vom 28.08. gegen `gutdurchdacht.de` waren **sechs
von acht** gemeldeten Luecken die des Werkzeugs, nicht die der Website. Ein
Werkzeug, das eigene blinde Stellen als fremde Befunde ausgibt, ist schlimmer
als keines.

**Was dieses Werkzeug ausgibt.** Nicht die Punktzahl. Punkte sind hier
uninteressant, weil niemand weiss, ob sie stimmen — genau das ist die Frage.
Ausgegeben wird, **was ausfiel und warum**: welche Erhebung nicht lieferte,
welche Kriterien deshalb aus der Wertung fallen, und die Handvoll Anzeichen,
an denen sich eine stille Fehlmessung erkennen laesst.

**Was es braucht.**

    GOOGLE_PAGESPEED_API_KEY   sonst fallen P1-P4 aus (anonymes Kontingent
                               ist in der Praxis erschoepft)
    ANTHROPIC_API_KEY          sonst fallen C1-C5, D1-D5 und I3 aus

Ohne beide bleibt die HTML-Haelfte — die ist nicht wertlos, aber ein Lauf,
der zwei Drittel des Katalogs ueberspringt, belegt keine Wiederholbarkeit.
Das Werkzeug sagt das im Kopf der Ausgabe, damit niemand ein Teilergebnis
fuer das Ergebnis nimmt.

**Last.** Ein Lauf holt Startseite, Rechtsseiten, Unterseiten und prueft bis
zu 100 Verweise — in der Groessenordnung hundert Anfragen an eine fremde
Domain. Deshalb nimmt das Werkzeug die Ziele als Argument und hat keine
eingebaute Liste: Welche fremde Seite so angefasst wird, entscheidet nicht
das Programm.

    python3 tools/klassenlauf.py K2=https://beispiel.de K3=https://anderes.de
"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.audit_criteria import Source, all_criteria  # noqa: E402
from services.audit_runner import collect_facts  # noqa: E402
from services.audit_scoring import score_audit  # noqa: E402

# Anzeichen einer stillen Fehlmessung: Werte, die formal da sind und
# inhaltlich nichts bedeuten. Der erste Fremdlauf ist genau daran haengen
# geblieben — eine Fehlerseite hat Text, eine Ueberschrift und ein <title>.
FEHLERSEITEN_WORTE = ("404", "not found", "seite nicht gefunden", "error",
                      "zugriff verweigert", "forbidden")


def _schluessel_lage() -> list:
    lage = []
    for name, wofuer in (("GOOGLE_PAGESPEED_API_KEY", "P1-P4"),
                         ("ANTHROPIC_API_KEY", "C1-C5, D1-D5, I3")):
        da = bool((os.getenv(name) or "").strip())
        lage.append(f"  {'✓' if da else '✗'} {name} — ohne ihn fallen {wofuer} aus")
    return lage


def _verdachtsmomente(fakten: dict) -> list:
    """Wo die Erhebung geliefert hat, ohne etwas gemessen zu haben."""
    hinweise = []
    qa = fakten.get("qa") or {}

    titel = str(qa.get("title_text") or "").lower()
    if any(w in titel for w in FEHLERSEITEN_WORTE):
        hinweise.append(f"Der <title> sieht nach Fehlerseite aus: {titel!r}")

    woerter = fakten.get("word_count") or 0
    if 0 < woerter < 50:
        hinweise.append(f"Nur {woerter} Woerter — Startseite oder Abwehrseite?")

    if fakten.get("reachable") and not qa:
        hinweise.append("Startseite erreichbar, aber der QA-Scanner lieferte nichts")

    legal = fakten.get("legal") or {}
    for block in ("impressum", "datenschutz"):
        seite = legal.get(block) or {}
        if seite.get("reachable") and not seite.get("fields"):
            hinweise.append(f"{block}: erreichbar, aber kein einziges Feld erkannt")

    return hinweise


def _ausfaelle(fakten: dict) -> list:
    """Welche Erhebung nicht geliefert hat — mit dem Grund, den sie nennt."""
    zeilen = []
    for name, wert in sorted(fakten.items()):
        if not isinstance(wert, dict) or "collected" not in wert:
            continue
        if wert.get("collected") is True:
            continue
        grund = wert.get("reason") or "ohne Angabe"
        detail = str(wert.get("detail") or "")[:80]
        zeilen.append(f"  ✗ {name}: {grund}" + (f" — {detail}" if detail else ""))
    return zeilen


async def _ein_lauf(klasse: str, url: str) -> None:
    print(f"\n{'═' * 70}\n{klasse}  {url}\n{'═' * 70}")

    fakten = await collect_facts(url)
    if not fakten.get("reachable"):
        print(f"  Nicht erreichbar: HTTP {fakten.get('status_code')} "
              f"{fakten.get('error', '')}")
        return

    ergebnis = score_audit(fakten)
    quellen = ergebnis["sources"]

    ausfaelle = _ausfaelle(fakten)
    print(f"\nErhebungen ohne Ergebnis ({len(ausfaelle)}):")
    print("\n".join(ausfaelle) if ausfaelle else "  — keine")

    nicht_erhoben = [c for c in all_criteria()
                     if quellen.get(c.key) == Source.NOT_COLLECTED.value]

    # **Die eigene blinde Stelle zuerst (L-113, 28.08.2026).** Dieses Werkzeug
    # ruft `collect_facts`, aber **keinen** Bildschirmabzug und keine KI — der
    # echte Auditweg (`routers.audit._gather`) macht beides. Die sechs
    # `Source.AI`-Kriterien fallen hier also **immer** aus, und zwar bei jeder
    # Seite. Sie in dieselbe Liste zu schreiben wie eine echte Fehlmessung
    # hiesse, dem Werkzeug einen Befund unterzuschieben, der aus ihm selbst
    # kommt: 6 von 8 Meldungen im Lauf vom 28.08. waren genau das.
    eigene_luecke = [c for c in nicht_erhoben if c.source == Source.AI]
    echte_luecke = [c for c in nicht_erhoben if c.source != Source.AI]

    verloren = sum(c.max_points for c in echte_luecke)
    print(f"\nKriterien ohne Messung: {len(echte_luecke)} von "
          f"{len(list(all_criteria()))} ({verloren} von 103 Punkten)")
    for c in echte_luecke:
        print(f"  ⚪ {c.buch_code} {c.key} ({c.max_points} P) — {c.buch_label}")
    if not echte_luecke:
        print("  — keine")

    if eigene_luecke:
        print(f"\nVon diesem Werkzeug nicht erhoben ({len(eigene_luecke)}) — "
              f"**kein** Befund ueber die Website:")
        print("  Es holt keinen Bildschirmabzug und befragt kein Modell; der "
              "Auditweg tut beides.")
        for c in eigene_luecke:
            print(f"  ◻ {c.buch_code} {c.key} ({c.max_points} P) — {c.buch_label}")

    verdacht = _verdachtsmomente(fakten)
    if verdacht:
        print("\nAnzeichen einer stillen Fehlmessung:")
        for v in verdacht:
            print(f"  ⚠ {v}")

    print(f"\nScore {ergebnis['total_score']}/100 · {ergebnis['level']} · "
          f"Abdeckung {ergebnis.get('coverage')}%")
    print("Die Punktzahl steht hier nur als Anhalt. Geprueft wird die "
          "Erhebung, nicht der Betrieb.")


async def main(ziele: list) -> None:
    print("Schluessellage:")
    print("\n".join(_schluessel_lage()))
    for ziel in ziele:
        klasse, _, url = ziel.partition("=")
        if not url:
            print(f"Uebersprungen — erwartet KLASSE=URL, bekam {ziel!r}")
            continue
        await _ein_lauf(klasse, url)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    asyncio.run(main(sys.argv[1:]))
