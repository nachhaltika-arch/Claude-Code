/**
 * Ein ausstehender Rechtstext muss ausstehend aussehen (ORDERS_05).
 *
 * **Der Fehler, gegen den das gebaut ist.** ORDERS_05 verbietet Platzhalter,
 * die aussehen wie echte Texte — und zwar nicht aus Ordnungsliebe: Ohne
 * **korrekte** Widerrufsbelehrung beginnt die Frist nicht zu laufen, sie wird
 * zwölf Monate und vierzehn Tage lang. Ein Käufer kann dann nach einem Jahr
 * das Geld zurückverlangen und hat das Produkt bereits. Eine fehlende
 * Belehrung ist ein sichtbarer Mangel; eine, die geprüft aussieht, ist ein
 * unsichtbarer.
 *
 * **Warum das eine Zusicherung braucht und kein Auge.** Das Warnband ist
 * genau die Sorte Sache, die jemand beim Aufräumen wegnimmt, weil sie stört —
 * und danach sieht die Seite fertig aus. Geprüft wird deshalb am Inhalt, nicht
 * an der Seite: `ausstehend` ist die Wahrheit, das Band nur ihre Anzeige.
 *
 * **Und eine positive Zusicherung daneben** (siehe [[waechter_ohne_wirkung]]):
 * Ein Test, der nur „Warnband vorhanden" prüft, bleibt grün, wenn die Texte
 * fertig sind und das Band fälschlich stehen bleibt. Deshalb wird beides
 * geprüft — mit Vorlage und mit gefülltem Text.
 */
import { render, screen } from '@testing-library/react';
import React from 'react';

import Rechtstext from '../pages/Rechtstext';
import {
  AGB,
  AUSSTEHEND,
  FASSUNG,
  VERZICHTSTEXT,
  WIDERRUF,
  textIstVollstaendig,
} from '../inhalte/rechtstexte';

const FERTIG = [
  { titel: 'Geltungsbereich', hinweis: '', ausstehend: false,
    absaetze: ['Diese Bedingungen gelten für alle Bestellungen.'] },
];

describe('Der Zustand der Vorlage', () => {
  test('solange ein Abschnitt aussteht, gilt der Text als unvollständig', () => {
    // Arrange & Act & Assert
    expect(textIstVollstaendig(AGB)).toBe(false);
    expect(textIstVollstaendig(WIDERRUF)).toBe(false);
  });

  test('ein durchgehend gefüllter Text gilt als vollständig', () => {
    // Die Gegenprobe: ohne sie wäre die Prüfung oben auch dann grün, wenn
    // `textIstVollstaendig` schlicht immer false zurückgäbe.
    expect(textIstVollstaendig(FERTIG)).toBe(true);
  });

  test('ohne anwaltliche Fassung gibt es keine Fassungskennung', () => {
    // Ein erfundenes Datum sähe beantwortet aus. `null` ist die Aussage.
    expect(FASSUNG).toBeNull();
  });

  test('der Verzichtstext ist als ausstehend markiert und nicht formuliert', () => {
    // Er steht an drei Stellen — Formular, Belehrung, Bestätigung — und muss
    // dreimal gleich lauten. Solange er aussteht, überall sichtbar so.
    expect(VERZICHTSTEXT).toBe(AUSSTEHEND);
  });
});

describe('Die Darstellung', () => {
  test('eine Vorlage zeigt das Warnband und die Markierung im Klartext', () => {
    // Arrange & Act
    render(<Rechtstext titel="AGB" unterzeile="" abschnitte={AGB}
                       fassung={FASSUNG} />);

    // Assert
    expect(screen.getByTestId('rechtstext-warnband')).toBeInTheDocument();
    expect(screen.getAllByText(AUSSTEHEND).length).toBe(AGB.length);
  });

  test('das Warnband nennt den Grund, nicht nur eine Warnung', () => {
    // „Achtung" allein schickt niemanden an die richtige Stelle.
    render(<Rechtstext titel="AGB" unterzeile="" abschnitte={AGB}
                       fassung={FASSUNG} />);

    expect(screen.getByTestId('rechtstext-warnband').textContent)
      .toMatch(/AGB_FASSUNG/);
  });

  test('ein fertiger Text zeigt kein Warnband und keine Markierung', () => {
    // Die positive Zusicherung: Sonst bliebe ein stehengebliebenes Warnband
    // unbemerkt, und die fertigen AGB sähen ungültig aus.
    render(<Rechtstext titel="AGB" unterzeile="" abschnitte={FERTIG}
                       fassung="2026-09-01" />);

    expect(screen.queryByTestId('rechtstext-warnband')).toBeNull();
    expect(screen.queryByText(AUSSTEHEND)).toBeNull();
    expect(screen.getByText(/Diese Bedingungen gelten/)).toBeInTheDocument();
  });

  test('die Fassung steht in der Kopfzeile, wenn es eine gibt', () => {
    render(<Rechtstext titel="AGB" unterzeile="Für den Kauf" abschnitte={FERTIG}
                       fassung="2026-09-01" />);

    expect(screen.getByText(/Fassung 2026-09-01/)).toBeInTheDocument();
  });

  test('ohne Fassung sagt die Kopfzeile das, statt zu schweigen', () => {
    render(<Rechtstext titel="AGB" unterzeile="Für den Kauf" abschnitte={AGB}
                       fassung={null} />);

    expect(screen.getByText(/noch keine gültige Fassung/)).toBeInTheDocument();
  });
});
