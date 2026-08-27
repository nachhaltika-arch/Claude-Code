# BUCH-11 — Rechtstexte, Compliance, ISBN

## Warum dieser Schritt kein Anhängsel ist

Du verkaufst ein Buch, das Handwerksbetrieben erklärt, wie sie rechtssichere Websites
bauen. **Wenn deine eigene Verkaufsseite rechtlich unsauber ist, ist das Produkt tot.**
Ein einziger Screenshot in einem Handwerkerforum genügt.

Gleichzeitig entstehen durch das Buch selbst drei neue Pflichten, die du bisher nicht
hattest: du wirst Verlag, du verkaufst an Verbraucher, und du gibst rechtsnahe Auskunft.

---

## Die fünf Themen im Überblick

### 1. RDG — die Grenze zur Rechtsberatung

Das Rechtsdienstleistungsgesetz erlaubt jedem, **allgemein** über Rechtslage zu
informieren. Verboten ist die **Rechtsdienstleistung im Einzelfall** durch Nichtanwälte.

| Zulässig im Buch | Unzulässig |
|---|---|
| „§ 5 TMG verlangt folgende Angaben: …" | „In Ihrem Fall genügt es, wenn Sie …" |
| „Gerichte haben Google Fonts als Verstoß gewertet" | „Ihre Seite ist damit abmahnsicher" |
| Musterformulierungen als Beispiel | Individuell angepasste Texte für den Leser |

Praktisch heißt das: **generisch bleiben, nie auf den konkreten Leser eingehen**, und in
jedem Rechtskapitel einen Verweis auf anwaltliche Prüfung. Das ist kein Kleingedrucktes —
es gehört sichtbar in die Titelei und an jeden Kapitelanfang der Rechtsteile.

### 2. Widerrufsrecht bei digitalen Inhalten

Beim PDF-Verkauf erlischt das Widerrufsrecht nur, wenn drei Dinge zusammenkommen
(§ 356 Abs. 5 BGB):

1. Der Käufer verlangt **ausdrücklich**, dass die Lieferung sofort beginnt
2. Er bestätigt, dass er dadurch sein Widerrufsrecht verliert
3. Du **dokumentierst** diese Zustimmung

Punkt 3 ist der Grund für `waiver_accepted_at` in `BUCH-04`. Ohne diese drei Punkte
hat jeder PDF-Käufer 14 Tage Rückgaberecht auf eine Datei, die er längst besitzt.

Beim **gedruckten** Buch gilt das normale 14-tägige Widerrufsrecht — daran führt kein
Weg vorbei, und du musst die Rücksendung ermöglichen.

### 3. Preisangaben

Als Verkäufer an Verbraucher gilt die Preisangabenverordnung: **Gesamtpreis inklusive
Umsatzsteuer**, Versandkosten separat und vorher erkennbar. Ein Preis „39 € zzgl. MwSt."
auf einer Verbraucherseite ist ein Verstoß.

### 4. ISBN, Verlag, Pflichtexemplare

Mit einer ISBN wirst du formal zum Verleger:

| Pflicht | Was zu tun ist |
|---|---|
| ISBN | BoD vergibt eine kostenlos beim Titelanlegen |
| Impressum im Buch | Verlagsangabe, Anschrift, Druckerei-Hinweis |
| Pflichtexemplare | 2 Exemplare an die Deutsche Nationalbibliothek Leipzig/Frankfurt |
| Landesbibliothek | Rheinland-Pfalz: 1 Exemplar an die Rheinische Landesbibliothek Koblenz |

Die Pflichtexemplare kosten dich zwei Bücher und einen Versand. Sie zu unterlassen ist
eine Ordnungswidrigkeit — und wäre für ein Buch über Rechtskonformität schwer erklärbar.

### 5. Urheberrecht an Inhalten

Screenshots fremder Websites im Kapitel „20 häufigste Fehler" sind heikel. Lösung:
**alle Negativbeispiele nachbauen**, nicht abfotografieren. Erfundene Firmennamen
(„Muster Heizungsbau GmbH"), erfundene Adressen. Etwas Mehraufwand, null Risiko.

---

## PFLICHT-CHECK

```bash
git remote -v && git branch --show-current
```

---

## PROMPT FÜR CLAUDE CODE

```
Führe zuerst aus: git remote -v && git branch --show-current
Erwartet: origin = nachhaltika-arch/Claude-Code, branch = staging
Bei Abweichung: stoppe und melde.

WICHTIGER HINWEIS
Die hier erzeugten Texte sind Entwuerfe zur anwaltlichen Pruefung, keine
fertigen Rechtstexte. Kennzeichne jede Datei im Kopf mit:
"ENTWURF - vor Veroeffentlichung anwaltlich pruefen lassen. Stand: 2026-08-14"

SCHRITT 1 — Rechtstexte fuer die Landingpage
Lege an: landing-buch/recht/impressum.html, datenschutz.html,
widerruf.html, agb.html
Alle im selben Design wie index.html, mit Zurueck-Link.

impressum.html
  Nach Paragraph 5 TMG: KOMPAGNON communications BP GmbH, Koblenz,
  vertretungsberechtigte Person, Registergericht und HRB, USt-IdNr.,
  Kontaktdaten inkl. Telefon und E-Mail, Verantwortlicher fuer den Inhalt.
  Platzhalter in doppelten geschweiften Klammern fuer alles, was du nicht kennst -
  erfinde KEINE Registernummern.
  Zusaetzlich: Hinweis auf die EU-Streitschlichtungsplattform und die Erklaerung,
  ob zur Teilnahme an Verbraucherschlichtung bereit.

datenschutz.html
  Verantwortlicher, Rechtsgrundlagen, Hosting durch Netlify (Drittlandtransfer USA,
  Standardvertragsklauseln), Verarbeitung bei Bestellung, Zahlungsabwicklung ueber
  Stripe, E-Mail-Versand ueber Brevo, Speicherdauer, Betroffenenrechte,
  Beschwerderecht bei der Aufsichtsbehoerde.
  Wichtig: KEINE Cookies und KEIN Tracking erwaehnen, solange die Seite keine
  einsetzt - eine Datenschutzerklaerung, die nicht zur Realitaet passt, ist
  selbst ein Mangel.

widerruf.html
  Gesetzliches Muster der Widerrufsbelehrung, angepasst fuer zwei Faelle:
  a) Warenlieferung (gedrucktes Buch): 14 Tage ab Erhalt, Muster-Widerrufsformular
  b) Digitale Inhalte (PDF): Hinweis auf vorzeitiges Erloeschen nach
     Paragraph 356 Abs. 5 BGB
  Muster-Widerrufsformular als eigener, abtrennbarer Abschnitt.

agb.html
  Geltungsbereich, Vertragsschluss, Preise und Versand, Zahlung, Lieferzeit
  (7-12 Werktage bei Print), Eigentumsvorbehalt, Nutzungsrechte am PDF
  (einfaches, nicht uebertragbares Nutzungsrecht fuer den Kaeufer;
  Weitergabe und Vervielfaeltigung untersagt), Haftung, Gewaehrleistung,
  Schlussbestimmungen.

SCHRITT 2 — Verlinkung pruefen
Alle vier Seiten muessen im Footer von index.html UND danke.html verlinkt sein,
und die Widerrufsbelehrung zusaetzlich direkt im Checkout-Formular.
Zeige mir die Fundstellen:
grep -n "impressum\|datenschutz\|widerruf\|agb" landing-buch/*.html

SCHRITT 3 — Buch-Titelei
Schreibe buch/manuskript/00-titelei.md mit:
  - Schmutztitel
  - Haupttitel mit Untertitel und Versionsangabe
  - Impressumsseite: Autor, Verlag KOMPAGNON communications BP GmbH,
    Anschrift, ISBN-Platzhalter {{ISBN}}, Auflage, Erscheinungsjahr,
    Herstellungshinweis "Herstellung und Verlag: BoD - Books on Demand,
    Norderstedt", Copyright-Vermerk
  - Haftungsausschluss (eigene Seite, gut sichtbar):
    Das Buch vermittelt allgemeine Informationen und stellt keine Rechtsberatung
    im Einzelfall dar. Rechtsstand August 2026. Fuer die Anwendung im konkreten
    Fall anwaltliche Beratung empfohlen. Keine Haftung fuer Aktualitaet und
    Vollstaendigkeit.
  - Inhaltsverzeichnis-Platzhalter {{TOC}}

SCHRITT 4 — Kapitel-Disclaimer
Ergaenze in buch/layout/print.css und screen.css eine Klasse .rechtshinweis
(kleiner Kasten, --kc-mid Randlinie links, 9pt) und dokumentiere in
buch/README.md, dass jedes Rechtskapitel (03, 06) damit beginnen muss.

SCHRITT 5
git add -A
git commit -m "Add legal pages for book landing page and book front matter"
git push origin staging
```

---

## DEINE MANUELLEN AUFGABEN (nicht delegierbar)

| Aufgabe | Wann | Aufwand |
|---|---|---|
| Alle vier Rechtstexte anwaltlich prüfen lassen | vor Live-Gang | 1 Termin |
| BoD-Konto anlegen, ISBN beantragen | vor Drucklegung | 1 Std |
| ISBN in `00-titelei.md` eintragen, PDF neu bauen | nach ISBN-Erhalt | 10 Min |
| 2 Pflichtexemplare an DNB senden | nach Erscheinen | 30 Min |
| 1 Exemplar an Landesbibliothek Koblenz | nach Erscheinen | 15 Min |
| Stripe-Rechnungsangaben vervollständigen | vor erstem Verkauf | 20 Min |

**Zur anwaltlichen Prüfung:** Ein Termin für alle vier Texte plus die Frage nach der
RDG-Grenze im Buch kostet erfahrungsgemäß 400–800 €. Gemessen daran, dass das Buch dein
Autoritätsnachweis gegenüber der Handwerkskammer werden soll, ist das gut investiert.

---

## VERIFIKATION

| Prüfung | Erwartung |
|---|---|
| `grep` aus Schritt 2 | Treffer in **beiden** HTML-Dateien |
| Landingpage im Browser, Footer | vier Links, alle funktionieren |
| Checkout-Formular | Widerrufs-Checkbox vorhanden und **erzwungen** |
| Formular ohne Checkbox absenden | Meldung erscheint, kein Absenden |
| Preisangaben auf der Seite | überall „inkl. MwSt.", Versand separat genannt |

---

## COMMIT-MESSAGE

```
Add legal pages for book landing page and book front matter
```

---

## ZWEI SCHRITTE VORAUS

- **Der Rechtsstand veraltet.** „Stand: August 2026" muss im Buch stehen — und in
  spätestens 18 Monaten brauchst du eine geprüfte Neuauflage. Setze dir dafür jetzt eine
  Erinnerung; ein Fachbuch mit veraltetem Rechtsstand im Umlauf ist ein echtes Risiko.
- **Das Buch macht dich angreifbarer.** Sobald du als Autorität auftrittst, prüfen
  Mitbewerber deine eigene Seite. Lass sowohl die Landingpage als auch
  `kompagnon-frontend.onrender.com` durch dein eigenes Audit laufen und behebe alles unter
  85 Punkten, bevor das Buch erscheint.
- **Die Handwerkskammer-Schiene profitiert direkt.** Für die ISB-158/IMPULS-Beratung
  brauchst du eine Kammerempfehlung. Ein Buch mit ISBN, DNB-Eintrag und sauberem
  Verlagsimpressum ist genau die Art von Nachweis, die dort zählt. Deshalb lohnt sich der
  formale Aufwand doppelt.
