"""
Legt die beiden Brevo-Listen für das Widget an und nennt ihre IDs.

Einmal ausführen, dann die beiden IDs in Render als Umgebungsvariablen
eintragen:

    cd kompagnon/backend
    BREVO_API_KEY=... venv/bin/python -m scripts.brevo_widget_listen

Die Trennung ist keine Ordnungsliebe: In *Adresse bestätigt* steht, wem die
Adresse gehört. Erst in *Marketing-Opt-in* steht, wer angeschrieben werden
möchte. Eine Automatisierung gehört ausschließlich an die zweite Liste —
sonst mailt sie Leute an, die nie eingewilligt haben.

Das Skript ist gefahrlos wiederholbar in dem Sinn, dass es nichts löscht.
Brevo legt allerdings bei jedem Lauf neue Listen an, wenn der Name schon
existiert — also nur einmal laufen lassen und die IDs notieren.
"""
import sys

LISTEN = [
    ("KOMPAGNON Widget — Adresse bestätigt", "BREVO_LIST_VERIFIED_ID",
     "Überblick über die Interessenten. KEINE Automatisierung darauf!"),
    ("KOMPAGNON Widget — Marketing-Opt-in", "BREVO_LIST_OPTIN_ID",
     "Nur wer eingewilligt hat. Hier darf die Automatisierung hängen."),
]


def main() -> int:
    from services.brevo_service import BrevoError, BrevoService
    from services.widget_crm import MERKMALE

    try:
        with BrevoService() as brevo:
            print("Merkmale anlegen (vorhandene werden übersprungen):")
            for name, typ in MERKMALE:
                brevo.ensure_attribute(name, typ)
                print(f"  · {name} ({typ})")

            print("\nListen anlegen:\n")
            for name, variable, hinweis in LISTEN:
                listen_id = brevo.create_list(name)
                print(f"  {name}")
                print(f"    {hinweis}")
                print(f"    → {variable}={listen_id}\n")

        print("Beide Werte in Render eintragen (Backend → Environment) und "
              "den Dienst neu starten.")
        return 0
    except BrevoError as e:
        print(f"Fehlgeschlagen: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
