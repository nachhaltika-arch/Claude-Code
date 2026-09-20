# Widersprüche zwischen den Dokumenten — was das System dazu sagt

**Stand 17.09.2026.** Der Vertriebsplan führt **17** Stellen auf, an denen
sich Projektdokumente widersprechen (Reiter *Widersprüche*, Punkt P1-18 im
Aktionsplan). Elf davon sind Entscheidungen — Budget, Preise, Reihenfolge,
Wortwahl — und gehören David.

**Sechs sind keine Entscheidungen, sondern Tatsachenfragen.** Bei ihnen hat
das laufende System eine Antwort, und die steht hier, damit niemand sie noch
einmal sucht. Jede Zeile nennt ihren Beleg.

> **Was diese Datei nicht kann.** Sie bereinigt die Quelldokumente nicht.
> Die meisten liegen im Claude-Projekt „KOMPAGNON KAS NEU", nicht in diesem
> Repo — ich kann sie weder lesen noch ändern. Was hier steht, ist die
> gemessene Wahrheit; wer ein Dokument berichtigt, schreibt sie dorthin ab.

---

## 3 — Ereignisname: „Analyse gestartet" oder „Analyse begonnen"?

**Es heißt „Analyse begonnen".** Fassung 4 nennt „Analyse gestartet", der
Code nicht.

| Fundstelle | |
|---|---|
| `frontend/public/embed/audit-widget.html:912` | „Analyse begonnen" — Weg A, Entscheidung David am 15.09.2026 |
| `backend/tests/test_analyse_begonnen.py` | prüft alle drei Fundstellen auf **denselben** Namen |

Der Test hält ausdrücklich fest, dass Widget, ausgelieferte Landingpage und
Einbauanleitung denselben Namen tragen müssen. Wer in einem Dokument
„gestartet" schreibt, bricht die Kette an einer Stelle, die kein Test sieht —
denn Dokumente prüft er nicht.

## 8 — Pixel-ID in der Sequenz

**Im Repo steht nur die richtige.** Die im Vertriebsplan genannte inaktive
Kennung `1099910707622652` kommt in diesem Repo **kein einziges Mal** vor —
gesucht in `*.py`, `*.md`, `*.html`, `*.js`. Produktiv meldet
`/api/widget/config` die Kennung `1363198722345965`.

Der Widerspruch betrifft damit ausschließlich ein Dokument außerhalb des
Repos. Hier ist nichts zu ändern; dort schon.

## 9 — Rollen: Vertrag gegen Code

**Der Code kennt vier Rollen, und keine heißt „Auditor".**

    ROLLEN = ("superadmin", "admin", "mitarbeiter", "kunde")   services/rollen.py:35
    ALTE_ROLLEN = {"auditor": "mitarbeiter", "nutzer": "mitarbeiter"}          :59

`auditor` und `nutzer` sind **abgelöste** Namen, die beim Anmelden auf
`mitarbeiter` abgebildet werden. AGB, AVV und Produktbild 06 nennen
Administrator / Auditor / Kunde — also eine Rolle, die es nicht mehr gibt,
und keine der beiden Rollen, die tatsächlich Innendienstrechte tragen
(`superadmin`, `admin`).

**Das bleibt ein Vertragsrisiko und ist hier nicht auflösbar:** Welche
Formulierung im Vertrag steht, entscheiden David und der Anwalt (P2-10,
P3-06). Gemessen ist nur, dass die Vertragsfassung den Code nicht
beschreibt.

## 10 — Stufen gegen Stränge

**Beide Zahlenreihen existieren, sie gehören nur zu verschiedenen Dingen.**

Die Bewertungsstufen stehen in `services/audit_katalog.py:445`:

| ab | Stufe |
|---|---|
| 95 | Website Standard Platin |
| 85 | Website Standard Gold |
| 70 | Website Standard Silber |
| 50 | Website Standard Bronze |
| 0 | Nicht konform |

Die AGB-Einbindung nennt „unter 70 / 70–84,4 / ab 84,5" als *Stufen*. Das
sind keine. **Und die Stränge, zu denen sie gehören sollen, gibt es im Code
nicht:** `services/sequence_runner.py` kennt weder das Wort noch eine
Verzweigung nach Punktzahl — die Sequenz hat drei Stufen und einen einzigen
Strang (siehe P1-05, offen).

Wer die AGB-Zahlen als Stufen liest, verspricht etwas anderes als das
System liefert.

## 11 — Produktstatus Check PLUS

**Live seit dem 13.09.2026, Abdeckung 96 %.** Produktiv an
`/api/widget/config` gemessen (17.09.): `check_plus.verfuegbar: true`,
Kaufadresse gesetzt, 249,00 € netto / 296,31 € brutto.

Die Redaktionsstrategie 1KG führt das Produkt noch als Entwurf und nennt
78 % Abdeckung. Beide Zahlen sind überholt; die 78 % stammten aus einem
Lauf vom 04.09., an dem die PageSpeed-Zeitgrenze noch bei 60 s lag.

**Was dabei offen bleibt** (L-187): Der Kaufweg läuft über einen
Stripe-Zahllink, der den Shop umgeht — keine Bestellung im System, kein
AGB-Nachweis, keine Anrechnung. `AGB_FASSUNG` ist produktiv leer.

## 17 — Absender-Befund

**Die Vermutung war falsch, der wahre Fehler liegt woanders — und er ist am
17.09.2026 gefunden worden.**

„Fremde Absenderidentität hartkodiert" trifft nicht zu: `noreply@kompagnon.group`
ist die eigene Domain, und die Antwortfähigkeit ist seit dem 27.08. über
`replyTo` gelöst (`services/brevo_mail.py:77`).

Der Fehler in `widget_crm.py` ist ein anderer und war bis heute unbelegt:
`uebertrage_anfrage` brach bei fehlender Listen-ID mit einem **blanken
`return`** ab, ohne Protokollzeile. An den Render-Protokollen gemessen:
Zwischen dem 03.09. und 13.09. haben **neun** Adressen bestätigt, darunter
zwei echte Interessenten — zu keiner einzigen steht eine Brevo-Zeile im
Protokoll, weder Erfolg noch Misserfolg. Genau diese doppelte Abwesenheit
ist die Signatur des stillen `return`.

**Daraus folgt:** `BREVO_LIST_VERIFIED_ID` und `BREVO_LIST_OPTIN_ID` sind
produktiv nicht gesetzt. Die Stelle warnt seit dem 17.09.; das Setzen der
Variablen liegt bei David.

---

## Die elf übrigen

Sie sind hier nicht aufgelöst, weil sie Entscheidungen verlangen und keine
Messung: **1** Budget und Laufzeit · **2** Doppelzählung und CAPI · **4**
Lead-Erwartung · **5** „103 Punkte" und Wortwahl · **6** Preise auf
LinkedIn · **7** UTM-Schema und Kampagnenname · **12** Beispiel Elektro
Hansen · **13** Buch (Seitenzahl) · **14** Reihenfolge der Themen · **15**
Branchenspiegel und Sprechstunde · **16** Newsletter.

Für einige liegt die Antwort im Vertriebsplan selbst („Es gilt Fassung 4",
„Es gilt der September-Plan") — sie sind entschieden, aber in den
Quelldokumenten nicht nachgetragen. Das ist Schreibarbeit an Dateien
außerhalb dieses Repos.
