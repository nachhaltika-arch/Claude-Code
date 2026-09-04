# -*- coding: utf-8 -*-
"""Die Blueprints laufen nicht auseinander, ohne dass es auffaellt (L-35).

**Die Entscheidung dahinter (David, 27.08.2026): Produktiv bleibt bewusst
nicht blueprint-verwaltet.** Einen Blueprint auf laufende Dienste anzuwenden
uebernimmt sie entweder oder legt sie neu an; bei einem Dienst mit
Datentraeger (L-94) und angehaengter Datenbank ist das ein echtes
Ausfallrisiko fuer einen Nutzen, den ein Ein-Personen-Betrieb nie einloest.

**Damit ist die Aufgabe eine andere:** Die Dateien beschreiben, sie steuern
nicht — also muss auffallen, **wenn die Beschreibung nicht mehr stimmt**.
Genau danach wurde in diesem Monat dreimal von Hand gesucht (16.08., 24.08.,
27.08.), und jedes Mal fand sich etwas.

**Was dieser Waechter kann und was nicht.** Er vergleicht die Dateien
untereinander und gegen `.env.example` — das laeuft ohne Zugangsdaten bei
jedem Lauf. Ob die Dateien zu den **laufenden Diensten** passen, kann er
nicht sagen; dafuer gibt es `tools/blueprint_abgleich.py`, das einen
Render-Schluessel braucht. Ein Waechter, der so tut, als pruefe er die
Wirklichkeit, waere schlimmer als keiner.

**Warum eine eingefrorene Differenz und keine Gleichheit.** Die Dateien
*duerfen* sich unterscheiden — Staging spricht SMTP, Produktiv Brevo. Ein
Test auf Gleichheit waere sofort rot und am naechsten Tag abgeschaltet.
Festgehalten wird deshalb die **bekannte** Differenz, mit Begruendung je
Eintrag. Wer eine Variable in eine Datei schreibt und in der anderen
vergisst, aendert die Differenz — und wird rot.
"""
import re
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parent.parent.parent      # kompagnon/
STAGING = WURZEL / "render-staging.yaml"
PRODUKTIV = WURZEL / "render-produktiv.yaml"
BEISPIEL = WURZEL / "backend" / ".env.example"


def schluessel(datei: Path) -> set:
    """Alle `- key: NAME` einer Blueprint-Datei.

    **Bewusst zeilenweise statt mit einem YAML-Leser.** `pyyaml` steht nicht
    in `requirements.txt`; eine Abhaengigkeit fuer einen Test aufzunehmen
    waere der teurere Weg, und dieselbe Entscheidung ist im Bestand schon
    einmal so gefallen (`tests/pdf_inhalt.py`). Die Form `- key: NAME` ist
    in allen drei Dateien einheitlich — nachgezaehlt, nicht angenommen.
    """
    return set(re.findall(r"^\s*- key:\s*([A-Za-z_][A-Za-z0-9_]*)",
                          datei.read_text(encoding="utf-8"), re.M))


def beispiel_schluessel() -> set:
    return set(re.findall(r"^([A-Z][A-Z0-9_]*)=",
                          BEISPIEL.read_text(encoding="utf-8"), re.M))


# ── Die bekannte Differenz, mit Begruendung je Gruppe ─────────────────
#
# Stand 27.08.2026, ausgezaehlt statt geschaetzt: 25 zu 10.

#: Steht nur im Produktiv-Blueprint.
NUR_PRODUKTIV = {
    # (a) Gehoert eigentlich auch auf Staging — Staging ist sonst keine
    #     getreue Probe der Produktion, und genau das ist sein Zweck.
    #     Offen seit dem 24.08., bewusst nicht auf Verdacht angeglichen.
    "CREDENTIALS_KEY", "CMS_ENCRYPTION_KEY", "BREVO_WEBHOOK_SECRET",
    "NETLIFY_WEBHOOK_SECRET", "TRACKDESK_WEBHOOK_SECRET", "WEBHOOK_SECRET",
    "PUBLIC_BASE_URL", "API_BASE_URL", "GOOGLE_PLACES_API_KEY",
    "NORTHDATA_API_KEY", "PAGESPEED_API_KEY",
    # (b) Modell- und Betriebsschalter, produktiv gesetzt, auf Staging
    #     bisher nicht gebraucht.
    "ASSISTENT_MAX_TOKENS", "ASSISTENT_MODELL", "AUDIT_AI_MODEL",
    "AUDIT_RECOGNITION_MODEL", "HWK_SCRAPER_ENABLED", "DEBUG", "LOG_LEVEL",
    "TRUSTED_PROXY_HEADER",
    # (c) Angaben, die nur auf echten Dokumenten erscheinen (Rechnung,
    #     Impressum). Auf Staging waeren sie irrefuehrend.
    "BANK_BIC", "BANK_IBAN", "BANK_NAME", "COMPANY_ADDRESS",
    "CONTACT_EMAIL", "CONTACT_PHONE",
}

#: Steht nur im Staging-Blueprint.
NUR_STAGING = {
    # (a) Staging verschickt ueber SMTP, Produktiv ueber Brevo. Zu Recht
    #     verschieden.
    "SMTP_HOST", "SMTP_PASSWORD", "SMTP_PORT", "SMTP_SENDER_EMAIL",
    "SMTP_SENDER_NAME", "SMTP_USER", "USE_MOCK_EMAIL",
    # (b) Plattformschalter des Frontend-Dienstes.
    "CI", "NODE_VERSION",
    # (c) **Kein Fehler, auch wenn es wie einer aussieht.** Produktiv heisst
    #     die Variable `PAGESPEED_API_KEY`, hier `GOOGLE_PAGESPEED_API_KEY`.
    #     Der Code liest **beide**, mit dokumentiertem Rueckfall und eigenem
    #     Test (`tests/test_pagespeed_schluessel.py`, 11.08.2026). Wer hier
    #     angleicht, ohne nachzusehen, repariert etwas Funktionierendes.
    "GOOGLE_PAGESPEED_API_KEY",
}

#: Steht in `.env.example`, aber in **keinem** Blueprint.
IN_KEINEM_BLUEPRINT = {
    # (a) Demo-Zugaenge fuer die lokale Entwicklung. **`ADMIN_*` steht
    #     bewusst NICHT hier** — die Admin-Anmeldung gibt es auf beiden
    #     Servern und damit in beiden Blueprints; nur Mitarbeiter- und
    #     Kundenkonto sind rein lokal.
    "MITARBEITER_EMAIL", "MITARBEITER_PASSWORD",
    "KUNDE_EMAIL", "KUNDE_PASSWORD",
    # (b) **Eine echte Luecke, am 27.08. gefunden.** Das KI-Sichtbarkeits-Abo
    #     braucht diese Schluessel; sie werden ueber eine Anbietertabelle
    #     **dynamisch** gelesen, weshalb ein `getenv`-Suchlauf sie uebersieht
    #     und niemand sie vermisst hat.
    "OPENAI_API_KEY", "PERPLEXITY_API_KEY",
    # (c) Hat eine Vorgabe im Code und muss nirgends gesetzt werden.
    "SCHEDULER_TIMEZONE", "SMTP_FROM",
}


# ── Die Gegenprobe zuerst ─────────────────────────────────────────────

def test_die_dateien_sind_lesbar_und_nicht_leer():
    """Ohne diese Zusicherung waeren alle Vergleiche unten auch dann gruen,
    wenn eine Datei umbenannt wuerde — ein Waechter, der nichts liest, sieht
    aus wie einer, der nichts zu beanstanden hat."""
    for datei in (STAGING, PRODUKTIV, BEISPIEL):
        assert datei.exists(), f"{datei.name} fehlt"
    assert len(schluessel(STAGING)) > 25
    assert len(schluessel(PRODUKTIV)) > 40
    assert len(beispiel_schluessel()) > 40


# ── Blueprint gegen Blueprint ─────────────────────────────────────────

def test_nur_die_bekannte_differenz_steht_zwischen_den_blueprints():
    """**Der eigentliche Waechter.** Wer eine Variable in eine Datei
    schreibt und in der anderen vergisst, aendert die Differenz.

    Genau so entstand der Befund vom 24.08. (dem Staging-Blueprint fehlten
    26) und der vom 27.08. (`STRIPE_WEBHOOK_SECRET_BUCH` musste in alle drei
    Dateien von Hand nachgetragen werden).
    """
    st, pr = schluessel(STAGING), schluessel(PRODUKTIV)

    assert pr - st == NUR_PRODUKTIV, (
        "Die Differenz Produktiv→Staging hat sich geaendert.\n"
        f"  neu hinzugekommen: {sorted((pr - st) - NUR_PRODUKTIV)}\n"
        f"  nicht mehr da:     {sorted(NUR_PRODUKTIV - (pr - st))}\n"
        "Entweder die Datei ergaenzen oder die Liste hier — mit Begruendung.")

    assert st - pr == NUR_STAGING, (
        "Die Differenz Staging→Produktiv hat sich geaendert.\n"
        f"  neu hinzugekommen: {sorted((st - pr) - NUR_STAGING)}\n"
        f"  nicht mehr da:     {sorted(NUR_STAGING - (st - pr))}")


def test_die_gemeinsame_menge_ist_die_mehrheit():
    """Gegenprobe zum Test darueber: Waeren die Ausnahmelisten irgendwann so
    gross wie die Dateien, pruefte er nichts mehr."""
    st, pr = schluessel(STAGING), schluessel(PRODUKTIV)

    assert len(st & pr) > len(NUR_STAGING), "Mehr Ausnahme als Regel"


# ── Blueprints gegen die Beispieldatei ────────────────────────────────

def test_keine_variable_faellt_zwischen_beispiel_und_blueprints_durch():
    """`.env.example` ist die Liste dessen, was der Bestand liest. Was darin
    steht und in **keinem** Blueprint, bekommt auf keinem Server einen Wert —
    und faellt erst dem ersten Nutzer auf."""
    fehlend = beispiel_schluessel() - schluessel(STAGING) - schluessel(PRODUKTIV)

    assert fehlend == IN_KEINEM_BLUEPRINT, (
        "Die Menge der nirgends gesetzten Variablen hat sich geaendert.\n"
        f"  neu:           {sorted(fehlend - IN_KEINEM_BLUEPRINT)}\n"
        f"  nicht mehr da: {sorted(IN_KEINEM_BLUEPRINT - fehlend)}")


@pytest.mark.parametrize("name", sorted(IN_KEINEM_BLUEPRINT))
def test_jede_ausnahme_traegt_ihren_grund(name):
    """Eine Ausnahmeliste ohne Begruendungen wird zur Muellhalde: Der
    Naechste haengt seinen Eintrag an und niemand weiss mehr, warum.

    Geprueft wird am Quelltext dieser Datei — die Kommentarbloecke sind
    Teil der Zusicherung, nicht Beiwerk.
    """
    quelle = Path(__file__).read_text(encoding="utf-8")
    block = quelle.split("IN_KEINEM_BLUEPRINT = {")[1].split("}")[0]

    assert name in block
    assert block.count("#") >= 6, "Die Liste hat ihre Begruendungen verloren"


# ── Und das Werkzeug daneben zeigt auf die richtigen Dienste ──────────

def test_das_werkzeug_nennt_die_laufenden_dienste():
    """`tools/blueprint_abgleich.py` vergleicht gegen benannte Dienste.

    **Genau hier lag der Fehler vom 23.08.:** Der Blueprint nannte
    `kompagnon-backend` — und so heisst heute der **stillgelegte**
    Oregon-Dienst (L-34). Wer damit arbeitet, vergleicht gegen eine Leiche
    und haelt das Ergebnis fuer eine Aussage.

    Der API-Teil des Werkzeugs laeuft ohne Render-Schluessel nicht und ist
    deshalb **nicht** durch Tests gedeckt. Diese Zusicherung deckt das, was
    ohne Schluessel pruefbar ist: die Namen und die Dateien.
    """
    quelle = (Path(__file__).resolve().parent.parent
              / "tools" / "blueprint_abgleich.py").read_text(encoding="utf-8")

    assert "kompagnon-backend-fra" in quelle, "der laufende Produktivdienst"
    assert "kompagnon-backend-staging" in quelle
    assert '"kompagnon-backend"' not in quelle, (
        "So heisst der stillgelegte Oregon-Dienst (L-34)")

    for dateiname in ("render-staging.yaml", "render-produktiv.yaml"):
        assert dateiname in quelle
        assert (WURZEL / dateiname).exists()


def test_das_werkzeug_gibt_keine_werte_aus():
    """Ein Werkzeug, das Geheimnisse ausgibt, waere gefaehrlicher als die
    Luecke, die es finden soll — dieselbe Regel wie bei `/health` (L-139).

    Gemessen am Quelltext: Es liest `envVar["key"]`, nie `["value"]`.
    """
    quelle = (Path(__file__).resolve().parent.parent
              / "tools" / "blueprint_abgleich.py").read_text(encoding="utf-8")

    assert '["key"]' in quelle
    assert '["value"]' not in quelle and "'value'" not in quelle
