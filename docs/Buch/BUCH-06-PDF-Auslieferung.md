# BUCH-06 — PDF-Auslieferung: Wasserzeichen, signierte Links, Versandmail

## Warum dieser Schritt

Ein verkauftes PDF muss beim Käufer ankommen — und zwar so, dass es nicht am nächsten Tag
in einer WhatsApp-Gruppe von Handwerksmeistern kursiert.

Drei Maßnahmen, gestaffelt nach Wirkung:

1. **Kein fester Download-Pfad.** Läge das PDF unter
   `https://…/static/homepage-standard.pdf`, wäre es nach dem ersten Verkauf öffentlich.
   Stattdessen: ein zufälliges Einmal-Token pro Bestellung, gültig 14 Tage, maximal
   5 Downloads.
2. **Personalisiertes Wasserzeichen.** In die Fußzeile jeder Seite wird eingestempelt:
   *Lizenziert für Max Mustermann, Mustermann GmbH · Bestellnr. HS-2026-0042*. Das hält
   niemanden technisch auf, aber es verhindert leichtfertiges Weitergeben zuverlässig —
   niemand verschickt ein Dokument mit dem eigenen Namen darauf.
3. **Zustellung per Mail statt direkter Anzeige.** Das PDF geht per Brevo an die
   bestätigte Adresse, nicht an den Browser, der gerade auf der Danke-Seite steht.

**Technisch wichtig:** Das Buch wird nicht bei jeder Bestellung neu gerendert (siehe
`BUCH-03`). Wir nehmen das fertige PDF und stempeln nur das Wasserzeichen ein. Das dauert
unter einer Sekunde statt 60.

---

## PFLICHT-CHECK

```bash
git remote -v && git branch --show-current
```

---

## PROMPT FÜR CLAUDE CODE

```
Führe zuerst aus: git remote -v && git branch --show-current
Erwartet: origin = nachhaltika-arch/Claude-Code, branch = claude/kompagnon-automation-system-FapM9
Bei Abweichung: stoppe und melde.

SCHRITT 0 — Bestand pruefen
Zeige mir, welche E-Mail-Module im Backend existieren. Laut fruehrerer Analyse gibt es
ein Duplikat, das stille Fallback-Fehler verursacht. Sag mir, welches Modul das
produktiv genutzte ist, und verwende NUR dieses. Lege kein drittes an.

SCHRITT 1 — Speicherort des Master-PDF
Das gebaute PDF liegt nicht im Repo. Es muss zur Laufzeit erreichbar sein.
Baue backend/services/book_asset.py mit einer Funktion get_master_pdf_path(),
die in dieser Reihenfolge sucht:
  1. Pfad aus ENV BOOK_PDF_PATH
  2. /opt/render/project/src/buch/build/homepage-standard-screen.pdf
Fehlt die Datei, wirf einen klaren Fehler mit dem gesuchten Pfad im Text.
Logge diesen Fehler als ERROR, nicht als WARNING.

SCHRITT 2 — Wasserzeichen
Lege backend/services/book_watermark.py an.

Funktion: stamp_pdf(master_path, buyer_line, order_number) -> bytes
Vorgehen:
  1. Mit reportlab eine einzelne Overlay-Seite in der Groesse der Master-Seiten
     erzeugen. Inhalt: unten zentriert, 7pt, Graustufe 0.45:
     "Lizenziert fuer {buyer_line} · Bestellnr. {order_number} · Weitergabe nicht gestattet"
  2. Mit pypdf ueber alle Seiten des Masters iterieren und das Overlay per
     merge_page() darauflegen
  3. Ergebnis als BytesIO zurueckgeben, NICHT auf Platte schreiben
WICHTIG: Keine Unicode-Sub-/Superscript-Zeichen verwenden, reportlab-Standardschriften
enthalten diese Glyphen nicht und rendern schwarze Kaesten.
Setze zusaetzlich die PDF-Metadaten: Title, Author "KOMPAGNON communications BP GmbH",
Subject mit der Buchversion.

SCHRITT 3 — Download-Token
Ergaenze backend/services/book_delivery.py:

  create_download_token(order) -> str
    secrets.token_urlsafe(32), speichert token + expires_at (jetzt + 14 Tage)

Endpunkt: GET /api/book/download/{token}
  1. Bestellung ueber download_token suchen. Nicht gefunden -> 404 mit neutraler Meldung
  2. payment_status != 'paid' -> 403
  3. download_expires_at abgelaufen -> 410 mit Hinweis, sich per Mail zu melden
  4. download_count >= 5 -> 429 mit demselben Hinweis
  5. download_count um 1 erhoehen, delivered_at setzen falls leer
  6. stamp_pdf() aufrufen und als StreamingResponse ausliefern
     media_type application/pdf
     Content-Disposition: attachment; filename="Homepage-Standard-{version}.pdf"
  7. Cache-Control: no-store

SCHRITT 4 — Versandmail
Ergaenze backend/services/book_delivery.py:

  send_delivery_email(order_id)
    Oeffnet eine EIGENE DB-Session mit SessionLocal() und schliesst sie im finally.
    (Diese Funktion laeuft als BackgroundTask - die Session des Requests ist da
    bereits zu.)
    Laedt die Bestellung, erzeugt Token falls nicht vorhanden, baut die Download-URL
    aus BACKEND_URL + /api/book/download/{token} und versendet ueber das in
    Schritt 0 identifizierte Brevo-Modul.

Mailinhalt (deutsch, Sie-Form, KOMPAGNON-Branding):
  Betreff: "Ihr Homepage Standard - Download bereit (Bestellnr. {order_number})"
  Inhalt: Dank, Download-Button, Hinweis 14 Tage / 5 Downloads,
  Hinweis auf personalisiertes Wasserzeichen,
  bei variant bundle zusaetzlich: gedruckte Ausgabe folgt separat,
  Abschluss: Verweis auf das kostenlose Audit mit Link.

Verknuepfe diese Funktion mit dem Stub aus BUCH-05 Schritt 2 Punkt 8.

SCHRITT 5 — Wiederholbarkeit
Endpunkt: POST /api/book/orders/{id}/resend (nur fuer Admin-Rolle)
Erzeugt ein NEUES Token, setzt download_count auf 0 und versendet die Mail erneut.
Das brauchst du im Support-Fall.

SCHRITT 6 — Verifikation
python -c "
from backend.services.book_watermark import stamp_pdf
data = stamp_pdf('buch/build/homepage-standard-screen.pdf', 'Testkunde, Test GmbH', 'HS-2026-0001')
open('/tmp/test-stamped.pdf','wb').write(data.getvalue() if hasattr(data,'getvalue') else data)
print('OK, Bytes:', len(data.getvalue() if hasattr(data,'getvalue') else data))
"

SCHRITT 7
git add -A
git commit -m "Add watermarked PDF delivery with signed download tokens"
git push origin claude/kompagnon-automation-system-FapM9
```

---

## VERIFIKATION

| Prüfung | Erwartung |
|---|---|
| `/tmp/test-stamped.pdf` öffnen | Wasserzeichen auf **jeder** Seite, lesbar, nicht störend |
| Testkauf durchführen | Mail kommt an, Download funktioniert |
| Download 6× aufrufen | beim 6. Mal HTTP 429 |
| Falsches Token aufrufen | HTTP 404, keine Detailinfos |

**Achtung — der PDF-Pfad auf Render.** Render setzt bei jedem Deploy das Dateisystem
zurück. Wenn das Buch-PDF nicht im Repo liegt (es ist in `.gitignore`), ist es nach dem
nächsten Deploy weg und jeder Download schlägt fehl. **Zwei Optionen:**

- **A (einfach):** PDF doch ins Repo aufnehmen, `.gitignore`-Eintrag entfernen.
  Bei ~10 MB vertretbar, Git wird träge bei vielen Versionen.
- **B (sauber):** PDF in einen S3-kompatiblen Speicher legen (Render Disks oder Cloudflare
  R2) und `BOOK_PDF_PATH` bzw. eine URL darauf zeigen lassen.

Ich empfehle für den Start **A** — funktioniert sofort, kein zusätzlicher Dienst.
Entscheide das, bevor der Prompt läuft, und teile es Claude Code mit.

---

## COMMIT-MESSAGE

```
Add watermarked PDF delivery with signed download tokens
```

---

## ZWEI SCHRITTE VORAUS

- **Der Support-Fall kommt garantiert.** Jemand löscht die Mail, das Token läuft ab.
  Deshalb Schritt 5. Ohne ihn musst du in die Datenbank greifen — an einem Samstag.
- **Der Käufer wird eine Rechnung wollen.** Die Auslieferungsmail ist der natürliche Ort
  dafür. Plane ein, dass hier später die Stripe-Rechnungs-URL mitgeschickt wird.
- **Wasserzeichen und Druck-PDF nicht verwechseln.** Das Wasserzeichen gehört nur ins
  Screen-PDF. Wenn du versehentlich das Druck-PDF stempelst und zu BoD hochlädst, steht
  auf jedem gedruckten Exemplar der Name des ersten Testkäufers.
