"""
Eine eingefrorene Website, gegen die die Erhebung geprüft wird.

Schritt 6 des Anforderungskatalogs verlangt „Tests je Kategorie gegen eine
feste Referenz-Website". Bis zum 15.08.2026 prüften alle Tests die Rechenwege
gegen erfundene Eingaben — die Bewertung war abgedeckt, die Erhebung nicht.
An einem Vormittag fielen deshalb fünf Fehler auf, die keiner der Tests sehen
konnte: eine Fehlerseite, die als Messung zählte; ein Ort, der zwischen zwei
Tags verschwand; eine Datei, die unter dem falschen Namen gesucht wurde;
Spalten, die niemand befüllte.

Eine echte fremde Website taugt dafür nicht: Sie ändert sich, und der Test
würde ohne Codeänderung rot. Diese hier ist festgeschrieben und deckt
bewusst genau die Stellen ab, an denen die Erhebung bisher gescheitert ist:

* Die Anschrift steht in benachbarten Elementen („Straße 12" + „22047 Ort").
* Es gibt eine ``/llms.txt`` — unter dem Namen der Konvention.
* Die ``robots.txt`` sperrt niemanden aus und nennt eine Sitemap.
* Startseite mit Canonical, JSON-LD, Viewport, Alt-Texten, tel:- und
  mailto:-Verweis.
"""

BASIS = "https://referenz-heizung.de"

STARTSEITE = """<!doctype html>
<html lang="de"><head>
<meta charset="utf-8">
<title>Heizung und Sanitär in Musterstadt | Referenz GmbH</title>
<meta name="description" content="Meisterbetrieb für Heizung, Sanitär und Wärmepumpen in Musterstadt. Beratung, Einbau und Wartung aus einer Hand — seit 1998.">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="canonical" href="https://referenz-heizung.de/">
<link rel="icon" href="/favicon.ico">
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"Plumber","name":"Referenz GmbH",
 "address":{"@type":"PostalAddress","postalCode":"22047","addressLocality":"Musterstadt"}}
</script>
</head><body>
<header><a href="tel:+4940123456">040 123456</a>
<a href="mailto:info@referenz-heizung.de">info@referenz-heizung.de</a></header>
<h1>Heizung und Sanitär in Musterstadt</h1>
<h2>Unsere Leistungen</h2>
<img src="/bilder/waermepumpe.jpg" alt="Eingebaute Wärmepumpe in einem Musterstadter Reihenhaus">
<img src="/bilder/bad.jpg" alt="Fertiges Badezimmer mit bodengleicher Dusche">
<ul>
  <li><a href="/leistungen/waermepumpe">Wärmepumpe</a></li>
  <li><a href="/leistungen/bad">Badsanierung</a></li>
  <li><a href="/leistungen/wartung">Wartung</a></li>
</ul>
<h2>So läuft ein Auftrag ab</h2>
<p>Nach Ihrer Anfrage melden wir uns innerhalb von 24 Stunden. Die Besichtigung
ist kostenfrei, danach erhalten Sie ein Festpreisangebot. Auf alle Arbeiten
geben wir fünf Jahre Gewährleistung. Unsere Monteure sind aus Musterstadt und
der Umgebung; Anfahrten innerhalb von 20 Kilometern berechnen wir nicht.
Wir arbeiten seit 1998 als eingetragener Meisterbetrieb und beschäftigen
zwölf Mitarbeiterinnen und Mitarbeiter. Für Notfälle erreichen Sie uns auch
außerhalb der Geschäftszeiten unter der genannten Rufnummer.</p>
<h2>Kontakt</h2>
<form action="/anfrage" method="post">
  <label for="name">Name</label><input id="name" name="name">
  <label for="mail">E-Mail</label><input id="mail" name="mail" type="email">
  <label for="zustimmung">
    <input id="zustimmung" name="zustimmung" type="checkbox">
    Ich habe die <a href="/datenschutz">Datenschutzerklärung</a> gelesen.
  </label>
  <button type="submit">Anfrage senden</button>
</form>
<footer>
  <span>Referenz GmbH</span><span>Musterweg 12</span><span>22047 Musterstadt</span>
  <a href="/impressum">Impressum</a> <a href="/datenschutz">Datenschutz</a>
  <a href="/barrierefreiheit">Erklärung zur Barrierefreiheit</a>
  <p>Stand: 2026 — zuletzt aktualisiert im August 2026</p>
</footer>
</body></html>"""

IMPRESSUM = """<!doctype html><html lang="de"><head><title>Impressum</title></head><body>
<h1>Impressum</h1>
<p>Angaben gemäß § 5 DDG</p>
<p><span>Referenz GmbH</span><span>Musterweg 12</span><span>22047 Musterstadt</span></p>
<p>Vertreten durch den Geschäftsführer Max Muster.</p>
<p>Telefon: 040 123456 — E-Mail: info@referenz-heizung.de</p>
<p>Registergericht: Amtsgericht Musterstadt, Registernummer HRB 12345</p>
<p>Umsatzsteuer-Identifikationsnummer gemäß § 27a UStG: DE123456789</p>
<p>Zuständige Kammer: Handwerkskammer Musterstadt. Berufsbezeichnung:
Installateur- und Heizungsbauermeister, verliehen in Deutschland.</p>
<p>Verantwortlich für den Inhalt: Max Muster, Anschrift wie oben.</p>
</body></html>"""

DATENSCHUTZ = """<!doctype html><html lang="de"><head><title>Datenschutzerklärung</title></head><body>
<h1>Datenschutzerklärung</h1>
<p>Verantwortlicher im Sinne der DSGVO ist die Referenz GmbH, Musterweg 12,
22047 Musterstadt.</p>
<p>Zwecke der Verarbeitung: Bearbeitung Ihrer Anfrage und Angebotserstellung.</p>
<p>Rechtsgrundlage ist Art. 6 Abs. 1 lit. b DSGVO.</p>
<p>Betroffenenrechte: Auskunft, Berichtigung, Löschung, Einschränkung der
Verarbeitung, Datenübertragbarkeit und Widerspruch. Beschwerderecht bei der
Aufsichtsbehörde.</p>
<p>Auftragsverarbeiter: unser Hostinganbieter, gebunden nach Art. 28 DSGVO.</p>
<p>Speicherdauer: bis zum Abschluss der Anfrage, längstens sechs Monate.</p>
</body></html>"""

LEISTUNGSSEITE = """<!doctype html><html lang="de"><head>
<title>Wärmepumpe in Musterstadt — Referenz GmbH</title>
<meta name="description" content="Wärmepumpe planen und einbauen lassen in Musterstadt: Beratung, Förderung, Festpreis.">
</head><body><h1>Wärmepumpe</h1>
<h2>Ablauf und Kosten</h2>
<p>Wir prüfen Ihr Haus, beraten zur Förderung und bauen ein. Die Besichtigung
ist kostenfrei, das Angebot ein Festpreis.</p>
</body></html>"""

ROBOTS = """# robots.txt der Referenz GmbH
Sitemap: https://referenz-heizung.de/sitemap.xml

User-agent: *
Disallow: /anfrage
"""

SITEMAP = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://referenz-heizung.de/</loc></url>
  <url><loc>https://referenz-heizung.de/leistungen/waermepumpe</loc></url>
  <url><loc>https://referenz-heizung.de/impressum</loc></url>
</urlset>"""

LLMS = """# Referenz GmbH
> Meisterbetrieb für Heizung und Sanitär in Musterstadt.

## Seiten
- [Wärmepumpe](https://referenz-heizung.de/leistungen/waermepumpe)
"""

BARRIEREFREIHEIT = """<!doctype html><html lang="de"><head>
<title>Erklärung zur Barrierefreiheit</title></head><body>
<h1>Erklärung zur Barrierefreiheit</h1>
<p>Diese Website erfüllt die Anforderungen des BFSG und orientiert sich an
WCAG 2.1 Level AA.</p></body></html>"""


# Pfad → (Statuscode, Inhalt, Inhaltstyp)
SEITEN = {
    "/": (200, STARTSEITE, "text/html"),
    "/impressum": (200, IMPRESSUM, "text/html"),
    "/datenschutz": (200, DATENSCHUTZ, "text/html"),
    "/barrierefreiheit": (200, BARRIEREFREIHEIT, "text/html"),
    "/leistungen/waermepumpe": (200, LEISTUNGSSEITE, "text/html"),
    "/leistungen/bad": (200, LEISTUNGSSEITE, "text/html"),
    "/leistungen/wartung": (200, LEISTUNGSSEITE, "text/html"),
    "/robots.txt": (200, ROBOTS, "text/plain"),
    "/sitemap.xml": (200, SITEMAP, "application/xml"),
    "/llms.txt": (200, LLMS, "text/plain"),
}

# Kopfzeilen, die die Sicherheitsprüfung erwartet
KOPFZEILEN = {
    "content-type": "text/html; charset=utf-8",
    "strict-transport-security": "max-age=31536000",
    "x-frame-options": "SAMEORIGIN",
    "content-security-policy": "default-src 'self'",
    "x-content-type-options": "nosniff",
    "cache-control": "public, max-age=3600",
    "server": "nginx",
}
