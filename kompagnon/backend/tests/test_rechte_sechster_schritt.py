"""Die vier Rechte, die **nicht** durchgesetzt werden — und warum (L-05).

Vierzehn von achtzehn Rechten sperren wirklich (Stand 22.08.2026, fuenfter
Schritt). Die uebrigen vier standen seither als „noch offen" in der Liste,
als waeren sie liegengebliebene Arbeit. Sie sind es nicht — jedes einzelne
haengt an einer Stelle, an der ein Rechtezwang etwas kaputt machen wuerde
oder ins Leere ginge. Am 22.08. nachgeprueft:

| Recht | Wo es haengt | Warum kein Zwang |
|---|---|---|
| `create_audits` | `POST /api/audit/start` | **Absichtlich ohne Anmeldung** — der Weg des eingebetteten Widgets auf fremden Seiten. Ein Zwang haette das Geschaeftsmodell gesperrt, nicht einen Nutzer. |
| `view_audits` | `GET /api/audit/{id}` | Prueft je Aufruf selbst (`_audit_oder_404` mit Token **oder** Anmeldung) — der Kunde erreicht seinen Bericht ueber einen Einmal-Token, den keine Rolle kennt. |
| `download_pdf` | `GET /api/audit/{id}/pdf` | Traegt `require_innendienst` und ist damit **enger** als die Matrix, die es auch Nutzer und Kunde gibt. Der Widerspruch gehoert in die Matrix, nicht in einen zusaetzlichen Zwang. |
| `view_dashboard` | — | Es gibt **keine** Route. Das Dashboard ist Frontend; hier gibt es nichts durchzusetzen. |

**Warum das ein Ergebnis ist und kein Ausweichen.** Ein Recht, das nicht
sperren kann, gehoert benannt — sonst steht es auf ewig als offener Punkt
und suggeriert eine Luecke, die es nicht gibt. Und der Fall `download_pdf`
ist der wichtige: Dort geht Matrix und Wirklichkeit auseinander, und die
Route ist **strenger**. Wer das ohne Hinschauen „durchsetzt", weicht die
Route auf und gibt dem Kunden ein Recht, das er heute nicht hat.
"""
import pytest


NICHT_DURCHGESETZT = {"create_audits", "view_audits", "download_pdf", "view_dashboard"}


class TestDieVierSindBenannt:
    def test_genau_diese_vier_sind_ohne_wirkung(self):
        """Kommt ein fuenftes dazu, ist es unbemerkt eingeschlichen."""
        from routers.admin_settings import DEFAULT_PERMISSIONS
        from services.rechte import DURCHGESETZTE_RECHTE

        alle = {r for rechte in DEFAULT_PERMISSIONS.values() for r in rechte}

        assert alle - set(DURCHGESETZTE_RECHTE) == NICHT_DURCHGESETZT

    def test_vierzehn_von_achtzehn(self):
        from routers.admin_settings import DEFAULT_PERMISSIONS
        from services.rechte import DURCHGESETZTE_RECHTE

        alle = {r for rechte in DEFAULT_PERMISSIONS.values() for r in rechte}
        assert (len(DURCHGESETZTE_RECHTE), len(alle)) == (14, 18)


class TestDerWidgetWegBleibtOffen:
    def test_eine_analyse_startet_ohne_anmeldung(self, client, monkeypatch):
        """**Die Begruendung fuer `create_audits`.** Wer hier eine Sperre
        einzieht, sperrt das eingebettete Widget aus — und damit den Weg, auf
        dem Interessenten hereinkommen."""
        from services import ratenbegrenzung

        monkeypatch.setattr(ratenbegrenzung, "pruefe_audit_grenzen",
                            lambda *a, **k: None)

        antwort = client.post("/api/audit/start",
                              json={"website_url": "https://l05.example"})

        assert antwort.status_code != 403, (
            "Der oeffentliche Analyse-Weg ist gesperrt — das Widget auf "
            "fremden Seiten kommt damit nicht mehr durch")


class TestDasPdfBleibtEng:
    def test_der_kunde_laedt_kein_audit_pdf(self, client, kunde_headers):
        """**Die Route ist strenger als die Matrix.** Sie bleibt es: Ein
        „Durchsetzen" nach Matrix waere hier eine Aufweichung."""
        antwort = client.get("/api/audit/1/pdf", headers=kunde_headers)

        assert antwort.status_code == 403

    def test_und_die_matrix_sagt_etwas_anderes(self):
        """Der Widerspruch wird festgehalten, nicht stillschweigend auf einer
        Seite aufgeloest — das ist Davids Entscheidung."""
        from routers.admin_settings import DEFAULT_PERMISSIONS

        assert "download_pdf" in DEFAULT_PERMISSIONS["kunde"], (
            "Wenn die Matrix hier geaendert wurde, ist der Widerspruch "
            "aufgeloest — dann gehoert dieser Test angepasst")
