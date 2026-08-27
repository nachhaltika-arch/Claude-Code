# -*- coding: utf-8 -*-
"""Welche Rollen es gibt — an einer Stelle beantwortet.

**Der Anlass (27.08.2026, Entscheidung David).** Es gab vier Rollen neben dem
Superadmin: `admin`, `auditor`, `nutzer`, `kunde`. Zwei davon meinten
dasselbe und taten es verschieden:

- `auditor` war die **arbeitende** Innendienstrolle. Rund zwanzig
  Oberflächenwege hingen an `roles={['admin','auditor']}`, und die
  Rechtematrix gab ihr Betriebe, Projekte und Audits.
- `nutzer` war die Vorgaberolle jedes neuen Kontos und durfte fast nichts:
  Dashboard, Audits, PDF. Wer so angelegt wurde, kam an keinen Betrieb.

Beide sind jetzt **eine** Rolle: `mitarbeiter` — Mitarbeiter KOMPAGNON. Sie
erbt die Rechte des Auditors, weil das die Rechte sind, mit denen im Werkzeug
tatsächlich gearbeitet wurde. Damit nimmt die Zusammenlegung niemandem etwas
weg; sie gibt der Rolle `nutzer` dazu, was sie ohnehin hätte haben müssen.

**Warum dieses Modul und nicht wieder eine Aufzählung je Datei.** Die
Rollennamen standen an über siebzig Stellen in Backend und Oberfläche. Beim
letzten Mal (L-05, 18.08.) war genau das der Fehler: Die Sperre zählte auf,
*wer nicht darf*, und liess `nutzer` durch — an einer Stelle korrigiert, an
den anderen nicht. Wer eine Rolle ändert, ändert sie hier; alles andere liest
von hier.

**Die alten Namen bleiben hier stehen**, und zwar mit Absicht:
`migrations_runtime` schreibt bestehende Konten damit um, und der
Posteingang, die Rechtetabelle und die Testdaten dürfen sie kennen. Ein
Bestand, der einen Namen nicht mehr kennt, den er selbst gespeichert hat,
sperrt Menschen aus.
"""

#: Jede Rolle, die es gibt. Die Reihenfolge ist die Rangfolge — von innen
#: nach aussen.
ROLLEN = ("superadmin", "admin", "mitarbeiter", "kunde")

#: Wer zum Innendienst gehört, **wenn niemand etwas anderes eingestellt hat**.
#: Für die eigentliche Frage siehe `routers.auth_router.require_innendienst`:
#: Die liest die Rechteverwaltung, statt Rollen aufzuzählen.
INNENDIENST = ("superadmin", "admin", "mitarbeiter")

#: Admin und Superadmin bleiben drin, was auch immer jemand anhakt. Die
#: Oberfläche lässt beide Rollen nicht bearbeiten; hier steht derselbe Boden
#: noch einmal, weil eine Oberflächenprüfung keine Sperre ist.
IMMER_INNENDIENST = ("superadmin", "admin")

#: Rollen, deren Haken sich in der Rechteverwaltung setzen lassen.
#: `superadmin` und `admin` sind bewusst nicht dabei — wer sie bearbeiten
#: dürfte, könnte sich selbst aussperren oder alles geben.
BEARBEITBAR = ("mitarbeiter", "kunde")

#: Rollen, die eine Unterschrift und eine Position im Audit-Bericht führen
#: dürfen. Das ist eine **Produkt**eigenschaft des Berichts, keine
#: Rechtefrage: Im PDF steht, wer geprüft hat.
MIT_UNTERSCHRIFT = ("superadmin", "admin", "mitarbeiter")

#: Was aus den Namen von gestern wird. Gelesen von `migrations_runtime`
#: (Bestand) und von `rolle_normalisieren` (alles, was von aussen kommt).
ALTE_ROLLEN = {
    "auditor": "mitarbeiter",
    "nutzer": "mitarbeiter",
}

#: Die Rolle eines Kontos, das **der Innendienst** ohne Angabe anlegt.
#: Gilt für `POST /api/admin/users` — dort sitzt jemand, der schon
#: angemeldet ist und `manage_users` hat.
VORGABE = "mitarbeiter"

#: Die Rolle eines Kontos, das sich **selbst** anlegt (`POST
#: /api/auth/register`, öffentlich erreichbar über `/register`).
#:
#: **Warum das nicht `VORGABE` sein darf (gefunden am 27.08.2026 beim
#: Zusammenlegen der Rollen).** Bis heute vergab die Selbstregistrierung
#: `nutzer` — eine Rolle mit Dashboard, Audits und PDF. Mit der
#: Zusammenlegung wäre daraus `mitarbeiter` geworden, und damit hätte sich
#: **jeder Fremde über das öffentliche Formular ein Innendienstkonto
#: anlegen können**: `GET /api/leads/` gibt dieser Rolle den gesamten
#: Betriebsbestand.
#:
#: Der Fehler wäre nicht die Zusammenlegung gewesen, sondern die stille
#: Kopplung: Wer die Vorgaberolle hebt, hebt ungewollt auch das, was ein
#: Unbekannter bekommt. Deshalb stehen die beiden hier getrennt, jede mit
#: ihrem eigenen Grund — und `tests/test_rolle_mitarbeiter.py` hält fest,
#: dass diese hier **nie** zum Innendienst gehört.
SELBSTREGISTRIERUNG = "kunde"


def rolle_normalisieren(rolle: str | None) -> str | None:
    """Einen Rollennamen auf den heutigen Stand bringen.

    Gibt `None` zurück, wenn der Name zu keiner bekannten Rolle gehört — der
    Aufrufer entscheidet dann, ob er ablehnt oder die Vorgabe nimmt. Ein
    stilles Zurückfallen auf `VORGABE` wäre hier falsch: Ein Tippfehler in
    `role` würde sonst ein Innendienstkonto anlegen.
    """
    if not rolle:
        return None
    schlank = rolle.strip().lower()
    schlank = ALTE_ROLLEN.get(schlank, schlank)
    return schlank if schlank in ROLLEN else None


def ist_innendienst(rolle: str | None) -> bool:
    """Gehört diese Rolle zum Innendienst? Alte Namen zählen mit."""
    return rolle_normalisieren(rolle) in INNENDIENST
