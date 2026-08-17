---
name: resume-point-2026-08-16
description: "Stand 2026-08-16 — eigene Domains api./kas.kompagnon.group live, sieben Webhooks nahmen unsignierte Fremdanfragen an, Anforderungskatalog bis auf die Branchen-Ausweitung zu, UX-Prüfung nach Krug mit Arbeitsliste; morgen Paket 2"
metadata: 
  node_type: memory
  type: project
  originSessionId: 23187c5a-98e4-46cd-b53f-9f76742d7f0a
  modified: 2026-08-16T19:54:53.085Z
---

**Ein sehr langer Tag mit drei Teilen.** Geplant war Schritt 2 des Umzugsplans.
Erledigt wurden: die Domains, ein Sicherheitsbefund, die Schließung des
Anforderungskatalogs und eine vollständige UX-Prüfung mit begonnener Umsetzung.

## Teil 1 — Eigene Domains (L-34, Schritt 2 abgeschlossen)

`api.kompagnon.group` (Schnittstelle) und **`kas.kompagnon.group`** (Oberfläche,
Anmeldung unter `/login`) sind live, Zertifikate bis 14.11.2026, DNS bei IONOS.
Alte `onrender.com`-Adressen bleiben gültig. Gesetzt: `API_BASE_URL`,
`CORS_ALLOWED_ORIGINS`, `FRONTEND_URL`.

**Der Durchstich ist vollständig belegt** — Widget → API → Audit (60 s) →
Brevo → Mail → Rücklink auf `api.kompagnon.group`. Zwei Mails im Postfach.

**Auto-Deploy stand auf beiden Produktiv-Diensten auf „On Commit"** — die
Voraussetzung aus `ci.yml:265` war nie erfüllt, der CI-Torwächter also
dekorativ. Jetzt „Off". **Folge im Alltag: Eine Variable zu speichern wirkt
nicht mehr sofort**, der Knopf heißt „Save only", der Deploy muss ausgelöst
werden.

**Brevo blockierte den Mailversand** (401, unbekannte Server-IP). David hat die
IP-Prüfung für API-Schlüssel abgeschaltet — richtig so: Die IPs rotieren
(zwei verschiedene an einem Tag, drei /24-Bereiche in vier Monaten), statische
IPs sind bei Render kostenpflichtig, und nach dem Frankfurt-Umzug ändern sie
sich ohnehin wieder.

## Teil 2 — Sicherheit und Katalog

**Sieben Webhook-Endpunkte nahmen unsignierte Fremdanfragen an.** Drei
Signaturprüfungen trugen `if SECRET:` bzw. `if not secret: return True` —
fehlte die Variable, fand **keine Prüfung** statt, und produktiv war keine je
gesetzt. Live gemessen: 200 ohne Signatur. Jetzt 403, produktiv verifiziert.
**Kein Ausfallrisiko, weil nachgezählt:** `webhook_log` leer, 0 Leads aus
diesen Quellen, 0 Affiliate-Conversions — nie benutzt.

**Anforderungskatalog: bis auf die Branchen-Ausweitung geschlossen.** § 6.1
galt seit dem 15.08. als erledigt, war es aber nur für den Audit-Pfad — der
PageSpeed-Schlüssel heißt in Render `PAGESPEED_API_KEY`, sieben Aufrufer lasen
`GOOGLE_PAGESPEED_API_KEY`. § 7 und § 8 lasen sich wie Randnotizen und waren
Defekte: Die Vermutung `lead.trade` wurde in zwei kundenwirksamen Dokumenten
als Tatsache gedruckt.

## Teil 3 — UX-Prüfung nach Krug (neu)

**`docs/ux-soll-ist-kas.md`** — 31 Befunde aus drei Nutzerreisen, am laufenden
System erhoben. **`docs/ux-arbeitsliste.md`** — abzuarbeiten, jeder Punkt mit
Fundstelle und Prüfschritt. Browser-Fassung:
`https://claude.ai/code/artifact/946b018e-40f7-481f-826a-83fbf9d53d66`

**Paket 1 ist abgeschlossen:** ein Vokabular (**„Betrieb"**, entschieden nach
der kundenseitigen Sprache), Statuswerte übersetzt (`utils/leadStatus.js` als
einzige Quelle), Menü „Deals" statt „Pipeline", und die Adressen umbenannt —
`/app/betriebe`, `/app/betriebe/:id`, `/app/projektpipeline`, alte leiten
weiter.

**Morgen: Paket 2** — die zwei Listen derselben Firmen zusammenlegen
(„Unternehmen" 61 / „Kunden" 50). Vorher klären, warum die Zahlen abweichen.
Danach Paket 3 (vier Stellen, an denen die Oberfläche etwas Falsches behauptet).

## Was der Tag über die Arbeitsweise sagt

**Zweimal habe ich mich selbst korrigieren müssen, beide Male öffentlich im
Dokument:** UX-01 („Menü widerspricht dem Titel") war falsch — ich hatte die
Adresse von Hand aufgerufen. Und die leeren Dashboard-Kacheln waren nicht leer,
sondern langsam. Beide Korrekturen stehen sichtbar in der Analyse; eine stille
Korrektur wäre genau das, was ich dem System vorwerfe.

**Der beste Fund kam vom Hinsehen, nicht vom Lesen:** Nach einer Weiterleitung
blieb die Seitenleiste ganz zugeklappt — Tests grün, Build sauber, Code
korrekt, Navigation blind. Kein Test hätte das gefunden. Es lohnt sich, Dinge
gemeinsam am Bildschirm anzusehen.

## Offen bei David

- **Sammel-PR** `staging → main` — dreizehn Commits, davon sechs UX. Regelgemäß
  freitags ([[feedback-pr-only-fridays]])
- **Der eigentliche Umzug nach Frankfurt** (L-34) — Blueprint liegt
  (`render-produktiv.yaml`), danach L-44 (Inbound-Regel). **Eigene Sitzung**
- Produktiv fehlen `STRIPE_SECRET_KEY` (Zahlungen unmöglich) und
  `CMS_ENCRYPTION_KEY`; `SUPERADMIN_EMAIL`/`_PASSWORD` sind gesetzt und werden
  **nirgends gelesen**
- Uploads liegen auf flüchtigem Dateisystem, kein `disk:` in den Blueprints —
  die eine vorhandene Datei ist bereits verloren
- Ungeklärt: Wer hat die Widget-Bestätigung um 16:12:09 per POST ausgelöst?
  Der Code ist korrekt gebaut, im Protokoll steht keine Abweisung — aber ich
  habe nur die Seite abgerufen. DSGVO-relevant, gehört gezielt nachgesehen

Prüfstand: **976 Backend-, 109 Frontend-Tests**, CI grün.
Voriger Stand [[resume-point-2026-08-15]]; Fehlerbauart wie
[[migration-trap-main-py]].
