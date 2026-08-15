---
name: resume_point_2026_08_12
description: "Wiederaufnahme 2026-08-12 — Widget-Pentest und DSGVO abgeschlossen, Bericht hinter Double-Opt-in; offen nur noch Live-Test durch David"
metadata: 
  node_type: memory
  type: project
  originSessionId: 7e2c88f9-9f53-4931-8502-eca89b9d7234
  modified: 2026-08-12T14:18:16.394Z
---

Arbeitsstand vom 2026-08-12. Vollständige Übergabe im Repo:
`docs/widget-stand-2026-08-12.md`.

Sechs Commits auf `staging` (`ef5aa6c`…`f9e8169`), Staging verifiziert.

**Pentest — vier Befunde behoben.** Der schwerste: `GET /api/widget/teaser/{id}`
lief auf der laufenden Nummer der Analyse und gab ohne Login jede Analyse der
Datenbank aus, auch die im Tool angelegten — also die Interessentenliste. Jetzt
`poll_token` pro Anfrage. Dazu: `CF-Connecting-IP` wurde vertraut, obwohl kein
Cloudflare davorsteht (IP-Grenzen frei umgehbar, jetzt an `TRUSTED_PROXY_HEADER`
gebunden); fehlende `X-Frame-Options`/`Referrer-Policy` auf Bericht- und
Bestätigungsseite; `javascript:` in `href` möglich.

**DSGVO — David hat Double-Opt-in vor dem Bericht gewählt.** Vorher ging der
fertige Bericht mit Punktzahl, Mängeln, PDF und Verkaufsknopf sofort an jede
eingetippte Adresse, auch an fremde — unbestellte Werbung nach § 7 UWG. Jetzt
sagt die erste Mail nur, dass etwas angefordert wurde; Bericht, PDF und Angebot
liegen hinter dem Klick aus dem Postfach. Der Klick wird als
`report_confirmed_at` festgehalten, die Anfragenliste zeigt „abgerufen" statt
nur „versendet".

**CI-Umstellung.** Widget, Mail und Bericht liefen auf drei verschiedenen
Paletten, keine davon die CI (`#0F2E2B`/`#F5C518` im Bericht, `#04293a`/
`#207a92` im Widget statt Pantone 3165/3135/3945). Jetzt einheitlich über
`backend/services/brand.py` als Gegenstück zu `tokens.css`. Grafisch
aufgefrischt: Bericht mit Score-Kopf und Bereichsbalken, E-Mail
tabellenbasiert wegen Outlook. **Bewusst keine Webschriften** — Google Fonts
würde die IP des Empfängers an Google geben und den DSGVO-Fortschritt
zurückdrehen.

**Echter Durchlauf verifiziert** (2026-08-12): Widget → Audit (kompagnon.eu,
65/100 Bronze) → Teaser → Brevo-Mail → Klick → Berichtsseite → PDF (82 KB) →
Double-Opt-in-Bestätigung. Dabei **toter Berichtslink gefunden**:
`api_base_url()` fiel ohne `API_BASE_URL` auf die Produktiv-Adresse zurück,
die Variable war im Staging-Blueprint nie deklariert — jeder Berichtslink von
Staging war tot. Jetzt über `RENDER_EXTERNAL_URL`, das Render selbst setzt.

**Brevo schreibt Links auf `sendibt3.com` um** (Klick-Tracking). Offen: im
Brevo-Konto abschalten — fremde Domain im Link schreckt genau die Empfänger
ab, die die Mail nicht angefordert haben.

**Zwei-Mail-Ablauf (David entschieden).** Erst Bestätigungsmail ohne jede
Angabe zur Website, nach dem Klick (`/api/widget/verify/{token}`,
`verified_at`) folgt Mail 2 mit dem Berichtslink. Marketing-Opt-in bleibt
getrennt in Mail 2 — zwei Einwilligungen an einem Klick wären Bündelung.

**PDF überarbeitet.** Vier echte Fehler gefunden (Punktzahl vom Level-Balken
überdeckt, Donut erfand „25 %"-Viertel ohne Keyword-Daten, Summenzeile lief
mit `level[:15]` aus der Tabelle, Protokoll-Kopfzeile dunkel auf dunkel).
Noto Sans liegt jetzt in `backend/assets/fonts/` (OFL dabei) — dabei fiel auf,
dass die Schrift **nie** die war, die im Code stand. `_clean_text` prüft jetzt
die Zeichenabdeckung und ersetzt Fehlendes (→ wird ->), wichtig weil
KI-Texte beliebige Zeichen enthalten können.

**Blocker gelöst: Double-Opt-in bestätigte sich selbst.** In vier Live-Läufen
kam die Berichts-Mail 15 s bis 4 min nach der Bestätigungsmail, ohne Klick —
Postfach-Dienste rufen Links ab UND schicken Formulare ab. GET→POST reichte
nicht. Jetzt verlangt das Formular einen Beleg echter Bedienung: verstecktes
Feld leer ausgeliefert, Wert im `data`-Attribut am Knopf, wandert erst bei
`pointerdown`/Tastendruck hinein, Server prüft per HMAC über den Token. Dazu
`verified_user_agent`/`verified_ip` als Nachweis. Live bewiesen (doi5): sieben
Minuten Ruhe, dann echter Klick → Mail 2 nach 40 Sekunden.

**Offen — braucht David:** Brevo-Klick-Tracking abschalten, in der
Anfragenliste prüfen ob der Eintrag auf „abgerufen" steht (brauchte
Admin-Zugang, den ich nicht habe), Einbau in die Ziel-Landingpage inkl.
Telefon. Danach `docs/audit-anforderungen-2026-08-11.md`.

Siehe [[migration_trap_main_py]] — hat heute Zeit gekostet. Weiter
[[feedback_pr_only_fridays]]: PR nach `main` erst freitags.
