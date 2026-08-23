#!/usr/bin/env python3
"""Welche Frontend-Dateien erreicht die Anwendung nicht?

    python3 tools/unerreichbare-dateien.py

**Warum es dieses Werkzeug gibt.** Am 23.08.2026 fiel bei L-65 auf, dass
`Landing.jsx` — 569 Zeilen mit unbelegten Werbesiegeln — von **keiner** Datei
importiert wird. Belegt war das nicht an der Importsuche, sondern am
ausgelieferten Paket: „Trusted Shops" steht nur in dieser Datei und hat im
Produktiv-Bundle null Treffer.

Die Frage danach war die interessantere: Wie viele solcher Dateien gibt es?

**Warum eine Wortsuche hier nicht reicht** — das ist der Grund, warum dieses
Werkzeug mehr tut als `grep`. Der erste Anlauf suchte den Dateinamen im
Quelltext und meldete vier Dateien als „doch benutzt". Alle vier waren
Falschtreffer:

- `Navbar` stand in einem **Kommentar** (`{/* App — with Navbar/Sidebar */}`)
- `AuditHistory` stand in **Log-Präfixen** (`console.error('[AuditHistory] …')`)
  in `CustomerDetail.jsx` — die Komponente wurde dorthin kopiert, die Lognamen
  blieben zurück
- `Landing` stand in `'Landing'` als Wert einer Seitentyp-Liste und in
  Kommentaren über „Landingpages"

Gezählt wird deshalb nur, was eine **Import-Anweisung** ist.

**Die zweite Kategorie, die dieses Werkzeug ausweist:** Dateien, die
ausschließlich von **Tests** importiert werden. Sie sind heimtückischer als
schlicht toter Code — sie haben grüne Tests, und die Tests prüfen etwas, das
die Anwendung nie ausführt.

**Was das Werkzeug nicht kann:** Es liest keine dynamischen Pfade
(`import(\`./seiten/${name}\`)`). Kommt so etwas dazu, meldet es zu viel. Der
Ausdruck deckt heute `from`, `import(...)` und `require(...)` ab.
"""
import pathlib
import re
import sys

WURZEL = pathlib.Path(__file__).resolve().parent.parent / "kompagnon" / "frontend" / "src"

# Einstiegspunkte und Werkzeugdateien, die niemand importieren muss.
EINSTIEGE = {"index", "App", "setupTests", "reportWebVitals"}


def ist_test(pfad: pathlib.Path) -> bool:
    return ".test." in pfad.name or ".spec." in pfad.name


def importiert(stamm: str, text: str) -> bool:
    """Nur echte Import-Anweisungen — keine Kommentare, keine Zeichenketten."""
    muster = (
        rf"from\s+['\"][^'\"]*/{re.escape(stamm)}(\.jsx?)?['\"]"
        rf"|import\s*\(\s*['\"][^'\"]*/{re.escape(stamm)}(\.jsx?)?['\"]"
        rf"|require\s*\(\s*['\"][^'\"]*/{re.escape(stamm)}(\.jsx?)?['\"]"
    )
    return re.search(muster, text) is not None


def main() -> int:
    if not WURZEL.is_dir():
        print(f"Nicht gefunden: {WURZEL}", file=sys.stderr)
        return 2

    alle = sorted(p for p in WURZEL.rglob("*")
                  if p.suffix in (".js", ".jsx") and "__" not in str(p))
    inhalte = {p: p.read_text(encoding="utf-8", errors="ignore") for p in alle}

    nur_tests, unerreichbar = [], []

    for pfad, text in inhalte.items():
        if pfad.stem in EINSTIEGE or ist_test(pfad):
            continue

        von_anwendung = any(
            importiert(pfad.stem, t) for p2, t in inhalte.items()
            if p2 != pfad and not ist_test(p2)
        )
        if von_anwendung:
            continue

        von_tests = any(
            importiert(pfad.stem, t) for p2, t in inhalte.items()
            if p2 != pfad and ist_test(p2)
        )
        zeilen = len(text.splitlines())
        (nur_tests if von_tests else unerreichbar).append((zeilen, pfad))

    nur_tests.sort(reverse=True)
    unerreichbar.sort(reverse=True)

    def zeige(titel: str, liste: list, hinweis: str) -> None:
        if not liste:
            print(f"\n{titel}: keine")
            return
        summe = sum(z for z, _ in liste)
        print(f"\n{titel} — {len(liste)} Dateien, {summe} Zeilen")
        print(f"  {hinweis}")
        for zeilen, pfad in liste:
            print(f"    {zeilen:>5}  {pfad.relative_to(WURZEL.parent)}")

    print(f"Geprüft: {len(inhalte)} Dateien unter {WURZEL}")
    zeige("Von der Anwendung nicht erreicht", unerreichbar,
          "Kein Import ausserhalb der Datei selbst — auch nicht aus Tests.")
    zeige("Nur von Tests importiert", nur_tests,
          "Gruene Tests fuer Code, den die Anwendung nie ausfuehrt.")

    gesamt = sum(z for z, _ in unerreichbar + nur_tests)
    print(f"\nSumme: {gesamt} Zeilen, die kein Nutzerweg erreicht.")
    print("Loeschen ist eine Entscheidung, kein Aufraeumen — manches ist "
          "absichtlich geparkt. Dieses Werkzeug nennt nur den Bestand.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
