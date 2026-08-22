"""Die drei Router unter `/api/projects` — an einer Stelle.

**Warum als eigene Datei (L-25, 22.08.2026).** `projects.py` hatte 4.860
Zeilen und wird in Etappen zerlegt. Jedes herausgeloeste Stueck braucht
dieselben Router-Objekte; sie in `projects.py` stehen zu lassen hiesse, dass
jedes neue Modul von dort importiert — und `projects.py` spaeter von ihm.
Ein Kreis, den Python beim Import nicht aufloest.

**Der andere Weg waere schlechter gewesen:** jedem Modul einen **eigenen**
`APIRouter` mit demselben Praefix zu geben und alle in `main.py` zu
registrieren. Dann liegen zwei Router auf einer Adresse — genau die Bauart,
die `tests/test_router_kollisionen.py` seit dem 21.08.2026 verbietet und die
L-28 gekostet hat: Es gewinnt der zuerst eingebundene, der andere ist tot,
und **niemand sagt es**.

So bleibt es **ein** Router je Zugangsart, und die Module haengen ihre Routen
nur daran. Die Adressen aendern sich dadurch nicht — ein Umzug, den das
Frontend bemerkt, ist ein misslungener.
"""
from fastapi import APIRouter, Depends

from routers.auth_router import require_any_auth, require_innendienst

router = APIRouter(prefix="/api/projects", tags=["projects"],
                   dependencies=[Depends(require_innendienst)])

# Ausdrücklich ohne Anmeldung — die Freigabe des Kunden über den Link aus der
# E-Mail. Der Token IST der Nachweis; die Routen prüfen ihn selbst.
public_router = APIRouter(prefix="/api/projects", tags=["projects-public"])

# Was ein Kunde am eigenen Projekt tun darf: es ansehen und Inhalte freigeben.
# Jede Route hier grenzt über `eigenes_projekt_pruefen` auf den eigenen Betrieb
# ein. Alles Übrige ist Innendienst — darunter `/{id}/credentials`, das
# entschlüsselte CMS-Passwörter herausgibt.
kunden_router = APIRouter(prefix="/api/projects", tags=["projects-kunde"],
                          dependencies=[Depends(require_any_auth)])
