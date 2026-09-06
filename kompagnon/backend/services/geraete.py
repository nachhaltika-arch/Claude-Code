# -*- coding: utf-8 -*-
'''Wo ist mein Konto angemeldet — und wie melde ich ein Gerät ab?

**Der Anlass (06.09.2026).** Das Kundenkonto bekommt eine Kontoverwaltung, und
dazu gehört die Frage, die jeder von seiner Bank kennt: *Auf welchen Geräten
bin ich eingeloggt?* Die Tabelle `user_sessions` gibt es seit Langem — mit
`ip_address`, `user_agent`, `created_at`. **Geschrieben hat sie nie jemand:**
`UserSession` wird in `auth_router` importiert und nirgends benutzt, die
Tabelle ist leer. Ein Modell ohne Schreiber.

**Der Token wird gehasht abgelegt, nie im Klartext.** Die Spalte heißt
`token`, aber was darin steht, ist ein SHA-256 des JWT. Wer die Datenbank
liest, bekommt damit keine gültige Anmeldung in die Hand — und für den
Abgleich reicht der Hash.

**Die Sperre ist eine Ausschlussliste, keine Zulassungsliste.** Das ist die
wichtigste Entscheidung hier. Eine Zulassungsliste („nur Token mit Zeile
gelten") würde beim Ausrollen **jeden** ausloggen, dessen Token vor dieser
Änderung ausgegeben wurde — Kunden wie Innendienst, ohne Vorwarnung. Die
Ausschlussliste sperrt nur, was ausdrücklich abgemeldet wurde. Unbekannte
Token laufen weiter.

Der Preis: Ein Token, der vor der Umstellung ausgegeben wurde, lässt sich
nicht abmelden — er hat keine Zeile. Er läuft aus. Das ist der ruhigere
Fehler von beiden.
'''
import hashlib
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

#: Wie viele Anmeldungen ein Konto in der Übersicht zeigt. Mehr sagt nichts
#: mehr — wer 40 Zeilen sieht, sieht keine davon.
LISTE_MAX = 20


def fingerabdruck(token: str) -> str:
    """SHA-256 des Tokens, hexadezimal. Nie der Token selbst."""
    return hashlib.sha256((token or "").encode("utf-8")).hexdigest()


def _geraetename(user_agent: str) -> str:
    '''Aus der Kennung des Browsers ein Wort, das ein Mensch wiedererkennt.

    **Bewusst grob.** „Chrome auf Windows" genügt, um das eigene Gerät von
    einem fremden zu unterscheiden; eine genaue Versionsangabe hilft niemandem
    und sieht aus, als wüssten wir mehr über den Nutzer, als er erwartet.
    '''
    ua = (user_agent or "").lower()
    if not ua:
        return "Unbekanntes Gerät"

    system = ("iPhone" if "iphone" in ua else
              "iPad" if "ipad" in ua else
              "Android-Gerät" if "android" in ua else
              "Mac" if "macintosh" in ua or "mac os" in ua else
              "Windows-PC" if "windows" in ua else
              "Linux-Rechner" if "linux" in ua else "")

    browser = ("Edge" if "edg/" in ua else
               "Chrome" if "chrome" in ua and "safari" in ua else
               "Firefox" if "firefox" in ua else
               "Safari" if "safari" in ua else "")

    if browser and system:
        return f"{browser} auf {system}"
    return browser or system or "Unbekanntes Gerät"


def anmeldung_merken(db, *, user_id: int, token: str, ip: str,
                     user_agent: str, gueltig_bis: Optional[datetime] = None):
    '''Eine Anmeldung festhalten — beim Login, nicht bei jeder Anfrage.

    **Fehler hier dürfen die Anmeldung nicht verhindern.** Wer sich einloggen
    will, soll hineinkommen, auch wenn die Geräteliste gerade klemmt. Deshalb
    wird jede Ausnahme protokolliert und verschluckt: Die Liste ist eine
    Auskunft, keine Bedingung.
    '''
    from modelle_konten import UserSession

    try:
        db.add(UserSession(
            user_id=user_id,
            token=fingerabdruck(token),
            ip_address=(ip or "")[:50],
            user_agent=(user_agent or "")[:500],
            created_at=datetime.utcnow(),
            expires_at=gueltig_bis,
            is_valid=True,
        ))
        db.commit()
    except Exception:  # noqa: BLE001
        db.rollback()
        logger.warning("Anmeldung nicht als Geraet vermerkt (user %s)", user_id)


def ist_abgemeldet(db, token: str) -> bool:
    '''Wurde genau dieser Token abgemeldet?

    Läuft bei **jeder** Anfrage — deshalb eine einzige indizierte Abfrage auf
    den Hash, und im Zweifel `False`. Eine klemmende Datenbank darf niemanden
    aussperren; sie sperrt ohnehin schon eine Zeile weiter oben, wo der Nutzer
    geladen wird.
    '''
    from modelle_konten import UserSession

    try:
        zeile = (db.query(UserSession)
                   .filter(UserSession.token == fingerabdruck(token))
                   .first())
    except Exception:  # noqa: BLE001
        db.rollback()
        return False
    return bool(zeile and not zeile.is_valid)


def liste(db, user_id: int, aktueller_token: str = "") -> list:
    """Die Anmeldungen eines Kontos, jüngste zuerst — ohne den Token."""
    from modelle_konten import UserSession

    jetzt = datetime.utcnow()
    hier = fingerabdruck(aktueller_token) if aktueller_token else None

    zeilen = (db.query(UserSession)
                .filter(UserSession.user_id == user_id)
                .order_by(UserSession.created_at.desc())
                .limit(LISTE_MAX)
                .all())

    return [{
        "id": z.id,
        "geraet": _geraetename(z.user_agent),
        # **Die Adresse gekürzt.** Das letzte Glied sagt einem Nutzer nichts
        # und ist ein personenbezogenes Datum mehr, als die Auskunft braucht.
        "netz": ".".join((z.ip_address or "").split(".")[:3]) + ".x"
                if (z.ip_address or "").count(".") == 3 else "",
        "angemeldet_am": z.created_at.isoformat() if z.created_at else None,
        "laeuft_ab": z.expires_at.isoformat() if z.expires_at else None,
        "abgelaufen": bool(z.expires_at and z.expires_at < jetzt),
        "abgemeldet": not z.is_valid,
        "dieses_geraet": hier is not None and z.token == hier,
    } for z in zeilen]


class NichtGefunden(LookupError):
    """Eine Anmeldung, die es nicht gibt — oder nicht die eigene."""


def abmelden(db, *, user_id: int, sitzung_id: int) -> dict:
    '''Eine Anmeldung sperren.

    **Die Zeile wird nicht gelöscht, sondern ungültig gesetzt.** Gelöscht wäre
    die Frage „von wo war mein Konto offen?" nicht mehr beantwortbar — und
    genau die stellt sich, wenn jemand einen Missbrauch vermutet.
    '''
    from modelle_konten import UserSession

    zeile = (db.query(UserSession)
               .filter(UserSession.id == sitzung_id,
                       UserSession.user_id == user_id)
               .first())
    if zeile is None:
        raise NichtGefunden("Diese Anmeldung gehört nicht zu Ihrem Konto.")

    zeile.is_valid = False
    db.commit()
    return {"id": zeile.id, "abgemeldet": True}
