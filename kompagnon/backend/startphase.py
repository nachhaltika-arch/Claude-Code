"""Was beim Start einmal nachgezogen wird — Seed und Altbestand.

**Warum getrennt von `main.py`.** Diese fuenf Funktionen haben mit dem
Aufbau der Anwendung nichts zu tun: Sie legen Demo-Daten an, ueberfuehren
Altbestaende und schalten Demo-Konten ab. Ihr einziger Aufrufer ist die
Phasenliste in `lifespan`; sie stehen dort als Name in einer Zeile.

Am 2026-08-30 aus `main.py` herausgeloest (L-25) — 335 ihrer damals 1.221
Zeilen. Die Datei war seit dem Herausloesen der Migrationen am 22.08. wieder
ueber die 800-Zeilen-Grenze gewachsen.

**Der Schnitt geht nach Zustaendigkeit, nicht nach Groesse:** Was hier steht,
laeuft **einmal beim Start** und schreibt in die Datenbank. Was in `main.py`
bleibt, baut die Anwendung auf und beantwortet Anfragen.
"""
import logging
import os
import secrets
from datetime import datetime

logger = logging.getLogger(__name__)


def _kurse_zusammenfuehren():
    """Startphase: die alte Kurstabelle in die Akademie überführen."""
    from services.kurse_zusammenfuehren import zusammenfuehren_beim_start

    zusammenfuehren_beim_start()


def _zuweisungs_kennungen_nachziehen():
    """Startphase: Altzeilen der Akademie-Zuweisung auf die Benutzer-ID ziehen."""
    from services.zuweisung_kennung import nachziehen_beim_start

    nachziehen_beim_start()


def _lebenszyklus_phasen_nachtragen():
    """Startphase: Lebenszyklus-Phase fuer Bestandsbetriebe nachtragen."""
    from services.lebenszyklus_nachtrag import nachtragen_beim_start

    nachtragen_beim_start()


def _create_default_admin():
    """Create demo users for all 4 roles — only in explicit non-production environments.

    Whitelist: laeuft nur bei ENVIRONMENT in {development, dev, local, staging}.
    Passwoerter kommen ausschliesslich aus ENV-Vars; fehlen sie, wird ein
    Zufallspasswort generiert und einmalig geloggt.
    """
    env = os.getenv("ENVIRONMENT", "development").lower()
    if env not in ("development", "dev", "local", "staging"):
        logger.info(f"⏭  Demo-User-Erstellung übersprungen (ENVIRONMENT={env})")
        return

    from database import SessionLocal, User
    from auth import hash_password
    db = SessionLocal()
    try:
        demo_users = [
            {"email": os.getenv("ADMIN_EMAIL",   "admin@kompagnon.de"),   "password": os.getenv("ADMIN_PASSWORD",   ""), "first_name": "Admin",  "last_name": "KOMPAGNON",  "role": "admin"},
            # Aus zwei Demo-Konten (auditor, nutzer) ist am 27.08.2026 eines
            # geworden — wie aus den zwei Rollen. `MITARBEITER_*` sind die
            # neuen Variablennamen; die alten werden weiter gelesen, damit
            # eine Umgebung, die sie gesetzt hat, nicht ploetzlich ein
            # Zufallspasswort bekommt.
            {"email": os.getenv("MITARBEITER_EMAIL") or os.getenv("AUDITOR_EMAIL", "mitarbeiter@kompagnon.de"),
             "password": os.getenv("MITARBEITER_PASSWORD") or os.getenv("AUDITOR_PASSWORD", ""),
             "first_name": "Max", "last_name": "Mitarbeiter",
             "role": "mitarbeiter", "position": "Mitarbeiter KOMPAGNON"},
            {"email": os.getenv("KUNDE_EMAIL",   "kunde@kompagnon.de"),   "password": os.getenv("KUNDE_PASSWORD",   ""), "first_name": "Thomas", "last_name": "Mustermann", "role": "kunde"},
        ]
        created = 0
        for ud in demo_users:
            if not db.query(User).filter(User.email == ud["email"]).first():
                pw = ud.pop("password")
                if not pw:
                    pw = secrets.token_urlsafe(12)
                    logger.warning(
                        f"⚠ Demo-User {ud['email']}: kein Passwort in ENV gesetzt, "
                        f"generiertes Dev-Passwort: {pw}  (NUR einmalig beim Anlegen)"
                    )
                pos = ud.pop("position", "")
                user = User(**ud, password_hash=hash_password(pw), position=pos, is_active=True, is_verified=True)
                db.add(user)
                created += 1
                logger.info(f"✓ Demo-User angelegt: {ud['email']} ({ud['role']})")
        if created:
            db.commit()
        else:
            logger.info("Alle Demo-User bereits vorhanden")
    except Exception as e:
        db.rollback()
        logger.error(f"Demo-User Fehler: {e}")
    finally:
        db.close()

    # ── Demo-Kunde vollständig aufbauen ──────────────────────
    try:
        from database import Lead, Project, AuditResult
        from seed_checklists import create_project_checklists

        _db2 = SessionLocal()

        # 1. Demo-Kunde User holen
        demo_kunde = _db2.query(User).filter(
            User.email == "kunde@kompagnon.de"
        ).first()
        if not demo_kunde:
            _db2.close()
            return

        # 2. Prüfen ob bereits vollständig eingerichtet
        if demo_kunde.lead_id:
            _db2.close()
            logger.info("Demo-Kunde bereits vollständig eingerichtet")
            return

        # 3. Portal-Token erzeugen (qr_service oder uuid-Fallback)
        try:
            from services.qr_service import generate_token
            _token = generate_token()
        except Exception:
            import uuid as _uuid
            _token = _uuid.uuid4().hex

        # 4. Demo-Lead anlegen
        demo_lead = Lead(
            company_name         = "Mustermann Sanitär GmbH",
            contact_name         = "Thomas Mustermann",
            email                = "kunde@kompagnon.de",
            phone                = "+49 261 987654",
            website_url          = "https://mustermann-sanitaer.de",
            city                 = "Koblenz",
            trade                = "Sanitär",
            lead_source          = "stripe_checkout",
            status               = "won",
            notes                = "Demo-Kunde | Paket: KOMPAGNON | 2.000 EUR",
            customer_token       = _token,
            onboarding_completed = False,
        )
        _db2.add(demo_lead)
        _db2.flush()

        # 5. User mit Lead verknüpfen + Passwort sicherstellen
        demo_kunde.lead_id      = demo_lead.id
        demo_kunde.first_name   = "Thomas"
        demo_kunde.last_name    = "Mustermann"
        demo_kunde.is_active    = True
        demo_kunde.is_verified  = True
        from auth import hash_password
        demo_kunde.password_hash = hash_password("Kunde2025!")

        # 6. Projekt in Phase 1 anlegen
        demo_project = Project(
            lead_id       = demo_lead.id,
            status        = "phase_1",
            start_date    = datetime.utcnow(),
            fixed_price   = 2000.0,
            hourly_rate   = 45.0,
            ai_tool_costs = 50.0,
        )
        _db2.add(demo_project)
        _db2.flush()

        # 7. Alle Checklisten-Einträge anlegen
        create_project_checklists(_db2, demo_project.id)

        _db2.commit()

        logger.info(
            f"✓ Demo-Kunde vollständig angelegt: "
            f"Lead {demo_lead.id} | Projekt {demo_project.id} | "
            f"Portal-Token: {demo_lead.customer_token}"
        )

    except Exception as e:
        logger.warning(f"Demo-Kunde Setup Fehler: {e}")
    finally:
        try:
            _db2.close()
        except Exception:
            pass

    # ── Produkte seeden (nur wenn Tabelle leer) ──────────────
    try:
        from database import SessionLocal
        from sqlalchemy import text as _t
        _db3 = SessionLocal()
        count = _db3.execute(_t("SELECT COUNT(*) FROM products")).scalar()
        if count == 0:
            # Der Katalog einer frischen Datenbank. Bis zum 23.08.2026
            # standen hier Starter/KOMPAGNON/Premium zu 1.500/2.000/2.800 EUR
            # brutto, waehrend die Angebote Websprints zu 3.500/7.900/12.900
            # EUR **netto** fuehrten — zwei Produktlinien nebeneinander, und
            # aus dieser Zeile zieht die Stripe-Sitzung ihren Betrag (L-97).
            #
            # Die Bestandsprodukte werden nicht geloescht, sondern in der
            # Migration auf `archived` gesetzt: Ein Projekt aus dem Fruehjahr
            # traegt `package_type='kompagnon'`, und die Kundenmail liest den
            # Preis aus genau dieser Zeile. Wer sie entfernt, deutet eine
            # bezahlte Rechnung nachtraeglich um.
            #
            # Preise sind **netto** angegeben (B2B, Handwerksbetriebe sind
            # vorsteuerabzugsberechtigt); `price_brutto` ist der Betrag, den
            # Stripe abbucht, und muss dazu passen — `test_produktkatalog`
            # rechnet es nach.
            SEED = [
                {
                    # WS-STA-01, aufgenommen am 04.09.2026 (L-164). Steht
                    # **vor** dem Relaunch: Die Leiter beginnt beim kleinsten
                    # Paket. `draft`, weil das Datenblatt als Freigabe den
                    # Meilenstein „Pflege-Abo aktiv, 24.09.2026" nennt — ohne
                    # laufende Abrechnung verkauft es eine Leistung, die
                    # niemand in Rechnung stellt.
                    #
                    # `gekoppeltes_abo` haelt nur **welches** Abo dazugehoert,
                    # nicht seinen Preis: Der steht in `services/abo_stunden.py`
                    # und wird in `services/preisangabe.py` verrechnet. § 4.1
                    # des Datenblatts verlangt den Gesamtpreis der
                    # Mindestlaufzeit in **jeder** Preisangabe; eine getippte
                    # Zahl waere falsch, sobald jemand das Entgelt aendert.
                    "slug": "websprint_start", "name": "Websprint Start",
                    "sort_order": 0,
                    "short_desc": "Ein-Seiten-Auftritt nach Homepage-Standard, inkl. 12 Monate Pflege",
                    "price_brutto": 1785.00, "price_netto": 1500.00, "tax_rate": 19,
                    "payment_type": "once", "delivery_days": 7, "status": "draft",
                    "gekoppeltes_abo": "ABO-BAS", "abo_mindestlaufzeit": 12,
                    "features": [
                        "Audit nach Homepage-Standard, dokumentiert",
                        "Eine Seite mit Betrieb, Leistungen, Einzugsgebiet, Kontakt und Oeffnungszeiten",
                        "Aufbau aus einer festen Vorlage des KOMPAGNON-Komponentensystems, responsiv",
                        "Einpflegen der gelieferten Texte, bis 4.000 Zeichen",
                        "Bildaufbereitung, bis 10 Bilder",
                        "Kontaktformular mit Spam-Schutz",
                        "Grundlagen der Barrierefreiheit",
                        "Technische Optimierung und strukturierte Auszeichnung",
                        "Hosting-Einrichtung, SSL, Domainumstellung",
                        "Eine Korrekturschleife",
                        "Abnahmeaudit mit schriftlichem Protokoll",
                        "Einweisungsvideo statt Live-Schulung",
                        "Pflege Basic fuer 12 Monate: Hosting, Sicherungen, Ueberwachung, 30 Minuten Aenderungen je Monat",
                        "Nicht enthalten: weitere Unterseiten, Texterstellung, Vor-Ort-Termine, individuelle Gestaltung"],
                    "checkout_fields": ["name", "company", "email", "phone"],
                    "webhook_actions": ["create_lead", "create_user",
                        "create_project", "send_welcome_email", "send_pdf"],
                },
                {
                    "slug": "websprint_relaunch", "name": "Websprint Relaunch",
                    "sort_order": 1,
                    "short_desc": "Bestehende Website auf den Homepage-Standard heben",
                    "price_brutto": 4165.00, "price_netto": 3500.00, "tax_rate": 19,
                    "payment_type": "once", "delivery_days": 14, "status": "live",
                    # Merkmale und Bauzeit aus dem Leistungsverzeichnis in
                    # docs/produkte/ws-rel-01.md. Das Blatt nannte als
                    # Freigabebedingung „nach Behebung L2 und L3".
                    #
                    # **Am 04.09.2026 richtiggestellt.** Hier stand, beides sei
                    # am 23.08. widerlegt — „der PageSpeed-Schluessel
                    # arbeitet". Die Haelfte stimmt: Die Score-Schwellen sind
                    # beidseitig gleich (L3 geschlossen). Der Schluessel
                    # arbeitet **nicht**: Der Produktivbericht vom 04.09.
                    # meldet 78 % Abdeckung, elf Kriterien tragen „nicht
                    # erhoben", darunter alle vier Performance-Werte. Das
                    # Paket bleibt verkaufbar — die zugesicherten 85 Punkte
                    # der Standard-Garantie sind es nicht, siehe L-165.
                    "features": [
                        "Eingangsaudit nach Homepage-Standard, 100 Punkte",
                        "Strukturabgleich und Seitenplan",
                        "Aufbau im KOMPAGNON-Komponentensystem, bis 6 Seiten",
                        "Redaktionelle Ueberarbeitung der vorhandenen Texte",
                        "Bildaufbereitung, bis 30 Bilder",
                        "Kontaktformular mit Spam-Schutz",
                        "Grundlagen der Barrierefreiheit",
                        "Technische Grundoptimierung",
                        "Hosting, SSL, Weiterleitungen, Domainumstellung",
                        "Eine Korrekturschleife",
                        "Abnahmeaudit mit schriftlichem Protokoll",
                        "Einweisung, 30 Minuten"],
                    "checkout_fields": ["name", "company", "email", "phone"],
                    "webhook_actions": ["create_lead", "create_user",
                        "create_project", "send_welcome_email", "send_pdf"],
                },
                {
                    "slug": "websprint_neubau", "name": "Websprint Neubau",
                    "sort_order": 2,
                    "short_desc": "Neuaufbau nach Homepage-Standard, bis 12 Seiten",
                    "price_brutto": 9401.00, "price_netto": 7900.00, "tax_rate": 19,
                    "payment_type": "once", "delivery_days": 28, "status": "live",
                    "highlighted": True, "highlight_label": "Empfehlung",
                    "features": ["Positionierungsgespraech, 90 Minuten",
                        "Bauplan als Freigabedokument, eine Ueberarbeitung",
                        "Texterstellung fuer bis zu 12 Seiten",
                        "Bildkonzept und Fotobriefing",
                        "Aufbau im KOMPAGNON-Komponentensystem, responsiv",
                        "Technische Optimierung und strukturierte Auszeichnung",
                        "Hosting, SSL, Weiterleitungen, Domainumstellung",
                        "Zwei Korrekturschleifen",
                        "Abnahmeaudit mit schriftlichem Protokoll",
                        "Einweisung, 60 Minuten",
                        "Pflege Basic fuer 3 Monate",
                        "Re-Audit nach 3 Monaten"],
                    "checkout_fields": ["name", "company", "email", "phone"],
                    "webhook_actions": ["create_lead", "create_user",
                        "create_project", "send_welcome_email", "send_pdf"],
                },
                {
                    "slug": "websprint_system", "name": "Websprint System",
                    "sort_order": 3,
                    "short_desc": "Neubau mit GEO/GAIO, Karriereseite und Messgrundlage",
                    "price_brutto": 15351.00, "price_netto": 12900.00, "tax_rate": 19,
                    "payment_type": "once", "delivery_days": 42, "status": "draft",
                    # `draft`, nicht `live`: Die Kernleistung dieses Pakets —
                    # Auslieferung von llms.txt, schema.org und Ground Page an
                    # die Kundenseite — ist nicht implementiert (L-99). Das
                    # Datenblatt WS-SYS-01 fuehrt es selbst als 🔴 gesperrt.
                    "features": ["Alles aus dem Websprint Neubau",
                        "Erweiterter Seitenumfang, bis 20 Seiten",
                        "Karriereseite mit Bewerbungsformular",
                        "GEO/GAIO-Layer: llms.txt, schema.org, Ground Page",
                        "Messgrundlage mit Consent-Layer und EU-Datenhaltung",
                        "Auftragsverarbeitungsvertrag",
                        "Pflege Pro fuer 12 Monate",
                        "Quartalsweises Re-Audit mit Massnahmenliste",
                        "Jahresgespraech, 90 Minuten"],
                    "checkout_fields": ["name", "company", "email", "phone"],
                    "webhook_actions": ["create_lead", "create_user",
                        "create_project", "send_welcome_email", "send_pdf"],
                },
            ]
            import json as _j
            for p in SEED:
                _db3.execute(_t("""
                    INSERT INTO products
                    (slug, name, short_desc, price_brutto, price_netto,
                     tax_rate, payment_type, delivery_days, status,
                     highlighted, highlight_label, features,
                     checkout_fields, webhook_actions, sort_order,
                     gekoppeltes_abo, abo_mindestlaufzeit)
                    VALUES (:slug, :name, :sd, :pb, :pn, :tr, :pt, :dd,
                     :status, :hl, :hll, :feat::jsonb, :cf::jsonb, :wa::jsonb, :so,
                     :abo, :abomon)
                """), {
                    "slug": p["slug"], "name": p["name"], "sd": p["short_desc"],
                    "pb": p["price_brutto"], "pn": p["price_netto"],
                    "tr": p["tax_rate"], "pt": p["payment_type"],
                    "dd": p["delivery_days"], "status": p["status"],
                    "hl": p.get("highlighted", False),
                    "hll": p.get("highlight_label", ""),
                    "feat": _j.dumps(p["features"]),
                    "cf":   _j.dumps(p["checkout_fields"]),
                    "wa":   _j.dumps(p["webhook_actions"]),
                    "so":   p["sort_order"],
                    "abo":    p.get("gekoppeltes_abo"),
                    "abomon": p.get("abo_mindestlaufzeit", 0),
                })
            _db3.commit()
            logger.info(f"✓ {len(SEED)} Produkte geseedet")
        _db3.close()
    except Exception as e:
        logger.warning(f"Produkt-Seed Fehler: {e}")

    # Der Block „Produkte seeden" stand hier bis zum 22.08.2026 ein
    # **zweites** Mal, wortgleich bis auf Zeilenumbrueche (L-29). Er war
    # wirkungslos — `count == 0` trifft nicht mehr zu, wenn der Block
    # darueber gerade geseedet hat. Die Falle lag im Aendern: Wer einen
    # Preis in der zweiten Vorlage anpasste, aenderte nichts, und nichts
    # sagte es ihm. `tests/test_produktvorlage.py` haelt es bei einer.


def _disable_demo_accounts_in_production():
    """Deaktiviert Demo-Konten wenn ENVIRONMENT=production gesetzt ist."""
    if os.getenv("ENVIRONMENT", "development").lower() != "production":
        return

    # Die alten beiden Adressen bleiben stehen, obwohl sie niemand mehr
    # anlegt: Wer sie in einer Umgebung schon hat, soll sie auch abgeschaltet
    # bekommen. Eine Liste, die einen Namen nicht mehr kennt, den der Bestand
    # noch traegt, laesst genau die Konten offen, die sie schliessen soll.
    DEMO_EMAILS = [
        "admin@kompagnon.de",
        "mitarbeiter@kompagnon.de",
        "auditor@kompagnon.de",
        "nutzer@kompagnon.de",
        "kunde@kompagnon.de",
    ]

    from database import SessionLocal, User
    db = SessionLocal()
    try:
        deactivated = 0
        for email in DEMO_EMAILS:
            user = db.query(User).filter(User.email == email).first()
            if user and user.is_active:
                user.is_active = False
                deactivated += 1
                logger.warning(f"🔒 Demo-Konto deaktiviert: {email}")
        if deactivated:
            db.commit()
            logger.warning(f"🔒 {deactivated} Demo-Konten in Produktion deaktiviert")
        else:
            logger.info("✓ Keine aktiven Demo-Konten gefunden")
    except Exception as e:
        db.rollback()
        logger.error(f"Demo-Deaktivierung fehlgeschlagen: {e}")
    finally:
        db.close()
