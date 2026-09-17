# -*- coding: utf-8 -*-
"""Die Abmeldung aus der E-Mail-Strecke — was ein Klick in der Mail erreicht.

Das Verfahren und seine Begruendungen stehen in `services/abmeldung.py`.
Hier steht nur, was der Browser davon sieht.

**Ohne Anmeldung, und das ist Absicht.** Wer sich abmelden will, hat kein
Konto und soll keines brauchen. Der Token in der Adresse ist der Nachweis.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from database import get_db
from services import abmeldung

router = APIRouter(prefix="/api/mail/abmelden", tags=["abmeldung"])

#: Die Marke steht im Kopf der Mails (`services/brand.py`).
_DARK = "#004F59"
_MID = "#008EAA"


def _seite(ueberschrift: str, satz: str, link_text: str = "",
           link_url: str = "") -> HTMLResponse:
    """Eine Seite ohne Anhaengsel — kein Menue, keine Verfolgung, kein Skript.

    Wer hier landet, hat gerade gesagt, dass er nichts mehr will. Eine Seite,
    die ihm bei der Gelegenheit noch ein Angebot macht, ist genau der Grund,
    warum Abmeldeseiten einen schlechten Ruf haben.
    """
    zurueck = ""
    if link_text and link_url:
        zurueck = (f'<p style="margin:24px 0 0"><a href="{link_url}" '
                   f'style="color:{_MID}">{link_text}</a></p>')

    return HTMLResponse(f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>{ueberschrift} — KOMPAGNON</title></head>
<body style="margin:0;background:#F6F5F2;font-family:'Noto Sans',Arial,sans-serif;
             color:#101315;line-height:1.6">
  <div style="max-width:34rem;margin:0 auto;padding:64px 20px">
    <div style="background:#fff;border-top:4px solid {_DARK};padding:32px 28px">
      <h1 style="margin:0 0 12px;font-size:22px;line-height:1.25;color:{_DARK}">
        {ueberschrift}</h1>
      <p style="margin:0;color:#454B4E">{satz}</p>
      {zurueck}
    </div>
    <p style="margin:24px 0 0;font-size:12px;color:#71797D">
      KOMPAGNON Communications BP GmbH ·
      <a href="mailto:info@kompagnon.eu" style="color:#71797D">info@kompagnon.eu</a>
    </p>
  </div>
</body></html>""")


@router.get("/{token}", response_class=HTMLResponse)
def abmelden(token: str, db: Session = Depends(get_db)):
    """Ein Klick, und die Strecke endet.

    Der Rueckweg steht auf der Seite: Ein Postfach-Scanner, der Links
    automatisch abruft, soll niemanden endgueltig austragen koennen.
    """
    lead_id = abmeldung.lead_aus_token(token)
    if lead_id is None:
        raise HTTPException(400, "Dieser Abmeldelink ist nicht gueltig.")

    abmeldung.setzen(db, lead_id, aktiv=False)

    return _seite(
        "Sie sind abgemeldet.",
        "Sie erhalten keine weiteren E-Mails aus dieser Reihe. "
        "Nachrichten, die Sie selbst anfordern — etwa einen Bericht — "
        "sind davon nicht betroffen.",
        "War das ein Versehen? Abmeldung rueckgaengig machen",
        f"/api/mail/abmelden/{token}/rueckgaengig")


@router.get("/{token}/rueckgaengig", response_class=HTMLResponse)
def rueckgaengig(token: str, db: Session = Depends(get_db)):
    lead_id = abmeldung.lead_aus_token(token)
    if lead_id is None:
        raise HTTPException(400, "Dieser Abmeldelink ist nicht gueltig.")

    abmeldung.setzen(db, lead_id, aktiv=True)

    return _seite(
        "Willkommen zurueck.",
        "Die Abmeldung ist zurueckgenommen, Sie erhalten die Reihe weiter. "
        "Abmelden koennen Sie sich jederzeit ueber den Link am Ende jeder "
        "E-Mail.")
