# BUCH-02 — Kapitelinhalte schreiben

## Warum dieser Schritt

Jetzt entsteht der eigentliche Text. 12 Kapitel plus Anhang, Ziel 150–200 Seiten.

**Wichtiger Grundsatz:** Wir schreiben nicht 200 Seiten am Stück. Wir schreiben **ein
Kapitel pro Durchgang**, prüfen es, und gehen dann weiter. Der Grund ist technisch: Bei
langen Generierungen bricht die Ausgabe ab, ohne dass ein Fehler erscheint — der Text
hört einfach mittendrin auf. Das ist genau die Art stiller Fehler, die dich sonst
Stunden kostet.

---

## Buchaufbau (verbindlich)

| # | Kapitel | Seiten | Inhalt |
|---|---|---|---|
| — | Titelei | 4 | Titel, Impressum, Disclaimer, Inhalt |
| 1 | Warum Ihre Website kein Prospekt ist | 12 | Marktlage Handwerk, Zahlen, Kosten schlechter Sichtbarkeit |
| 2 | Der Homepage Standard: Wie 100 Punkte entstehen | 12 | Das System, 6 Kategorien, 5 Stufen, Methodik |
| 3 | Rechtliche Compliance (30 Punkte) | 26 | Impressum, Datenschutz, Cookie, AGB |
| 4 | Technische Performance (20 Punkte) | 18 | Ladezeit, Mobile, Core Web Vitals |
| 5 | Barrierefreiheit (20 Punkte) | 18 | WCAG AA, Kontrast, Tastatur, BFSG |
| 6 | Sicherheit & Datenschutz (15 Punkte) | 14 | SSL, Header, Drittanbieter, Formulare |
| 7 | SEO & Sichtbarkeit (10 Punkte) | 14 | Technisches SEO, Schema.org, lokale Sichtbarkeit |
| 8 | Inhalt & Nutzererfahrung (5 Punkte) | 12 | Erstindruck, CTA, Navigation, Vertrauen |
| 9 | Der Selbsttest in 90 Minuten | 14 | Ausfüllbare Checkliste, Punktevergabe |
| 10 | Die 20 häufigsten Fehler | 12 | Konkrete Negativbeispiele aus Audits |
| 11 | Vom Bronze zum Gold: 30-Tage-Plan | 12 | Priorisierte Maßnahmen nach Aufwand/Wirkung |
| 12 | Wann Selbermachen sich nicht lohnt | 8 | Ehrliche Grenzen + Ausblick KI-Suche/GEO |
| A | Anhang: Glossar, Punktetabelle, Vorlagen | 12 | Nachschlagewerk |

**Summe ca. 198 Seiten.** Die Kapitel 3–8 sind das Herzstück: Sie folgen exakt der
Struktur des Audits. Der Leser kann seinen Score-Bericht daneben legen und Zeile für
Zeile mitlesen.

---

## Einheitliche Kapitelstruktur (Kapitel 3–8)

Jedes Kategoriekapitel folgt demselben Aufbau. Das ist kein Schema-F, sondern
Nutzerführung — der Leser lernt die Struktur einmal und findet sich danach überall zurecht.

1. **Was hier bewertet wird** (½ Seite) — Kategorie, Punktzahl, warum sie so gewichtet ist
2. **Der Praxisfall** (1 Seite) — anonymisiertes Beispiel eines Handwerksbetriebs
3. **Die Einzelkriterien** (je 2–4 Seiten) — pro Kriterium:
   - Was verlangt wird (mit Rechts- oder Normbezug)
   - Wie Sie es in 5 Minuten selbst prüfen
   - Was passiert, wenn es fehlt (konkret: Abmahnrisiko, Rankingverlust, Absprünge)
   - Wie Sie es beheben — mit Aufwandsangabe (Minuten/Stunden/Fachbetrieb)
4. **Punkteübersicht der Kategorie** (1 Seite) — Tabelle zum Selbsteintragen
5. **Häufige Irrtümer** (1 Seite)

---

## PFLICHT-CHECK

```bash
git remote -v && git branch --show-current
npm run check:standard
```

---

## PROMPT-VORLAGE (pro Kapitel einmal ausführen)

Ersetze `{{N}}`, `{{DATEI}}`, `{{TITEL}}`, `{{PUNKTE}}`, `{{SEITEN}}` und den Kapitel-Brief.

```
Führe zuerst aus: git remote -v && git branch --show-current
Erwartet: origin = nachhaltika-arch/Claude-Code, branch = staging
Bei Abweichung: stoppe und melde.

KONTEXT
Lies shared/homepage-standard.json vollstaendig. Alle Punktzahlen, Kriterien und
Gesetzesbezuege im Kapitel MUESSEN exakt dieser Datei entsprechen. Erfinde keine
Kriterien und aendere keine Punktzahlen.

AUFGABE
Schreibe das Kapitel {{N}} "{{TITEL}}" in die Datei buch/manuskript/{{DATEI}}.

ZIELGRUPPE
Inhaber eines deutschen Handwerksbetriebs, 40-60 Jahre, 3-25 Mitarbeiter.
Technisch nicht versiert, aber unternehmerisch erfahren. Er hat wenig Zeit und wenig
Geduld fuer Fachjargon. Er will wissen: Was kostet mich das, wenn ich es ignoriere?

TONALITAET
- Sie-Form, sachlich, respektvoll, ohne Anbiederung
- Keine Marketing-Superlative, keine Ausrufezeichen
- Jeder Fachbegriff wird bei Erstnennung in einem Halbsatz erklaert
- Konkrete Zahlen statt vager Behauptungen
- Keine Drohkulisse, aber klare Benennung realer Risiken

UMFANG
Ca. {{SEITEN}} Buchseiten, das entspricht ca. {{SEITEN}}*350 Woertern.
Schreibe das Kapitel VOLLSTAENDIG aus. Keine Platzhalter, keine Auslassungen,
kein "[hier weitere Beispiele]".

AUFBAU
{{KAPITEL-BRIEF — siehe Tabelle unten}}

RECHTLICHE SCHRANKE (zwingend)
Formuliere niemals eine einzelfallbezogene Rechtsempfehlung. Zulaessig:
"Das Telemediengesetz verlangt in Paragraph 5 folgende Angaben ..."
Unzulaessig:
"In Ihrem Fall genuegt es, wenn Sie ..."
Bei jedem Rechtsthema ein Satz, der auf anwaltliche Pruefung im Einzelfall verweist.

FORMAT
Markdown. Ueberschriften ab Ebene 2 (##). Tabellen als Markdown-Tabellen.
Kein HTML. Behalte den YAML-Frontmatter-Kopf der Datei bei und setze status: entwurf-fertig.

NACH DEM SCHREIBEN
Zaehle die Woerter und melde: "Kapitel {{N}}: X Woerter, ca. Y Seiten"
git add buch/manuskript/{{DATEI}}
git commit -m "Add book chapter {{N}}: {{TITEL}}"
git push origin staging
```

---

## Kapitel-Briefs (in diese Vorlage einsetzen)

**Kapitel 1 — `01-warum.md`, 12 Seiten**
> Einstieg über die Realität: Der Handwerker hat volle Auftragsbücher und fragt sich,
> warum er eine Website braucht. Antwort in drei Ebenen: (1) Fachkräftegewinnung — Bewerber
> prüfen den Betrieb online, bevor sie sich bewerben. (2) Auftragsqualität — nicht mehr
> Anfragen, sondern bessere. (3) Rechtliche Pflicht — die Website ist kein Marketing,
> sondern ein Impressumspflichtiges Medium. Danach: Was eine Website 2026 leisten muss,
> die es 2015 nicht musste (Mobile-First, KI-Suche, Barrierefreiheit). Abschluss: Ankündigung
> des Bewertungssystems.

**Kapitel 2 — `02-das-system.md`, 12 Seiten**
> Erklärung des Homepage Standards als Messsystem. Warum 100 Punkte, warum diese
> Gewichtung. Die 6 Kategorien im Überblick mit Begründung der Punkteverteilung
> (Recht 30, weil es das einzige mit direktem finanziellen Risiko ist). Die 5 Stufen mit
> Beschreibung, was eine Website auf dieser Stufe für den Betrieb bedeutet. Wie der Test
> durchgeführt wird. Was das System NICHT bewertet (Design-Geschmack, Textqualität im
> Detail) und warum diese Ehrlichkeit wichtig ist.

**Kapitel 3 — `03-recht.md`, 26 Seiten, 30 Punkte**
> Kriterien aus `shared/homepage-standard.json`: rc_impressum (6), rc_datenschutz (6),
> rc_cookie (6), rc_ecommerce (3) und die weiteren aus der Datei. Pro Kriterium: die
> Norm (TMG §5, DSGVO Art. 13, TDDDG §25, BGB §355), was konkret auf der Seite stehen
> muss, Selbstprüfung, Risiko bei Fehlen (Abmahnkosten realistisch beziffern), Behebung.
> Ein eigener Abschnitt zu Google Fonts: Warum das Nachladen von Google-Servern in
> Deutschland abgemahnt wurde und wie lokale Einbindung funktioniert.

**Kapitel 4 — `04-performance.md`, 18 Seiten, 20 Punkte**
> Kriterien tp_lcp, tp_mobile und weitere aus der Datei. Core Web Vitals in
> Handwerker-Sprache übersetzt: LCP = wann sieht der Besucher etwas, CLS = springt die
> Seite. Warum 3 Sekunden die Schmerzgrenze sind. Die häufigsten Ursachen bei
> Handwerker-Seiten: unkomprimierte Handy-Fotos vom Baustellenbesuch, Baukasten-Systeme
> mit zu viel Ballast. Selbstprüfung mit PageSpeed Insights, Schritt für Schritt mit
> Screenshots-Platzhaltern.

**Kapitel 5 — `05-barrierefreiheit.md`, 18 Seiten, 20 Punkte**
> Kriterien bf_kontrast, bf_tastatur, bf_screenreader, bf_lesbarkeit (je 5).
> WICHTIG UND EHRLICH: Das Barrierefreiheitsstärkungsgesetz gilt seit 28.06.2025, aber
> Kleinstunternehmen (unter 10 Mitarbeiter UND unter 2 Mio. € Jahresumsatz) sind bei
> Dienstleistungen ausgenommen. Das muss klar drin stehen, sonst ist das Buch unseriös.
> Begründe stattdessen die 20 Punkte anders: Barrierefreiheit ist gleichzeitig
> Bedienbarkeit für 60-jährige Kunden, Google-Ranking-Faktor und Zukunftssicherheit bei
> Betriebswachstum. Kontrastprüfung, Tastaturbedienung und Alt-Texte praktisch erklärt.

**Kapitel 6 — `06-sicherheit.md`, 14 Seiten, 15 Punkte**
> si_ssl (4), si_header (4), si_drittanbieter (4), si_formulare (3). HTTPS als Minimum,
> was ein Schloss-Symbol wirklich bedeutet. Security-Header verständlich erklärt (HSTS =
> Browser merkt sich, dass nur verschlüsselt zu sprechen ist). DSGVO-Drittanbieter:
> Google Maps, YouTube-Einbettungen, Schriftarten — die drei häufigsten Fallen.
> Formularsicherheit: Wo landen die Daten aus dem Kontaktformular?

**Kapitel 7 — `07-seo.md`, 14 Seiten, 10 Punkte**
> se_seo (4), se_schema (3), se_lokal (3). Technisches SEO auf das Nötigste reduziert:
> eine H1, Meta-Title, Meta-Description. Schema.org als „Übersetzung für Maschinen",
> speziell LocalBusiness. NAP-Konsistenz (Name, Adresse, Telefon) über Website, Google
> Business Profil und Impressum — der meistunterschätzte Local-Ranking-Faktor. Kurzer
> Vorgriff auf KI-Suche (wird in Kapitel 12 vertieft).

**Kapitel 8 — `08-ux.md`, 12 Seiten, 5 Punkte**
> ux_erstindruck, ux_cta, ux_navigation, ux_vertrauen, ux_content, ux_kontakt (je 1).
> Die 3-Sekunden-Regel. Ein Hauptziel pro Seite. Telefonnummer als klickbarer Link auf
> dem Handy — banal, aber bei der Mehrheit der geprüften Seiten falsch umgesetzt.
> Vertrauenssignale, die im Handwerk wirken: Innungsmitgliedschaft, Meisterbrief,
> Herstellerpartnerschaften, echte Bewertungen mit Namen.

**Kapitel 9 — `09-selbsttest.md`, 14 Seiten**
> Vollständige ausfüllbare Checkliste, exakt aus `shared/homepage-standard.json`
> generiert. Jedes Kriterium als Zeile: Kriterium, wie prüfen, max. Punkte, erreichte
> Punkte (leer zum Eintragen). Am Ende: Summenfeld und Stufenzuordnung. Zeitangabe
> 90 Minuten realistisch aufgeteilt.

**Kapitel 10 — `10-top20-fehler.md`, 12 Seiten**
> 20 konkrete Fehler, je etwa eine halbe Seite: Fehler, warum er passiert, was er kostet,
> Behebung in einem Satz. Aus echten Audit-Mustern: fehlendes Impressum im Footer der
> Unterseiten, Cookie-Banner ohne Ablehnen-Button, Telefonnummer als Bild, PDF-Preisliste
> statt Seiteninhalt, Kontaktformular ohne Datenschutzhinweis, Startseiten-Slider mit 8 MB.

**Kapitel 11 — `11-massnahmenplan.md`, 12 Seiten**
> Maßnahmen priorisiert nach Wirkung pro Aufwand. Woche 1: rechtliche Blocker (höchstes
> Risiko, geringster Aufwand). Woche 2: Technik/Ladezeit. Woche 3: Sichtbarkeit. Woche 4:
> Inhalt und Vertrauen. Je Maßnahme: Punktegewinn, Zeitaufwand, ob selbst machbar oder
> Fachbetrieb nötig.

**Kapitel 12 — `12-grenzen-des-selbermachens.md`, 8 Seiten**
> Ehrlich: Welche Punkte sind realistisch selbst erreichbar (Bronze → Silber, meist ja),
> welche nicht (Platin praktisch nie ohne Fachbetrieb). Rechenbeispiel Eigenzeit vs.
> Fremdkosten. Ausblick: KI-gestützte Suche verändert gerade, wie Betriebe gefunden
> werden — llms.txt, strukturierte Daten, zitierfähige Inhalte. Abschluss mit Verweis
> auf das kostenlose Audit (QR-Code-Platzhalter `{{QR_AUDIT}}`).

---

## VERIFIKATION

Nach jedem Kapitel:

```bash
wc -w buch/manuskript/<datei>.md
grep -c "^##" buch/manuskript/<datei>.md
npm run check:standard
```

**Prüfe selbst:** Bricht der Text mitten im Satz ab? Fehlen Kriterien, die in
`homepage-standard.json` stehen? Dann Kapitel neu generieren lassen — nicht flicken.

---

## ZWEI SCHRITTE VORAUS

- **Kapitel 9 sollte automatisch generiert werden**, nicht von Hand geschrieben. Wenn die
  Checkliste aus `homepage-standard.json` erzeugt wird, kann sie bei einer Standard-Änderung
  nicht veralten. Das ist ein kleiner Zusatzaufwand jetzt und spart die 2. Auflage.
- **Kapitel 5 ist dein Reputationsrisiko.** Wenn du 20 von 100 Punkten für Barrierefreiheit
  vergibst und der Leser herausfindet, dass er als Kleinstunternehmer gesetzlich befreit
  ist, verlierst du ihn. Die ehrliche Einordnung im Kapitel ist Pflicht — und sie macht
  dich glaubwürdiger als jeder Mitbewerber, der das verschweigt.
- **Bilder und Screenshots fehlen noch.** Plane pro Kategoriekapitel 3–5 Abbildungen ein.
  Bei 150–200 Seiten sind das ~30 Abbildungen, die vor dem Druck vorliegen müssen.
