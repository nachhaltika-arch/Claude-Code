"""Was eine Rolle darf — an einer Stelle beantwortet.

**Warum es das gibt (Luecke L-05).** Es gab die Tabelle `role_permissions`,
einen Bildschirm, der sie bearbeitet, und einen Endpunkt, der sie speichert.
Gelesen hat sie zur Rechtevergabe **niemand**: Die Sperren im Programm zaehlten
Rollen von Hand auf. Ein Haken liess sich setzen und wegnehmen, und es
passierte nichts — eine Zusicherung, die nicht gilt.

Drei Regeln:

1. **Die Vorgabe steht in `admin_settings.DEFAULT_PERMISSIONS`**, gespeicherte
   Eintraege stechen sie. So bleibt ein frisches System benutzbar, ohne dass
   jemand erst Haken setzen muss.
2. **Superadmin darf immer.** Sonst sperrt ein Haken den letzten aus, der ihn
   wieder wegnehmen koennte. Die Oberflaeche verweigert das Bearbeiten von
   `superadmin` und `admin` ohnehin; hier steht derselbe Boden noch einmal,
   weil eine Oberflaechenpruefung keine Sperre ist.
3. **Nur was in `DURCHGESETZTE_RECHTE` steht, wirkt wirklich.** Alles andere
   ist bisher Beschreibung. Der Bildschirm erfaehrt das ueber
   `GET /api/admin/roles` und kann es kennzeichnen — ein Haken, der nichts
   tut, soll nicht so aussehen wie einer, der etwas tut.
"""
import logging

logger = logging.getLogger(__name__)

#: Rechte, an denen tatsaechlich eine Sperre haengt. Wer eines dazunimmt,
#: haengt es an eine Route **und** traegt es hier ein — sonst luegt der
#: Bildschirm wieder.
DURCHGESETZTE_RECHTE = frozenset({
    "view_leads",       # Betriebe, Kundenkartei, Projekte (require_innendienst)
    "view_projects",
    # Ab 19.08.2026 — die drei, mit denen etwas Unwiderrufliches passiert:
    "delete_leads",             # DELETE /api/leads/{id}
    "manage_users",             # Konten anlegen, aendern, loeschen, Passwort
    "manage_settings",          # PATCH /api/admin/settings
    # Ab 21.08.2026 — drei, deren heutige Sperre der Vorgabe **genau**
    # entspricht. Das Durchsetzen ist dort additiv: Es nimmt niemandem etwas
    # weg, es macht den Haken wirksam.
    "create_leads",             # POST /api/leads/       (require_innendienst)
    "edit_leads",               # PATCH /api/leads/{id}  (require_innendienst)
    "view_users",               # GET /api/admin/users   (require_admin)
    #
    # **Nicht** dazugenommen, weil es eine Verhaltensaenderung waere:
    # `manage_projects` hat laut Vorgabe nur superadmin und admin, die
    # Projektrouten stehen aber auf `require_innendienst` — es naehme dem
    # Auditor etwas weg. `download_pdf`, `view_audits` und `view_dashboard`
    # haben laut Vorgabe **alle** Rollen; sie haengen an Routen, die teils
    # oeffentlich sind (Widget, Kundenportal), und das gehoert eigens
    # gemessen, nicht nebenbei verdrahtet.
    #
    # **Nicht** durchgesetzt, und zwar aus demselben Grund:
    # `deploy_kas_pages` und `manage_system_settings` hat per Vorgabe **nur**
    # der Superadmin. Sie durchzusetzen waere keine Absicherung, sondern eine
    # Verhaltensaenderung — sie naehme dem Admin etwas weg, das er heute tut
    # (deployen, die Rechtematrix pflegen). Das gehoert entschieden, nicht
    # nebenbei gemacht.
})


def _vorgabe(rolle: str, recht: str) -> bool:
    from routers.admin_settings import DEFAULT_PERMISSIONS

    return recht in DEFAULT_PERMISSIONS.get(rolle, [])


def hat_recht(rolle: str, recht: str, db=None) -> bool:
    """Darf diese Rolle das? Gespeichertes sticht die Vorgabe."""
    if rolle == "superadmin":
        return True

    from routers.admin_settings import PERM_LABELS

    if recht not in PERM_LABELS:
        return False

    eigene_sitzung = db is None
    if eigene_sitzung:
        from database import SessionLocal
        db = SessionLocal()

    try:
        from database import RolePermission

        eintrag = (db.query(RolePermission)
                     .filter(RolePermission.role == rolle,
                             RolePermission.permission == recht)
                     .first())
        if eintrag is not None:
            return bool(eintrag.is_allowed)
        return _vorgabe(rolle, recht)
    except Exception as fehler:
        # Ist die Tabelle nicht lesbar, gilt die Vorgabe — eine Anwendung, die
        # bei einem Datenbankschluckauf alle aussperrt, waere schlimmer.
        logger.warning("Rechte nicht lesbar (%s) — Vorgabe gilt", fehler)
        return _vorgabe(rolle, recht)
    finally:
        if eigene_sitzung:
            try:
                db.close()
            except Exception:
                pass
