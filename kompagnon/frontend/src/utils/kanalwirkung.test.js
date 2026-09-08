/**
 * „Welcher Kanal bringt Kunden?" — der Bericht aus L-84, den niemand sah.
 *
 * `GET /api/leads/quellen/wirkung` rechnet seit dem 24.08.2026 je Herkunft
 * Betriebe, Kunden und Quote. Aufgerufen hat ihn kein Bildschirm; die
 * Betriebsliste hatte einen Quellenfilter, aber nichts, was sagt, welcher
 * dieser Filter etwas wert ist (L-105, „der Knopf fehlt").
 *
 * **Die Regeln hier sind die aus `ux-methode-krug`:** Ein unbekannter Wert
 * wird weder roh gezeigt noch getarnt. Eine Quote, die es nicht gibt, ist
 * nicht null — sie ist keine.
 */
import { kanaeleAufbereiten, quoteText } from './kanalwirkung';

describe('Quote als Text', () => {
  test('0,25 wird zu „25 %"', () => {
    expect(quoteText(0.25)).toBe('25 %');
  });

  test('keine Quote ist kein Nullwert', () => {
    // Ein Kanal ohne Betriebe hat keine Quote. „0 %" wäre eine Aussage über
    // seine Wirkung, und die gibt es nicht.
    expect(quoteText(null)).toBe('—');
    expect(quoteText(undefined)).toBe('—');
  });

  test('0 bleibt 0 %', () => {
    // Der Unterschied zum Fall darüber ist der ganze Punkt: Hier **wurde**
    // gemessen, und das Ergebnis ist null Kunden.
    expect(quoteText(0)).toBe('0 %');
  });

  test('gerundet wird auf ganze Prozent', () => {
    expect(quoteText(0.333)).toBe('33 %');
    expect(quoteText(1)).toBe('100 %');
  });
});

describe('Kanäle aufbereiten', () => {
  const antwort = {
    kanaele: [
      { quelle: 'empfehlung', name: 'Empfehlung', bekannt: true, betriebe: 4, kunden: 2, quote: 0.5 },
      { quelle: 'xing_alt', name: 'xing_alt', bekannt: false, betriebe: 3, kunden: 0, quote: 0 },
    ],
    ohne_herkunft: 5,
    betriebe_gesamt: 12,
  };

  test('die Reihenfolge des Servers bleibt', () => {
    // Er sortiert nach Wirkung, bei gleicher Quote nach Bestand. Ein zweites
    // Sortieren im Browser wäre eine zweite Wahrheit.
    expect(kanaeleAufbereiten(antwort).kanaele.map((k) => k.quelle))
      .toEqual(['empfehlung', 'xing_alt']);
  });

  test('ein unbekannter Wert wird als solcher gekennzeichnet', () => {
    const [, unbekannt] = kanaeleAufbereiten(antwort).kanaele;
    expect(unbekannt.bekannt).toBe(false);
    expect(unbekannt.name).toBe('xing_alt');
  });

  test('Betriebe ohne Herkunft stehen als eigene Zeile', () => {
    const { ohneHerkunft } = kanaeleAufbereiten(antwort);
    expect(ohneHerkunft).toBe(5);
  });

  test('die Summe der Kanäle ist nicht der Gesamtbestand', () => {
    // 4 + 3 = 7 Betriebe in Kanälen, 12 insgesamt. Wer die Kanalsumme als
    // Gesamt liest, verliert fünf Betriebe — deshalb steht beides da.
    const { summeKanaele, gesamt } = kanaeleAufbereiten(antwort);
    expect(summeKanaele).toBe(7);
    expect(gesamt).toBe(12);
  });

  test('eine leere Antwort ergibt eine leere Auswertung, keinen Fehler', () => {
    expect(kanaeleAufbereiten({})).toEqual({
      kanaele: [], ohneHerkunft: 0, summeKanaele: 0, gesamt: 0,
    });
    expect(kanaeleAufbereiten(null).kanaele).toEqual([]);
  });

  test('ein kaputtes Feld wirft nicht', () => {
    const kaputt = { kanaele: 'nein', ohne_herkunft: null, betriebe_gesamt: 'x' };
    expect(kanaeleAufbereiten(kaputt)).toEqual({
      kanaele: [], ohneHerkunft: 0, summeKanaele: 0, gesamt: 0,
    });
  });
});
