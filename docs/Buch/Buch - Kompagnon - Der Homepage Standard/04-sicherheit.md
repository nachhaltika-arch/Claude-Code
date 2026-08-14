---
kapitel: 4
titel: "Sicherheit & Datenschutz"
punkte: 10
kriterien: 4
status: entwurf-fertig
zuletzt_geprueft: 2026-08-14
standard_version: "2026.2"
---

# 4. Sicherheit & Datenschutz — 10 Punkte

> **Rechtshinweis**
> Dieses Kapitel vermittelt allgemeine Informationen mit Stand August 2026 und stellt
> keine Rechtsberatung im Einzelfall dar. Insbesondere die Ausführungen zur Übermittlung
> von Daten in Länder außerhalb der EU beschreiben eine Rechtslage, die sich in den
> vergangenen Jahren mehrfach geändert hat. Lassen Sie Ihre konkrete Situation prüfen.

---

## 4.1 Was hier bewertet wird

Vier Kriterien, zusammen 10 Punkte.

| Code | Kriterium | Punkte |
|---|---|---|
| S1 | Verschlüsselungszertifikat gültig | 3 |
| S2 | Unverschlüsselte Aufrufe werden umgeleitet | 2 |
| S3 | Sicherheitsheader gesetzt | 3 |
| S4 | Keine Drittanbieter ohne Einwilligung | 2 |

Diese Kategorie ist die technisch eindeutigste des ganzen Standards. Alle vier Kriterien
lassen sich vollständig und ohne Ermessensspielraum messen: Ein Zertifikat ist gültig oder
nicht. Ein Header ist gesetzt oder nicht. Eine Verbindung wird aufgebaut oder nicht. Es
gibt hier nichts zu diskutieren und nichts zu schätzen.

Trotzdem stehen nur 10 Punkte darauf. Der Grund liegt in Grundsatz 2 aus Kapitel 2: Für die
Kundengewinnung ist diese Kategorie nur mittelbar relevant. Ein Besucher bemerkt ein
abgelaufenes Zertifikat sofort — der Browser stellt sich ihm mit einer roten Warnseite in
den Weg. Einen fehlenden Sicherheitsheader bemerkt er nie.

### Die Abgrenzung zu Kapitel 3

Zwei Kriterien dieses Buches prüfen dieselbe Messung aus zwei verschiedenen Blickwinkeln,
und das sollte klar sein, bevor Sie weiterlesen:

| | Frage | Kriterium |
|---|---|---|
| **Kapitel 3, L3** | Wird ordentlich um Einwilligung gebeten, und wird vor der Antwort schon geladen? | Der **Vorgang** |
| **Kapitel 4, S4** | Welche fremden Server werden tatsächlich kontaktiert, und wohin fließen die Daten? | Der **Zustand** |

Ein Beispiel macht den Unterschied deutlich. Eine Website ohne jeden Fremddienst braucht
keinen Einwilligungsdialog — sie bekommt bei L3 die volle Punktzahl **und** bei S4 die
volle Punktzahl. Eine Website mit vorbildlichem Dialog, die aber trotzdem eine Schriftart
sofort nachlädt, verliert bei beiden. Und eine Website mit vielen Fremddiensten, die alle
sauber erst nach Einwilligung laden, bekommt bei L3 die volle Punktzahl, bei S4 aber
Abzüge — weil der Datenabfluss dann zwar erlaubt, aber eben vorhanden ist.

---

## 4.2 Der Praxisfall

Der Elektrobetrieb aus Kapitel 2, 14 Mitarbeiter, Klasse K1. Im Frühjahr passierte
Folgendes.

Das Verschlüsselungszertifikat der Website lief ab. Die automatische Verlängerung war
Monate zuvor stillschweigend fehlgeschlagen — eine Konfigurationsänderung beim Hoster, von
der niemand etwas mitbekam. Es gab keine Warnmeldung, keine E-Mail, keinen Hinweis im
Verwaltungsbereich.

Was Besucher ab diesem Tag sahen, war keine Website, sondern eine ganzseitige Warnung
ihres Browsers: *Die Verbindung ist nicht sicher.* Darunter ein Knopf zum Zurückgehen und,
gut versteckt, einer zum Fortfahren. Wer nicht technisch versiert ist, geht zurück.

Elf Tage lang war die Website faktisch nicht erreichbar. Der Inhaber erfuhr davon, weil ein
Stammkunde ihn beiläufig darauf ansprach. In der Zwischenzeit gab es keine einzige Anfrage
über das Kontaktformular — was niemandem auffiel, weil es an manchen Tagen ohnehin keine
gibt.

Beim heutigen Audit erreicht der Betrieb in dieser Kategorie 8 von 10 Punkten: Zertifikat
gültig, Weiterleitung korrekt, keine Fremddienste vor Einwilligung. Was fehlt, sind die
Sicherheitsheader — von vier möglichen sind zwei gesetzt.

**Was dieser Fall zeigt:** Der Ausfall war nicht das Ergebnis eines Angriffs oder eines
Fehlers. Er war das Ergebnis davon, dass niemand hinsah. Genau dafür ist die jährliche
Prüfung da — und deshalb ist ein ungültiges Zertifikat ein Ausschlusskriterium und kein
Punktabzug.

---

## 4.3 S1 — Verschlüsselungszertifikat gültig · 3 Punkte

### Was verlangt wird

Wenn Sie in der Adresszeile Ihres Browsers ein Schloss sehen, bedeutet das: Die Verbindung
zwischen dem Besucher und Ihrem Server ist verschlüsselt. Niemand dazwischen kann
mitlesen, was übertragen wird — weder im WLAN eines Cafés noch beim Netzbetreiber.

Möglich wird das durch ein Zertifikat, das auf Ihrem Server liegt. Der Standard prüft vier
Dinge daran:

**Es muss gültig sein.** Zertifikate haben eine begrenzte Laufzeit. Die verbreiteten
kostenlosen Zertifikate laufen nach 90 Tagen ab und werden normalerweise automatisch
verlängert. „Normalerweise" ist hier das entscheidende Wort — siehe der Praxisfall oben.

**Es muss zu Ihrer Adresse passen.** Ein Zertifikat wird für bestimmte Adressen
ausgestellt. Der häufigste Fehler: Es gilt für `firma.de`, aber nicht für
`www.firma.de` — oder umgekehrt. Ruft jemand die falsche Variante auf, erscheint die
Warnseite. Da beide Schreibweisen im Umlauf sind, trifft das früher oder später jeden.

**Die Zertifikatskette muss vollständig sein.** Ein Zertifikat verweist auf ein
übergeordnetes, das auf ein weiteres verweist. Fehlt ein Glied dieser Kette, akzeptieren
manche Geräte das Zertifikat trotzdem und andere nicht. Das ist der tückischste Fall: Am
Bürorechner funktioniert alles, auf älteren Mobiltelefonen erscheint die Warnung. Sie
selbst sehen das Problem nie.

**Es darf keine unverschlüsselten Bestandteile geben.** Wenn eine verschlüsselte Seite ein
Bild oder ein Skript über eine unverschlüsselte Verbindung nachlädt, ist der Schutz
durchbrochen. Browser blockieren solche Inhalte teilweise oder entfernen das Schloss.

### So wird bewertet

| Punkte | Bedingung |
|---|---|
| **3** | Zertifikat gültig, passt zur aufgerufenen Adresse, Kette vollständig, keine unverschlüsselten Bestandteile |
| **2** | Gültig und passend, aber einzelne unverschlüsselte Bestandteile |
| **1** | Gültig, aber Kette unvollständig oder eine Adressvariante nicht abgedeckt |
| **0** | Abgelaufen, selbst ausgestellt, für eine andere Adresse ausgestellt oder gar nicht vorhanden → **Ausschlusskriterium: höchstens „Nicht konform"** |

### So prüfen Sie selbst — 5 Minuten

1. Rufen Sie Ihre Website auf. Ist ein Schloss in der Adresszeile? Klicken Sie darauf —
   der Browser zeigt Ihnen das Ablaufdatum.
2. Rufen Sie beide Varianten auf: einmal mit `www.` und einmal ohne. Funktionieren beide
   ohne Warnung?
3. Rufen Sie Ihre Website auf einem **Mobiltelefon** auf, möglichst einem älteren, und
   über Mobilfunk statt WLAN. Kommt dort dieselbe Seite ohne Warnung?
4. Notieren Sie sich das Ablaufdatum im Kalender, mit einer Erinnerung zwei Wochen vorher.

Punkt 4 ist der eigentliche Wert dieser Prüfung. Er verhindert genau den Fall aus 4.2.

### So beheben Sie es

Ein Zertifikat kostet heute nichts. Praktisch jeder Hoster bietet die automatische
Einrichtung an, meist mit einem einzigen Schalter im Verwaltungsbereich. Wenn Ihre Website
kein gültiges Zertifikat hat, ist das in aller Regel keine Kostenfrage, sondern eine, die
niemand gestellt hat.

Aufwand: eine halbe Stunde, in vielen Fällen fünf Minuten.

---

## 4.4 S2 — Unverschlüsselte Aufrufe werden umgeleitet · 2 Punkte

### Was verlangt wird

Ein gültiges Zertifikat nützt wenig, wenn die Seite auch unverschlüsselt erreichbar
bleibt. Denn nicht jeder tippt „https" davor. Und noch wichtiger: **Viele Verweise auf Ihre
Website stammen aus Quellen, die Sie nicht kontrollieren** — alte Branchenverzeichnisse,
gedruckte Visitenkarten, Einträge in Portalen, Verlinkungen von Partnern. Ein erheblicher
Teil davon zeigt noch auf die unverschlüsselte Adresse.

Der Server muss diese Aufrufe deshalb dauerhaft auf die verschlüsselte Variante umleiten,
und zwar automatisch und bevor irgendein Inhalt übertragen wird.

Der zugehörige Sicherheitsheader heißt HSTS und gehört zum nächsten Kriterium. Er sorgt
dafür, dass der Browser sich diese Umleitung merkt und beim nächsten Mal gar nicht erst
unverschlüsselt anfragt.

### So wird bewertet

| Punkte | Bedingung |
|---|---|
| **2** | Unverschlüsselte Aufrufe werden dauerhaft und automatisch umgeleitet, sowohl mit als auch ohne `www.` |
| **1** | Umleitung erfolgt, aber nur für eine Adressvariante, oder nur als vorübergehende Weiterleitung |
| **0** | Die Seite bleibt unverschlüsselt erreichbar |

### So prüfen Sie selbst — 2 Minuten

Tippen Sie in die Adresszeile `http://ihredomain.de` — ausdrücklich mit „http" und ohne
„s". Drücken Sie Enter. Springt die Adresse automatisch auf „https" um? Wiederholen Sie es
mit `http://www.ihredomain.de`.

Wenn eine der beiden Varianten unverschlüsselt geöffnet bleibt, haben Sie den Befund.

---

## 4.5 S3 — Sicherheitsheader · 3 Punkte

### Was verlangt wird

Wenn Ihr Server eine Seite ausliefert, schickt er zusammen mit dem Inhalt eine Reihe
technischer Anweisungen an den Browser mit. Diese Anweisungen heißen Header, und einige
davon sind Sicherheitsanweisungen. Sie sind für Besucher unsichtbar und für Angreifer
entscheidend.

Vier davon prüft der Standard:

**Strict-Transport-Security.** Weist den Browser an, sich zu merken, dass diese Website
ausschließlich verschlüsselt zu erreichen ist. Ab dem zweiten Besuch fragt der Browser
dann gar nicht mehr unverschlüsselt an — auch nicht, wenn jemand einen Link ohne „https"
untergeschoben hat.

**Content-Security-Policy.** Legt fest, aus welchen Quellen Inhalte geladen werden dürfen.
Schafft es jemand, ein fremdes Skript in Ihre Seite einzuschleusen, verhindert diese Regel,
dass es ausgeführt wird. Das ist der wirksamste, aber auch der aufwendigste der vier.

**X-Frame-Options.** Verhindert, dass Ihre Website unsichtbar in eine fremde Seite
eingebettet wird. Ohne diesen Header kann jemand Ihre Seite hinter einer eigenen
verstecken und Besucher dazu bringen, auf etwas zu klicken, das sie nicht sehen.

**X-Content-Type-Options.** Weist den Browser an, Dateien so zu behandeln, wie der Server
sie deklariert, statt selbst zu raten. Verhindert, dass eine harmlos aussehende Datei als
ausführbarer Code interpretiert wird.

### Warum das nicht „nur etwas für große Firmen" ist

Der häufigste Einwand lautet: *Ich habe doch nichts, was jemanden interessieren könnte.*
Das stimmt — und geht am Punkt vorbei.

Bei diesen Headern geht es nicht um Ihre Daten. Es geht darum, dass **Ihre Website nicht
zum Werkzeug gegen Ihre eigenen Besucher wird.** Kleine Unternehmensseiten sind für
automatisierte Angriffe gerade deshalb attraktiv, weil sie selten gepflegt werden. Ein
Angreifer interessiert sich nicht für Ihre Preisliste. Er interessiert sich für den
Vertrauensvorschuss, den Ihre Besucher Ihrer Adresse entgegenbringen.

### So wird bewertet

| Punkte | Bedingung |
|---|---|
| **3** | Alle vier Header gesetzt |
| **2** | Drei Header gesetzt |
| **1** | Zwei Header gesetzt |
| **0** | Höchstens ein Header gesetzt |

### So prüfen Sie selbst — 5 Minuten

Diese Prüfung können Sie nicht mit bloßem Auge machen, aber sie ist trotzdem einfach: Es
gibt kostenlose Prüfdienste im Netz, bei denen Sie Ihre Adresse eingeben und eine
Auswertung aller gesetzten Header bekommen. Suchen Sie nach „Security Header Check". Sie
erhalten eine Note und eine Liste dessen, was fehlt.

Für die Punktvergabe im Selbsttest zählen Sie einfach ab, wie viele der vier oben
genannten Header aufgeführt sind.

### So beheben Sie es

Drei der vier Header sind eine einzige Konfigurationszeile auf dem Server und in fünf
Minuten gesetzt. Der vierte — Content-Security-Policy — ist aufwendiger, weil er zu Ihrer
konkreten Website passen muss: Er muss alle Quellen erlauben, die Sie tatsächlich nutzen,
und alle anderen sperren. Setzt man ihn zu streng, funktionieren Teile der Seite nicht mehr.

**Praktische Empfehlung:** Lassen Sie die drei einfachen sofort setzen, das ist ein
Zehn-Minuten-Auftrag an Ihren Dienstleister und bringt Sie auf 2 von 3 Punkten. Die
Content-Security-Policy nehmen Sie beim nächsten größeren Eingriff an der Website mit.

---

## 4.6 S4 — Keine Drittanbieter ohne Einwilligung · 2 Punkte

### Was verlangt wird

Beim Aufruf Ihrer Startseite wird aufgezeichnet, welche fremden Server kontaktiert werden —
ohne dass irgendetwas angeklickt wurde. Jeder dieser Kontakte überträgt mindestens die
IP-Adresse Ihres Besuchers und Angaben zu seinem Gerät.

Typische Kandidaten in absteigender Häufigkeit: extern geladene Schriftarten, eingebettete
Kartenanwendungen, Videofenster, Statistikwerkzeuge, Bewertungsanzeigen, Chatfenster,
Schaltflächen sozialer Netzwerke, Buchungssysteme.

Bewertet wird zweierlei: **wie viele** solcher Verbindungen vor einer Einwilligung
aufgebaut werden, und **wohin** sie führen — innerhalb oder außerhalb der EU.

### Zur Rechtslage bei Übermittlungen in die USA

Hier ist Genauigkeit wichtig, weil zu diesem Thema viel Veraltetes im Umlauf ist.

Seit Juli 2023 gibt es einen Angemessenheitsbeschluss der Europäischen Kommission für
Übermittlungen an US-Unternehmen, die sich unter dem EU-US Data Privacy Framework
zertifiziert haben. Für diese Unternehmen ist die Übermittlung datenschutzrechtlich
zulässig, ohne dass zusätzliche Vertragskonstruktionen nötig wären. Das hat die Lage
gegenüber den Jahren davor deutlich entspannt.

**Was dadurch nicht entfällt, ist die Einwilligungspflicht.** Sie folgt aus einem anderen
Gesetz — dem Telekommunikation-Digitale-Dienste-Datenschutz-Gesetz — und knüpft nicht
daran an, wohin die Daten fließen, sondern daran, dass auf dem Gerät des Besuchers
gespeichert oder zugegriffen wird. Ein Statistikwerkzeug bleibt einwilligungspflichtig,
auch wenn sein Anbieter zertifiziert ist.

Kurz gefasst: Der Angemessenheitsbeschluss löst die Frage „darf ich die Daten dorthin
übermitteln?". Er löst nicht die Frage „darf ich es tun, bevor der Besucher zugestimmt
hat?".

### So wird bewertet

| Punkte | Bedingung |
|---|---|
| **2** | Vor einer Einwilligung werden keine fremden Server kontaktiert |
| **1** | Ein bis zwei Fremdverbindungen vor Einwilligung, ohne Übermittlung außerhalb der EU |
| **0** | Mehrere Fremdverbindungen vor Einwilligung oder Übermittlung außerhalb der EU vor Einwilligung |

**Ausschlusswirkung:** Werden Tracking-Dienste oder externe Schriftarten ohne Einwilligung
geladen, ist die höchste erreichbare Stufe **Bronze**. Diese Regel wirkt über L3 und S4
hinweg und wird nur einmal angewandt.

### So prüfen Sie selbst — 10 Minuten

Es ist dieselbe Prüfung wie in Abschnitt 3.5, mit einem anderen Blick auf das Ergebnis:

1. Privates Browserfenster öffnen, Ihre Startseite aufrufen, **nichts anklicken**.
2. Entwicklerwerkzeuge mit F12 öffnen, Reiter „Netzwerk", Seite neu laden.
3. Schauen Sie die Liste der kontaktierten Adressen durch. Alles, was nicht Ihre eigene
   Domain ist, ist ein Fremdkontakt.
4. Zählen Sie sie und notieren Sie sich die Namen.

Für Punkt 4 gilt: Sie müssen nicht wissen, was die einzelnen Dienste tun. Es genügt, die
Liste zu haben — sie ist gleichzeitig die Vorlage für die Prüfung Ihrer
Datenschutzerklärung aus Abschnitt 3.4.

### So beheben Sie es

| Fremddienst | Lösung | Aufwand |
|---|---|---|
| Externe Schriftart | Datei herunterladen, auf dem eigenen Server ablegen | 1 Stunde |
| Karte | Platzhalterbild, das erst nach Klick die echte Karte lädt | 1–2 Stunden |
| Video | Platzhalter mit Vorschaubild statt eingebettetem Fenster | 1 Stunde |
| Statistikwerkzeug | Hinter den Einwilligungsdialog legen oder auf eine Lösung wechseln, die auf dem eigenen Server läuft | 2–4 Stunden |
| Schaltflächen sozialer Netzwerke | Durch einfache Verweise ersetzen | 30 Minuten |

Die Schriftart ist fast immer der erste und lohnendste Schritt: eine Stunde Arbeit, ein
Ausschlusskriterium weniger, und die Seite lädt danach messbar schneller — was Ihnen in
Kapitel 5 zusätzliche Punkte bringt.

---

## 4.7 Ihre Punkte in dieser Kategorie

| Code | Kriterium | Max. | Ihre Punkte |
|---|---|---|---|
| S1 | Verschlüsselungszertifikat | 3 | ______ |
| S2 | Umleitung unverschlüsselter Aufrufe | 2 | ______ |
| S3 | Sicherheitsheader | 3 | ______ |
| S4 | Drittanbieter ohne Einwilligung | 2 | ______ |
| | **Summe** | **10** | **______** |

**Ausschlusskriterium ausgelöst?** ☐ nein ☐ ja, welches: ______________________

**Ihre Liste der Fremdkontakte** (aus 4.6, Schritt 4) — Sie brauchen sie in Kapitel 3
und in Kapitel 5:

______________________________________________________________________

---

## 4.8 Vier verbreitete Irrtümer

**„Ich habe das Schloss, also ist meine Website sicher."**
Das Schloss sagt genau eine Sache aus: Die Übertragung ist verschlüsselt. Es sagt nichts
darüber, ob die Website gepflegt ist, ob sie Fremddienste einbindet oder ob der Anbieter
vertrauenswürdig ist. Betrügerische Seiten haben ebenfalls ein Schloss — es ist kostenlos.

**„Sicherheitsheader brauche ich nicht, bei mir gibt es nichts zu holen."**
Es geht nicht um Ihre Daten. Es geht darum, dass Ihre Adresse nicht gegen Ihre Besucher
verwendet werden kann. Kleine, selten gepflegte Seiten sind für automatisierte Angriffe
attraktiver als große.

**„Um Sicherheit kümmert sich mein Hoster."**
Der Hoster liefert die Grundlage — Serverpflege, Zertifikatsverwaltung, Netzschutz. Was auf
Ihrer Website eingebunden ist und welche Header ausgeliefert werden, ist Ihre
Konfiguration. Fragen Sie im Zweifel schriftlich nach, wer wofür zuständig ist. Diese
Antwort ist auch für Ihre Datenschutzdokumentation nützlich.

**„Seit dem neuen EU-US-Abkommen ist die Sache mit den amerikanischen Diensten erledigt."**
Nur zur Hälfte. Der Angemessenheitsbeschluss von 2023 macht die Übermittlung an
zertifizierte Anbieter zulässig. Die Pflicht, vorher zu fragen, folgt aber aus einem
anderen Gesetz und bleibt unberührt. Wer einen zertifizierten Dienst ohne Einwilligung
lädt, hat das Übermittlungsproblem gelöst und das Einwilligungsproblem behalten.

---

> ### Das Wichtigste aus diesem Kapitel
>
> - **10 Punkte in vier Kriterien** — die technisch eindeutigste Kategorie des Standards,
>   ohne Ermessensspielraum.
> - Ein **ungültiges Zertifikat** ist ein Ausschlusskriterium. Prüfen Sie beide
>   Adressvarianten, mit und ohne `www.`, und einmal auf einem älteren Mobiltelefon.
> - **Tragen Sie das Ablaufdatum in Ihren Kalender ein.** Automatische Verlängerungen
>   scheitern lautlos, und Sie merken es als Letzter.
> - **Unverschlüsselte Aufrufe** müssen umgeleitet werden — viele Verweise auf Ihre Seite
>   stammen aus Quellen, die Sie nicht kontrollieren.
> - **Drei der vier Sicherheitsheader** sind in zehn Minuten gesetzt. Der vierte lohnt
>   sich beim nächsten größeren Eingriff.
> - **Extern geladene Schriftarten** sind der lohnendste Einzelfix des ganzen Buches: eine
>   Stunde Arbeit, ein Ausschlusskriterium weniger, dazu eine schnellere Seite.
> - Der EU-US-Angemessenheitsbeschluss löst die Übermittlungsfrage, **nicht** die
>   Einwilligungsfrage.

---

## Redaktionelle Anmerkungen (nicht drucken)

**Abgleich mit dem Code steht aus.** Kriterienzuschnitt und Punktzahlen (S1 3, S2 2, S3 3,
S4 2) stammen aus `audit-anforderungen-2026-08-11.md` § 3.2. Die Abstufungen innerhalb der
Kriterien sind konstruiert und gegen `audit_criteria.py` sowie `audit_collectors.check_tls`,
`check_https_redirect` und `detect_third_parties` abzugleichen.

**Offene Frage zur Doppelwertung.** L3 (Kapitel 3) und S4 (Kapitel 4) messen dieselben
Daten. Beide können Punkte kosten, und beide lösen dieselbe Bronze-Deckelung aus. Abschnitt
4.1 erklärt die Abgrenzung, und 4.6 stellt klar, dass die Deckelung nur einmal wirkt — das
muss im Code ebenso umgesetzt sein. **Zu prüfen:** Ob `BLOCKING_MAJOR` bei einem Befund,
der beide Kriterien betrifft, wirklich nur einmal greift.

**Zu bestätigen (anwaltlich, vor Drucklegung):**
1. Die Darstellung des EU-US Data Privacy Framework in 4.6 und im vierten Irrtum. Der
   Angemessenheitsbeschluss ist Gegenstand laufender rechtlicher Auseinandersetzungen; die
   Formulierung ist bewusst zurückhaltend gehalten, sollte aber vor Drucklegung auf
   Aktualität geprüft werden.
2. Ob die Abgrenzung „Übermittlungsfrage gegen Einwilligungsfrage" so tragfähig formuliert
   ist.

**Bewusst nicht genannt:** Namen konkreter Prüfdienste für Sicherheitsheader (4.5). Solche
Dienste verschwinden oder ändern ihren Umfang; eine allgemeine Suchanweisung veraltet
nicht. Falls doch ein Name gewünscht ist, gehört er in den Anhang, nicht in den Fließtext.

**Praxisfall 4.2** setzt Fall A aus Kapitel 2 fort (Elektrobetrieb, 8 von 10 Punkten in
dieser Kategorie). Die Zahlen sind mit Kapitel 2 abgestimmt: S1 3, S2 2, S3 1, S4 2. Nach
den ersten echten Läufen durch einen anonymisierten realen Fall ersetzen.

**Abbildungen (3 Stück):**
1. Die Browser-Warnseite bei ungültigem Zertifikat — selbst nachstellen, keine fremde Seite
   fotografieren. Das ist das Bild, das den Praxisfall trägt.
2. Schema der Zertifikatskette und wo sie reißen kann
3. Der Netzwerk-Reiter mit markierten Fremddomains, dieselbe Abbildung wie in Kapitel 3 —
   dort mit dem Blick auf die Einwilligung, hier mit dem Blick auf die Ziele. Prüfen, ob
   eine gemeinsame Abbildung mit zwei Beschriftungen ausreicht.
