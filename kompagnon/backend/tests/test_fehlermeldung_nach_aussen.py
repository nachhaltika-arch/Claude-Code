# -*- coding: utf-8 -*-
"""Was eine Fehlerantwort dem Browser verraet (L-175).

**Wie dieser Test entstanden ist.** Der Systemdurchlauf vom 06.09.2026 meldete
vier Endpunkte, die „im Fehlerfall mit Erfolg antworten". Am Gegenstand
nachgesehen stimmte das **nicht**: `audit_anfrage`, `send_email_endpoint` und
`request_approval` geben `success: False` bzw. eine Fehlermeldung zurueck, und
die Oberflaeche wertet sie aus — `KampagneLandingPage` zeigt genau diesen Text
an. Nur der HTTP-Status ist 200, und bei einem Aufruf des **eigenen**
Frontends ist das vertretbar.

**Der echte Befund lag daneben und war nicht gemeldet:** Alle drei reichen
`str(e)` **roh** an den Browser durch. Eine Ausnahme aus SQLAlchemy nennt
Tabellen- und Spaltennamen, ein Verbindungsfehler die Adresse des
Datenbankservers. Das ist ein Informationsleck an einer Stelle, die
**ohne Anmeldung** erreichbar ist (die Kampagnen-Landingpage).

**Und `forgot_password` ist Absicht, kein Fehler.** Die Antwort lautet immer
„Falls die E-Mail existiert, wurde ein Reset-Link gesendet" — genau damit
niemand durch Ausprobieren erfaehrt, welche Adressen ein Konto haben. Eine
ehrlichere Antwort waere hier die schlechtere.
"""
import ast
from pathlib import Path

import pytest

ROUTER = Path(__file__).resolve().parent.parent / "routers"

#: Die Stellen aus dem Befund, jeweils Datei und Funktion.
GEPRUEFT = [
    ("kampagne.py", "audit_anfrage"),
    ("messages.py", "send_email_endpoint"),
    ("projects.py", "request_approval"),
]


def _rohe_ausnahme_in_antwort(datei: str, funktion: str):
    """Gibt ein `return` im Abfangzweig die gefangene Ausnahme heraus?

    Gesucht wird der **Wortlaut** der Ausnahme, nicht ihre Art.

    **Die Unterscheidung ist der Punkt, und mein erster Wurf hatte sie
    nicht.** `str(e)` nennt Tabellen- und Spaltennamen oder die Adresse des
    Datenbankservers — das ist das Leck. `type(e).__name__` ist bloss
    „OperationalError": Es hilft dem Innendienst beim Einordnen und verraet
    nichts ueber den Aufbau. Ein Test, der beides verbietet, zwingt zu einer
    Absage, aus der niemand etwas machen kann.
    """
    baum = ast.parse((ROUTER / datei).read_text(encoding="utf-8"))
    treffer = []
    for knoten in ast.walk(baum):
        if not isinstance(knoten, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if knoten.name != funktion:
            continue
        for zweig in [k for k in ast.walk(knoten) if isinstance(k, ast.ExceptHandler)]:
            if not zweig.name:
                continue
            for r in [k for k in ast.walk(zweig) if isinstance(k, ast.Return)]:
                if _wortlaut_geht_hinaus(r, zweig.name):
                    treffer.append(f"{datei}:{r.lineno} {ast.unparse(r)[:70]}")
    return treffer


class _OhneArt(ast.NodeTransformer):
    """Schneidet `type(<name>).__name__` aus dem Baum.

    **Warum als Transformator und nicht als Textzaehlung.** Mein erster Wurf
    verglich `roh.count(name)` mit `roh.count(f"type({name}).__name__")` — und
    wurde rot, weil der Ausnahmename `e` auch in „Versand fehlgeschlagen"
    steckt. Ein Buchstabe als Teilzeichenkette gezaehlt: dieselbe Klasse
    Messfehler, die hier schon oefter Zahlen verdorben hat. Der Baum kennt
    keine Teilzeichenketten.
    """

    def __init__(self, name):
        self.name = name

    def visit_Attribute(self, knoten):  # noqa: N802 — von ast vorgegeben
        ist_art = (
            knoten.attr == "__name__"
            and isinstance(knoten.value, ast.Call)
            and isinstance(knoten.value.func, ast.Name)
            and knoten.value.func.id == "type"
            and any(isinstance(a, ast.Name) and a.id == self.name
                    for a in knoten.value.args)
        )
        return ast.Constant(value="<art>") if ist_art else self.generic_visit(knoten)


def _wortlaut_geht_hinaus(rueckgabe, name: str) -> bool:
    """Steht der **Wortlaut** der Ausnahme in der Antwort — nicht nur ihre Art?"""
    ohne_art = _OhneArt(name).visit(ast.parse(ast.unparse(rueckgabe)))
    return any(isinstance(k, ast.Name) and k.id == name
               for k in ast.walk(ohne_art))


@pytest.mark.parametrize("datei,funktion", GEPRUEFT)
def test_keine_rohe_ausnahme_geht_an_den_browser(datei, funktion):
    """**Der Kern.** Was der Nutzer liest, darf sagen *dass* es schiefging —
    nicht *woran es im Inneren lag*."""
    assert not _rohe_ausnahme_in_antwort(datei, funktion), (
        f"{funktion} reicht die gefangene Ausnahme an den Aufrufer durch: "
        f"{_rohe_ausnahme_in_antwort(datei, funktion)}")


def test_die_landingpage_bekommt_weiter_eine_lesbare_absage(client, monkeypatch):
    """**Die Gegenprobe.** Eine Antwort ohne jede Auskunft waere die andere
    Sorte Fehler: Die Oberflaeche wertet `success` aus und zeigt `error` an —
    steht dort nichts, sieht der Interessent einen leeren Kasten."""
    import routers.kampagne as k

    def kracht(*a, **kw):
        raise RuntimeError("relation \"leads\" does not exist")

    # Der Aufbau des Leads laeuft ueber die Sitzung — sie krachen zu lassen
    # trifft jeden Weg durch den Abfangzweig.
    monkeypatch.setattr(k, "SessionLocal", kracht, raising=False)

    antwort = client.post("/api/kampagne/audit-anfrage", json={
        "domain": "example.org", "email": "wer@example.org", "mobil": "0170 1234567"})

    assert antwort.status_code == 200
    d = antwort.json()
    if d.get("success") is False:
        assert d.get("error"), "eine Absage ohne Text ist ein leerer Kasten"
        assert "relation" not in d["error"], "der Datenbankfehler gehoert nicht nach aussen"


def test_die_neutrale_antwort_beim_passwort_bleibt_neutral():
    """**Kein blindes Reparieren.** Der Durchlauf zaehlte `forgot_password` zu
    derselben Familie. Die immergleiche Antwort ist dort aber der **Schutz**:
    Wer durch Ausprobieren erfaehrt, welche Adressen ein Konto haben, hat die
    halbe Anmeldung. Dieser Test haelt fest, dass niemand sie „ehrlicher"
    macht."""
    quelle = (ROUTER / "auth_router.py").read_text(encoding="utf-8")
    baum = ast.parse(quelle)

    fn = next(k for k in ast.walk(baum)
              if isinstance(k, (ast.FunctionDef, ast.AsyncFunctionDef))
              and k.name == "forgot_password")
    rueckgaben = [ast.unparse(r.value) for r in ast.walk(fn)
                  if isinstance(r, ast.Return) and r.value is not None]

    assert len(rueckgaben) == 1, (
        "Mehr als eine Antwort heisst: Der Aufrufer kann unterscheiden, ob es "
        f"das Konto gibt. {rueckgaben}")
    assert "Falls die E-Mail existiert" in rueckgaben[0]
