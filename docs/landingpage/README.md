# Die Landingpage von websprint.kompagnon.eu

`websprint-landingpage.html` ist die Datei, die bei Mittwald liegt — mit
dem Messblock darin. Sie ist der **erste** Schritt des Trichters und der
einzige, der nicht aus diesem Repo ausgeliefert wird.

## Warum sie hier liegt

Die Seite hat keine versionierte Quelle (L-20). Sie ist ein gebündelter
Export: ein HTML-Gerüst mit einer JSON-Ablage für die Bilder und der
Seitenvorlage als eingebettete Zeichenkette. Wer sie ändert, ändert diese
Datei — es gibt kein Projekt, aus dem sie neu erzeugt würde.

Bis zum 10.09.2026 lag die fertige Fassung nur im Zwischenspeicher einer
Sitzung. Zwischenspeicher werden geleert. Eine Datei, die von Hand
hochgeladen werden muss und die es nur einmal gibt, gehört an einen Ort,
der einen Verlauf hat.

**Was hier liegt, ist nicht automatisch live.** Diese Datei wird von Hand
zu Mittwald hochgeladen. Ändert jemand sie hier, ändert sich draußen
nichts, bis jemand sie hochlädt — und umgekehrt: Wer draußen etwas
ändert, ohne es hier nachzuziehen, hat zwei Fassungen.

## Was der Messblock tut

Er steht am Ende der Datei und ist absichtlich eigenständig — er ändert
nichts am vorhandenen Einwilligungs-Skript, sondern liest dessen Ergebnis.
Der ausführliche Kommentar dazu steht in
`kompagnon/frontend/public/embed/README.md`.

Kurz:

| | |
|---|---|
| Meta-Pixel | `1363198722345965`, lädt **nur** nach Zustimmung zu `c.marketing` |
| Einwilligung | gelesen aus `localStorage['kpg-consent-v1']`, Änderungen über einen `MutationObserver` auf dem Banner |
| Herkunft | `fbclid` und `_fbp` werden an das Widget durchgereicht, vorhandene Parameter bleiben erhalten |
| Abschluss | auf `kpg-audit-lead` folgt `fbq('track','Lead')` mit `eventID` und `gtag('event','generate_lead')` |

Die `eventID` ist der Grund, warum der Serverweg (Meta CAPI) und der
Browserweg dasselbe Ereignis nicht doppelt zählen.

## Vorschau

    python3 scripts/trichter-vorschau.py

Zeigt diese Datei als Schritt 1 neben Widget, Teaser, Berichtsseite und
den drei Mails — ohne Deploy.

## Was die Vorschau **nicht** zeigt

Ob der Messblock draußen wirklich misst. Das steht erst fest, wenn die
Datei hochgeladen ist und Meta einen Seitenaufruf sieht. Die Vorschau
zeigt Oberflächen, keine Abläufe.
