# Netlify-Prozess: Vollständige Dokumentation

## Schritt 1 — Site anlegen
Trigger: Admin klickt "Netlify-Site anlegen" in Schritt 10 (Veröffentlichen)
API: POST /api/projects/{id}/netlify/customer-create-site
Ergebnis: netlify_site_id + netlify_site_url in DB

## Schritt 2 — Alle Seiten deployen
Trigger: Admin klickt "Jetzt veröffentlichen"
API: POST /api/projects/{id}/netlify/deploy-all
Ergebnis: Alle GrapesJS-Seiten als HTML-Dateien auf Netlify

## Schritt 3 — Custom Domain setzen
Admin gibt Kundendomain ein → API setzt Custom Domain auf Netlify
Automatisch: DNS-Guide per E-Mail an Kunden + Portal-Nachricht

## Schritt 4 — Kunde trägt DNS ein
Beim Domain-Anbieter (IONOS, Strato etc.):
  A:     @    → 75.2.60.5
  CNAME: www  → [site].netlify.app

Optional (Alias-E-Mails):
  MX:  @  → mx1.forwardemail.net (Prio 10)
  TXT: @  → forward-email=info:kunde@gmail.com

## Schritt 5 — DNS-Polling (automatisch, alle 15 Min.)
Prüft per IP-Lookup ob DNS aktiv ist.
Bei Erfolg: netlify_domain_status = 'active', Portal-Nachricht "Site ist live"

## Schritt 6 — Subdomains (optional)
API: POST /api/projects/{id}/netlify/add-subdomain
Body: { "subdomain": "shop" }
Ergebnis: CNAME-Anleitung für Kunden

## Schritt 7 — SSL-Monitoring (täglich 08:00 Europe/Berlin)
Netlify erneuert Let's Encrypt automatisch alle ~89 Tage.
Job prüft täglich ob ssl_active noch true ist.

## Schritt 8 — SSL-Problem-Alert
Trigger: ssl_active wechselt von true auf false
Automatisch: Portal-Nachricht an Admin + E-Mail an Kunden
Admin muss manuell im Netlify-Dashboard SSL erneuern.

## SSL manuell erneuern (Admin-Anleitung)
1. Netlify-Dashboard öffnen: app.netlify.com
2. Projekt-Site auswählen
3. Domain management → HTTPS
4. "Renew certificate" klicken
5. Warten bis "Certificate status: Approved" erscheint
6. In KAS: netlify_ssl_active manuell auf true setzen

## E-Mail-Weiterleitungen einrichten
generate_dns_guide() akzeptiert email_forwarding-Parameter:
  [{"alias": "info", "ziel": "chef@gmail.com"}]

Erzeugt MX + TXT-Einträge für ForwardEmail.net (kostenlos, DSGVO-konform).
E-Mail wird automatisch in den DNS-Guide per E-Mail an den Kunden eingefügt.
