/**
 * AGB und Widerrufsbelehrung — die eine Datei, die David pflegt (ORDERS_05).
 *
 * **Warum hier und nicht im JSX.** Entscheidung David, 29.08.2026: „füge eine
 * Vorlage ein, die ich später ergänzen kann oder austauschen". Wer einen
 * Rechtstext einsetzt, soll Text bearbeiten und kein React — und wer ihn
 * gegen die Fassung der Kanzlei austauscht, ersetzt einen Abschnitt, keine
 * Seite. `pages/AGB.jsx` und `pages/Widerrufsbelehrung.jsx` stellen nur dar,
 * was hier steht.
 *
 * **Hier steht kein erfundener Rechtstext, und das ist die Vorgabe.**
 * ORDERS_05 wörtlich: *„Erfinde keine Rechtstexte — auch keine Platzhalter,
 * die aussehen wie echte Texte. Setze stattdessen eine unübersehbare
 * Markierung."* Was hier steht, ist deshalb die **Gliederung** samt einer
 * Notiz, was in den Abschnitt gehört — nie eine Formulierung, die jemand für
 * geprüft halten könnte.
 *
 * **Der Unterschied ist wichtig.** Eine fehlende Widerrufsbelehrung ist ein
 * sichtbarer Mangel. Eine erfundene, die geprüft aussieht, ist ein
 * unsichtbarer: Ohne **korrekte** Belehrung beginnt die Widerrufsfrist nicht
 * zu laufen — sie wird zwölf Monate und vierzehn Tage lang. Der Käufer kann
 * dann nach einem Jahr das Geld zurückverlangen und hat das Produkt bereits.
 *
 * **So wird ein Abschnitt fertig:** `absaetze` mit dem Wortlaut der Kanzlei
 * füllen und `ausstehend` entfernen. Solange irgendwo `ausstehend: true`
 * steht, zeigt die Seite oben ein Warnband — und der Verkauf bleibt ohnehin
 * gesperrt, bis im Backend `AGB_FASSUNG` gesetzt ist (`services/agb.py`).
 *
 * **Die Fassung gehört mit gepflegt.** `FASSUNG` hier und `AGB_FASSUNG` im
 * Backend müssen dieselbe Kennung tragen: Die eine zeigt dem Käufer, welche
 * Fassung er liest, die andere schreibt in seine Bestellung, welcher er
 * zugestimmt hat. Gehen sie auseinander, belegt die Bestellung eine Fassung,
 * die nie jemand gesehen hat.
 */

/** Die unübersehbare Markierung aus ORDERS_05. Nur an einer Stelle definiert,
 *  damit eine Suche danach wirklich alle Fundstellen findet. */
export const AUSSTEHEND = '[[RECHTSTEXT AUSSTEHEND]]';

/** Kennung der geltenden Fassung. `null`, solange keine vorliegt — nicht ein
 *  erfundenes Datum, das beantwortet aussieht. */
export const FASSUNG = null;

/** Ob überhaupt schon etwas Verbindliches dasteht. */
export function textIstVollstaendig(abschnitte) {
  return abschnitte.every((a) => !a.ausstehend);
}

/**
 * Allgemeine Geschäftsbedingungen.
 *
 * Die Gliederung folgt dem, was beim Fernabsatz an Verbraucher verlangt ist.
 * Sie ist ein Gerüst für die Kanzlei, keine Rechtsberatung — welche
 * Abschnitte es am Ende braucht, entscheidet sie.
 */
export const AGB = [
  {
    titel: '1. Geltungsbereich und Vertragspartner',
    hinweis: 'Wer verkauft (Firma, Anschrift, Registereintrag, Vertretung), '
      + 'für welche Angebote diese Bedingungen gelten und gegenüber wem '
      + '(Verbraucher, Unternehmer).',
    ausstehend: true,
    absaetze: [],
  },
  {
    titel: '2. Vertragsschluss',
    hinweis: 'Wann der Vertrag zustande kommt — die Produktdarstellung ist ein '
      + 'Angebot des Kunden, die Annahme erfolgt durch uns. Dazu die '
      + 'Bestellschritte und die Berichtigungsmöglichkeit vor dem Absenden.',
    ausstehend: true,
    absaetze: [],
  },
  {
    titel: '3. Preise und Zahlung',
    hinweis: 'Endpreise einschließlich Umsatzsteuer, Zahlungsdienstleister '
      + '(Stripe), Fälligkeit. Der Steuersatz steht je Produkt im Katalog: '
      + '7 % für das Workbook als elektronische Publikation, 19 % für '
      + 'Check PLUS als Prüfleistung.',
    ausstehend: true,
    absaetze: [],
  },
  {
    titel: '4. Lieferung digitaler Inhalte',
    hinweis: 'Bereitstellung als Download nach Zahlungseingang, Gültigkeitsdauer '
      + 'des Abruf-Links, was bei einem abgelaufenen Link gilt.',
    ausstehend: true,
    absaetze: [],
  },
  {
    titel: '5. Widerrufsrecht',
    hinweis: 'Verweis auf die gesonderte Widerrufsbelehrung und auf das '
      + 'Erlöschen des Widerrufsrechts bei sofortiger Bereitstellung nach '
      + 'ausdrücklicher Zustimmung (§ 356 Abs. 5 BGB).',
    ausstehend: true,
    absaetze: [],
  },
  {
    titel: '6. Nutzungsrechte',
    hinweis: 'Was der Käufer mit dem gekauften PDF darf und was nicht — '
      + 'einfaches Nutzungsrecht für eigene Zwecke, keine Weitergabe.',
    ausstehend: true,
    absaetze: [],
  },
  {
    titel: '7. Anrechnung auf einen Websprint',
    hinweis: 'Die Zusage aus dem Angebot: Der gezahlte Betrag wird innerhalb '
      + 'von sechs Monaten auf einen Websprint angerechnet. Bedingungen, '
      + 'Fristbeginn, einmalige Einlösung.',
    ausstehend: true,
    absaetze: [],
  },
  {
    titel: '8. Haftung',
    hinweis: 'Haftungsumfang und -begrenzung.',
    ausstehend: true,
    absaetze: [],
  },
  {
    titel: '9. Streitbeilegung',
    hinweis: 'Hinweis nach § 36 VSBG, ob an einem Streitbeilegungsverfahren '
      + 'vor einer Verbraucherschlichtungsstelle teilgenommen wird.',
    ausstehend: true,
    absaetze: [],
  },
];

/**
 * Widerrufsbelehrung.
 *
 * **Für diese gibt es ein amtliches Muster** (Anlage 1 zu Art. 246a § 1
 * Abs. 2 EGBGB). Es hier aus dem Gedächtnis hinzuschreiben wäre genau der
 * Fehler, den ORDERS_05 verbietet — die Belehrung ist nur dann wirksam, wenn
 * sie vollständig und auf dieses Geschäft zugeschnitten ist. Sie kommt
 * ausgefüllt von der Kanzlei.
 */
export const WIDERRUF = [
  {
    titel: 'Widerrufsrecht',
    hinweis: 'Amtliches Muster, ausgefüllt: Frist, Fristbeginn, Anschrift und '
      + 'Kontaktdaten der Stelle, an die der Widerruf zu richten ist.',
    ausstehend: true,
    absaetze: [],
  },
  {
    titel: 'Folgen des Widerrufs',
    hinweis: 'Rückzahlung, Frist, verwendetes Zahlungsmittel.',
    ausstehend: true,
    absaetze: [],
  },
  {
    titel: 'Erlöschen bei digitalen Inhalten',
    hinweis: 'Dass das Widerrufsrecht erlischt, wenn der Käufer der sofortigen '
      + 'Bereitstellung ausdrücklich zustimmt und bestätigt, dadurch sein '
      + 'Widerrufsrecht zu verlieren (§ 356 Abs. 5 BGB). Der Wortlaut dieser '
      + 'Zustimmung steht auch im Bestellformular und in der '
      + 'Bestellbestätigung — alle drei müssen übereinstimmen.',
    ausstehend: true,
    absaetze: [],
  },
  {
    titel: 'Muster-Widerrufsformular',
    hinweis: 'Das amtliche Formular aus Anlage 2 zu Art. 246a EGBGB, mit '
      + 'unseren Kontaktdaten ausgefüllt.',
    ausstehend: true,
    absaetze: [],
  },
];

/**
 * Der Wortlaut, dem der Käufer beim Verzicht zustimmt.
 *
 * **Er steht an drei Stellen und muss dreimal gleich lauten:** im
 * Bestellformular neben dem Häkchen, in der Widerrufsbelehrung und in der
 * Bestellbestätigung (ORDERS_05 Schritt 4, versendet in ORDERS_06). Deshalb
 * steht er hier einmal. Drei Kopien driften auseinander, und dann stimmt die
 * Bestätigung nicht mehr mit dem überein, was angehakt wurde.
 */
export const VERZICHTSTEXT = AUSSTEHEND;
