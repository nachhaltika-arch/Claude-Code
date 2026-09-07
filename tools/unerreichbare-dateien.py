#!/usr/bin/env python3
"""Welche Dateien erreicht die Anwendung nicht?

    python3 tools/unerreichbare-dateien.py            # beide Bereiche
    python3 tools/unerreichbare-dateien.py frontend   # nur einer

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

**Warum seit dem 24.08.2026 auch das Backend (L-11).** Der Befund zu L-11
trug einen Nebenbefund: `app/utils/encryption.py` werde von niemandem
importiert — „dasselbe wie L-95, nur im Backend, wo das Werkzeug bisher nicht
hinsieht". Genau das war der Punkt: Ein Werkzeug, das nur eine Haelfte des
Hauses prueft, laesst die andere Haelfte von Hand finden. Beim Nachsehen war
nicht nur die eine Datei tot, sondern das **ganze `app/`-Paket** — vier
Dateien, 14 Zeilen, und nichts ausserhalb nannte es.

**Was das Werkzeug nicht kann:** Es liest keine zusammengesetzten Pfade
(``import(`./seiten/${name}`)``). Kommt so etwas dazu, meldet es zu viel.

**Eine zusammengesetzte Stelle gibt es im Backend, und die ist abgedeckt:**
`main.py` laedt die vier Academy-Router ueber
``__import__(f'routers.{_name}')``. Die Namen stehen als Zeichenketten
daneben. Deshalb gilt ein Modul auch dann als erreicht, wenn sein Name als
eigenstaendige Zeichenkette in einer Datei steht, die dynamisch importiert —
eng genug, um nicht jede Zeichenkette gelten zu lassen.
"""
import ast
import pathlib
import re
import sys

WURZEL = pathlib.Path(__file__).resolve().parent.parent

#: Ordner, die in keinem Bereich mitgezaehlt werden.
UEBERSPRINGEN = ("node_modules", "venv", "__pycache__", ".git", "build", "dist")

#: Formen, in denen ein Modul zur Laufzeit geholt wird.
DYNAMISCH = ("__import__", "import_module")


# ── Frontend ───────────────────────────────────────────────────────────

def frontend_importiert(stamm: str, text: str) -> bool:
    """Nur echte Import-Anweisungen — keine Kommentare, keine Zeichenketten."""
    muster = (
        rf"from\s+['\"][^'\"]*/{re.escape(stamm)}(\.jsx?)?['\"]"
        rf"|import\s*\(\s*['\"][^'\"]*/{re.escape(stamm)}(\.jsx?)?['\"]"
        rf"|require\s*\(\s*['\"][^'\"]*/{re.escape(stamm)}(\.jsx?)?['\"]"
    )
    return re.search(muster, text) is not None


#: Dieselben drei Formen wie in `frontend_importiert`, nur ohne festen Namen —
#: fuer den **Graphen**, der einmal gebaut wird statt bei jedem Vergleich neu.
_FRONTEND_PFADE = re.compile(
    r"""from\s+['"]([^'"]+)['"]"""
    r"""|import\s*\(\s*['"]([^'"]+)['"]"""
    r"""|require\s*\(\s*['"]([^'"]+)['"]""")


def frontend_zielstaemme(text: str) -> set:
    """Die Dateinamen ohne Endung, die diese Datei importiert."""
    staemme = set()
    for treffer in _FRONTEND_PFADE.finditer(text):
        pfad = next(g for g in treffer.groups() if g)
        if "/" not in pfad:        # Paket aus node_modules, keine eigene Datei
            continue
        name = pfad.rsplit("/", 1)[-1]
        staemme.add(re.sub(r"\.jsx?$", "", name))
    return staemme


def frontend_ist_test(pfad: pathlib.Path) -> bool:
    return ".test." in pfad.name or ".spec." in pfad.name


# ── Backend ────────────────────────────────────────────────────────────

def backend_modulpfad(pfad: pathlib.Path, wurzel: pathlib.Path) -> tuple:
    """`routers/payments.py` → `("routers", "payments")`."""
    teile = pfad.relative_to(wurzel).with_suffix("").parts
    return teile[:-1] if teile and teile[-1] == "__init__" else teile


def backend_ziele(pfad: pathlib.Path, wurzel: pathlib.Path, text: str) -> set:
    """Alle Module, die diese Datei importiert — als absolute Pfade.

    **Warum `ast` und nicht ein Ausdruck.** Der erste Anlauf am 24.08.2026
    suchte den **Dateinamen** im Text, so wie es die Frontend-Haelfte tut. Das
    Ergebnis war Unsinn: `routers/payments.py` und `routers/customers.py`
    galten als „nur von Tests importiert", obwohl `main.py` sie laedt — denn
    eingebunden werden sie als `from .payments import router as
    payments_router`, und der Name im Text ist `payments_router`.

    Umgekehrt blieb `app/utils/encryption.py` **unsichtbar**, obwohl es der
    Anlass war: Es teilt seinen Dateinamen mit `utils/encryption.py`, und das
    wird importiert. In Python entscheidet der **Modulpfad**, nicht der
    Dateiname — genau die Verwechslung, vor der der Kopf dieser Datei warnt,
    einmal beim Autor selbst.

    `ast` liest die Anweisungen statt den Text: Kommentare und Zeichenketten
    koennen keinen Treffer erzeugen, und `from . import x` traegt seine
    Ebene mit.
    """
    try:
        baum = ast.parse(text)
    except SyntaxError:
        return set()

    # **Das Paket ist der Ordner, nicht der Modulpfad minus eins.** Fuer ein
    # `__init__.py` sind beide verschieden: `routers/__init__.py` hat den
    # Modulpfad `("routers",)`, sein Paket ist aber ebenfalls `("routers",)`.
    # Mit „Modulpfad minus eins" wurde daraus `()`, und damit landete
    # `from . import projects_content` bei `("projects_content",)` statt bei
    # `("routers", "projects_content")` — sieben Router galten als tot,
    # obwohl `routers/__init__.py` sie genau so einbindet.
    eigenes_paket = pfad.parent.relative_to(wurzel).parts
    ziele = set()

    for knoten in ast.walk(baum):
        if isinstance(knoten, ast.Import):
            for name in knoten.names:
                teile = tuple(name.name.split("."))
                # Auch die Zwischenpakete gelten als beruehrt.
                ziele.update(teile[:i] for i in range(1, len(teile) + 1))

        elif isinstance(knoten, ast.ImportFrom):
            if knoten.level:
                basis = eigenes_paket[:len(eigenes_paket) - (knoten.level - 1)]
            else:
                basis = ()
            if knoten.module:
                basis = basis + tuple(knoten.module.split("."))
            ziele.add(basis)
            # `from paket import modul` — der Name kann ein Modul sein.
            ziele.update(basis + (n.name,) for n in knoten.names)

    return ziele


def backend_dynamische_namen(text: str) -> set:
    """Modulnamen, die als Zeichenkette neben einem dynamischen Import stehen.

    `main.py` laedt die vier Academy-Router ueber
    ``__import__(f'routers.{_name}')``, die Namen stehen als Zeichenketten in
    der Schleife daneben. Nur Dateien, die ueberhaupt dynamisch importieren,
    werden so gelesen — sonst gaelte jede Zeichenkette als Import.
    """
    if not any(form in text for form in DYNAMISCH):
        return set()
    return set(re.findall(r"['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]", text))


def backend_ist_test(pfad: pathlib.Path) -> bool:
    return pfad.name.startswith("test_") or "tests" in pfad.parts


# ── Die zwei Bereiche ──────────────────────────────────────────────────

BEREICHE = {
    "frontend": {
        "titel": "Frontend",
        "wurzel": WURZEL / "kompagnon" / "frontend" / "src",
        "endungen": (".js", ".jsx"),
        # Einstiegspunkte und Werkzeugdateien, die niemand importieren muss.
        "einstiege": {"index", "App", "setupTests", "reportWebVitals"},
        "einstiegs_ordner": (),
        "sprache": "javascript",
        "ist_test": frontend_ist_test,
    },
    "backend": {
        "titel": "Backend",
        "wurzel": WURZEL / "kompagnon" / "backend",
        "endungen": (".py",),
        # `main` ist der Einstieg; `database`, `config` und `conftest` werden
        # ueber Namen geholt, die der Ausdruck oben nicht sicher trifft.
        # `__init__` ist Paketmechanik und nie ein eigener Import.
        "einstiege": {"main", "conftest", "__init__", "migrate", "migrations"},
        # **Von Hand gestartete Einstiege, keine Leichen.** Alles unter
        # `tools/` und `scripts/` traegt eine Shebang-Zeile und eine
        # Aufrufzeile im Kopf; niemand importiert sie, und das ist ihr Zweck.
        # Ohne diese Ausnahme meldete das Werkzeug sechs davon als tot — es
        # haette gestimmt und trotzdem in die Irre gefuehrt.
        "einstiegs_ordner": ("tools", "scripts"),
        "sprache": "python",
        "ist_test": backend_ist_test,
    },
}


def _dateien(bereich: dict) -> list:
    wurzel = bereich["wurzel"]
    return sorted(
        p for p in wurzel.rglob("*")
        if p.suffix in bereich["endungen"]
        and not any(teil in UEBERSPRINGEN for teil in p.parts)
    )


def frontend_erreicht_von(pfad, inhalte: dict, quellen: list) -> bool:
    """Erreicht eine der Quelldateien diese Datei? — über den Dateinamen."""
    return any(
        frontend_importiert(pfad.stem, inhalte[q]) for q in quellen if q != pfad
    )


def backend_erreicht_von(pfad, inhalte: dict, quellen: list, wurzel) -> bool:
    """Erreicht eine der Quelldateien dieses Modul? — über den Modulpfad."""
    mein_pfad = backend_modulpfad(pfad, wurzel)
    mein_name = mein_pfad[-1] if mein_pfad else ""
    for quelle in quellen:
        if quelle == pfad:
            continue
        text = inhalte[quelle]
        if mein_pfad in backend_ziele(quelle, wurzel, text):
            return True
        if mein_name in backend_dynamische_namen(text):
            return True
    return False


def _pruefe(bereich: dict) -> tuple:
    """(unerreichbar, nur_tests, geprueft) für einen Bereich."""
    wurzel = bereich["wurzel"]
    inhalte = {
        p: p.read_text(encoding="utf-8", errors="ignore")
        for p in _dateien(bereich)
    }
    ist_test = bereich["ist_test"]
    anwendung = [p for p in inhalte if not ist_test(p)]
    tests = [p for p in inhalte if ist_test(p)]

    def erreicht(pfad, quellen: list) -> bool:
        if bereich["sprache"] == "python":
            return backend_erreicht_von(pfad, inhalte, quellen, wurzel)
        return frontend_erreicht_von(pfad, inhalte, quellen)

    def ist_einstieg(pfad) -> bool:
        return (pfad.stem in bereich["einstiege"]
                or any(o in pfad.parts for o in bereich["einstiegs_ordner"]))

    def graph() -> dict:
        """Einmal `Quelle → Ziele`, statt bei jedem Sprung alles zu vergleichen.

        Der erste Anlauf am 07.09.2026 verglich in jedem Schritt jede Datei
        mit jeder — bei 359 Frontend- und 608 Backend-Dateien lief er nach
        zwei Minuten noch. Ein Werkzeug, das niemand abwartet, wird nicht
        benutzt.
        """
        kanten = {p: set() for p in inhalte}
        if bereich["sprache"] == "python":
            nach_modulpfad, nach_name = {}, {}
            for ziel in inhalte:
                mp = backend_modulpfad(ziel, wurzel)
                nach_modulpfad[mp] = ziel
                if mp:
                    nach_name.setdefault(mp[-1], []).append(ziel)
            for quelle, text in inhalte.items():
                for mp in backend_ziele(quelle, wurzel, text):
                    if mp in nach_modulpfad:
                        kanten[quelle].add(nach_modulpfad[mp])
                for name in backend_dynamische_namen(text):
                    kanten[quelle].update(nach_name.get(name, ()))
        else:
            nach_stamm = {}
            for ziel in inhalte:
                nach_stamm.setdefault(ziel.stem, []).append(ziel)
            for quelle, text in inhalte.items():
                for stamm in frontend_zielstaemme(text):
                    kanten[quelle].update(nach_stamm.get(stamm, ()))
        for quelle in kanten:
            kanten[quelle].discard(quelle)
        return kanten

    kanten = graph()

    def erreichbar_ab(start: list) -> set:
        """Alles, was von `start` aus ueber Importe zu erreichen ist.

        **Am 07.09.2026 von einem Sprung auf die ganze Kette umgestellt
        (L-95).** Vorher fragte die Messung, ob **irgendeine** Anwendungsdatei
        die gepruefte importiert. Dass die importierende Datei selbst niemanden
        hat, der sie ruft, blieb ungeprueft — eine Kette unerreichbarer
        Dateien deckte sich damit gegenseitig zu, und je laenger sie war,
        desto weniger fiel auf.

        Gemessen hat es der Vorlagenstrang: `allTemplates.js` (3 Zeilen)
        importiert `templates.js` (146) und `templates_zusatz.js` (**3.121**),
        und `allTemplates.js` importiert **niemand**. Gemeldet wurden drei
        Zeilen statt 3.270 — und `templates_zusatz.js` ist zugleich die
        groesste Datei im Frontend und steht in L-25 ueber der
        800-Zeilen-Grenze. Ohne diese Umstellung waere sie aufgeteilt worden
        statt entschieden.
        """
        gefunden, offen = set(start), list(start)
        while offen:
            for ziel in kanten.get(offen.pop(), ()):
                if ziel not in gefunden:
                    gefunden.add(ziel)
                    offen.append(ziel)
        return gefunden

    einstiege = [p for p in anwendung if ist_einstieg(p)]
    von_der_anwendung = erreichbar_ab(einstiege)
    # Tests sind selbst Einstiegspunkte — sie werden ausgefuehrt, nicht
    # importiert. Was sie erreichen, ist Pruefwerkzeug und kein toter Code.
    von_tests = erreichbar_ab(tests)

    nur_tests, unerreichbar = [], []
    for pfad, text in inhalte.items():
        if ist_einstieg(pfad) or ist_test(pfad):
            continue
        if pfad in von_der_anwendung:
            continue
        eintrag = (len(text.splitlines()), pfad)
        ziel = nur_tests if pfad in von_tests else unerreichbar
        ziel.append(eintrag)

    nur_tests.sort(reverse=True)
    unerreichbar.sort(reverse=True)
    return unerreichbar, nur_tests, len(inhalte)


def _zeige(titel: str, liste: list, hinweis: str, wurzel: pathlib.Path) -> None:
    if not liste:
        print(f"\n  {titel}: keine")
        return
    summe = sum(z for z, _ in liste)
    print(f"\n  {titel} — {len(liste)} Dateien, {summe} Zeilen")
    print(f"    {hinweis}")
    for zeilen, pfad in liste:
        print(f"      {zeilen:>5}  {pfad.relative_to(wurzel.parent)}")


def main(argv: list) -> int:
    gewuenscht = [a for a in argv[1:] if not a.startswith("-")]
    namen = gewuenscht or list(BEREICHE)

    unbekannt = [n for n in namen if n not in BEREICHE]
    if unbekannt:
        print(f"Unbekannter Bereich: {unbekannt} — bekannt: {list(BEREICHE)}",
              file=sys.stderr)
        return 2

    gesamt = 0
    for name in namen:
        bereich = BEREICHE[name]
        wurzel = bereich["wurzel"]
        if not wurzel.is_dir():
            print(f"Nicht gefunden: {wurzel}", file=sys.stderr)
            return 2

        unerreichbar, nur_tests, geprueft = _pruefe(bereich)
        print(f"\n{bereich['titel']} — {geprueft} Dateien unter {wurzel}")
        _zeige("Von der Anwendung nicht erreicht", unerreichbar,
               "Kein Import ausserhalb der Datei selbst — auch nicht aus Tests.",
               wurzel)
        _zeige("Nur von Tests importiert", nur_tests,
               "Gruene Tests fuer Code, den die Anwendung nie ausfuehrt — "
               "ODER ein Pruefhelfer, der genau dorthin gehoert.\n    "
               "Am 24.08.2026 war beides in dieser Liste: `tokenwerte.js` und "
               "`kontrast.js` messen\n    die Design-Tokens fuer fuenf "
               "Testdateien. Sie sind kein toter Code, sondern Werkzeug.",
               wurzel)
        gesamt += sum(z for z, _ in unerreichbar + nur_tests)

    print(f"\nSumme ueber alle geprueften Bereiche: {gesamt} Zeilen, "
          "die kein Nutzerweg erreicht.")
    print("Loeschen ist eine Entscheidung, kein Aufraeumen — manches ist "
          "absichtlich geparkt. Dieses Werkzeug nennt nur den Bestand.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
