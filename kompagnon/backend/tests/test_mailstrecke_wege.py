"""Jeder Lead-Weg erreicht die Entscheidung über die Mailstrecke (L-62).

**Vorgänger dieser Datei war `test_mailstrecke_greift_nicht.py`**, und der
hielt den umgekehrten Zustand fest: Die Strecke griff für **keinen** Weg.
Sein Schlusssatz war „Wird er rot, ist das kein Fehler — es ist die Frage, ob
die Entscheidung gefallen ist. Wer ihn anpasst, hat sie getroffen."

**Am 24.08.2026 ist sie gefallen (David):** Die Strecke wird scharf
geschaltet, aber nur für Betriebe, die **ab dem Stichtag** entstehen. Der
Bestand bekommt nichts — die Listen einfach anzugleichen hätte ab dem
nächsten Deploy Post an Altdaten geschickt, darunter Kaltakquise.

**Was dieser Test hält, ist der Weg, nicht die Regel.** Die Regel steht in
`services/lead_quellen.py` und wird von
`tests/test_mailstrecke_stichtag.py` geprüft. Hier geht es um das, was am
21.08. der eigentliche Fund war: dass ein Weg an der Entscheidung **vorbei**
laufen kann, ohne dass es jemandem auffällt. Das Ausbleiben einer Mail
protokolliert nichts.
"""
import pathlib
import re

import pytest

WURZEL = pathlib.Path(__file__).resolve().parent.parent


def _quelle(name: str) -> str:
    return (WURZEL / name).read_text(encoding="utf-8")


#: Die Stelle, an der die Entscheidung fällt — eine einzige.
ENTSCHEIDER = "strecke_anstossen_wenn_erlaubt"

#: Jeder Pfad, auf dem ein Betrieb entsteht und eine Strecke bekommen könnte.
ANLEGENDE_WEGE = (
    ("routers/leads.py", "der Innendienst und die öffentlichen Formulare"),
    ("routers/webhooks.py", "Facebook, LinkedIn, Google, Postkarte, Telefon"),
)


class TestJederWegErreichtDieEntscheidung:
    @pytest.mark.parametrize("datei, wer", ANLEGENDE_WEGE)
    def test_der_weg_ruft_den_entscheider(self, datei, wer):
        assert ENTSCHEIDER in _quelle(datei), (
            f"{datei} legt Betriebe an ({wer}), ruft aber nicht "
            f"`{ENTSCHEIDER}`. Genau so lief `_upsert_lead` bis zum "
            "24.08.2026 an der Entscheidung vorbei — mit rohem SQL, und "
            "niemand hat es gemerkt."
        )

    def test_es_gibt_genau_einen_entscheider(self):
        """Zwei Stellen driften auseinander — das war der ganze Befund."""
        # Arrange & Act
        definitionen = [
            p for p in WURZEL.rglob("*.py")
            if "venv" not in p.parts and "tests" not in p.parts
            and re.search(rf"^def {ENTSCHEIDER}\(", p.read_text(
                encoding="utf-8", errors="ignore"), re.MULTILINE)
        ]

        # Assert
        assert len(definitionen) == 1, [str(p) for p in definitionen]

    def test_niemand_startet_die_strecke_am_entscheider_vorbei(self):
        """`start_sequence_for_lead` direkt zu rufen umgeht Herkunft und Stichtag."""
        # Arrange — erlaubt ist es nur dort, wo ein Mensch es ausloest,
        # und in der Entscheiderfunktion selbst.
        erlaubt = {
            "services/sequence_runner.py",   # die Definition und der Entscheider
            "routers/leads_nachfassen.py",   # Innendienst loest von Hand aus
            # **Der Kaufweg, begruendet ausgenommen.** Der Lead entsteht in
            # `_handle_successful_payment`, also nach abgeschlossener Zahlung:
            # Rechtsgrundlage ist der Vertrag (Art. 6 Abs. 1 lit. b, siehe
            # `lead_quellen.QUELLEN["stripe_checkout"]`), und die Strecke ist
            # dort Begruessung, nicht Akquise.
            #
            # Der Stichtag aus L-62 soll den **Kaltakquise-Bestand** schuetzen.
            # Dieser Pfad laeuft nur bei einer **neuen** Zahlung — es gibt
            # keinen Bestand, den er anschreiben koennte. Ihn durch den
            # Entscheider zu schicken haette einen echten Nachteil: Ein
            # wiederkehrender Kunde mit altem Lead-Datensatz bekaeme nach dem
            # Kauf keine Begruessung mehr.
            "routers/payments.py",
        }

        # Act
        schuldige = []
        for pfad in WURZEL.rglob("*.py"):
            if "venv" in pfad.parts or "tests" in pfad.parts:
                continue
            rel = pfad.relative_to(WURZEL).as_posix()
            if rel in erlaubt:
                continue
            if "start_sequence_for_lead" in pfad.read_text(
                    encoding="utf-8", errors="ignore"):
                schuldige.append(rel)

        # Assert
        assert not schuldige, (
            "Diese Stellen starten die Strecke direkt und umgehen damit "
            f"Herkunft und Stichtag: {schuldige}"
        )
