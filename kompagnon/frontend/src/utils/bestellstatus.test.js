/**
 * Die Danke-Seite sagt, was wirklich passiert ist — nicht, was sie hofft.
 *
 * **Der Befund vom 31.08.2026 (L-105).** `GET /api/shop/orders/{nr}/status`
 * war seit ORDERS_04 gebaut und hatte **keinen Aufrufer**. Die Danke-Seite
 * stammt aus ORDERS_03 und sagte deshalb bis heute in jedem Fall dasselbe:
 * „Sobald die Zahlung bei uns bestätigt ist …" — auch wenn sie es längst war.
 *
 * Geprüft wird hier die **Entscheidung**, nicht die Darstellung: Welcher
 * Status ergibt welche Aussage, und wann wird aufgehört zu fragen.
 */
import {
  AUSGELIEFERT, BEZAHLT, GESCHEITERT, OFFEN, aussage, weiterFragen,
} from './bestellstatus';

describe('Was die Danke-Seite sagt', () => {
  test('vor der ersten Antwort wird nichts behauptet', () => {
    const a = aussage(null);
    expect(a.art).toBe('wartet');
    expect(a.text).toMatch(/warten/i);
  });

  test('bezahlt und ausgeliefert sagen dasselbe — der Käufer merkt keinen Unterschied', () => {
    // Zwischen „bezahlt" und „ausgeliefert" liegt der Mailversand. Für den
    // Käufer ist beides derselbe Zustand: Die Mail ist unterwegs.
    expect(aussage(BEZAHLT).art).toBe('gut');
    expect(aussage(AUSGELIEFERT).art).toBe('gut');
    expect(aussage(BEZAHLT).titel).toBe(aussage(AUSGELIEFERT).titel);
  });

  test('eine gescheiterte Zahlung sagt, dass nichts abgebucht wurde', () => {
    const a = aussage(GESCHEITERT);
    expect(a.art).toBe('fehler');
    expect(a.text).toMatch(/nichts abgebucht/i);
  });

  test('nach Ablauf der Wartezeit steht dort, was der Käufer tun kann', () => {
    // Wer nach zwei Minuten dieselbe Zeile liest, hält die Seite für kaputt.
    const vorher = aussage(OFFEN, false);
    const nachher = aussage(OFFEN, true);
    expect(nachher.text).not.toBe(vorher.text);
    expect(nachher.text).toMatch(/nicht offen lassen|müssen diese Seite nicht/i);
  });

  test('keine Aussage verspricht einen Download auf dieser Seite', () => {
    // Der Endpunkt gibt bewusst kein Token heraus. Eine Aussage, die einen
    // Abruf hier ankündigt, wäre ein Versprechen, das die Seite nicht halten
    // kann — und der Anfang eines Wunsches, das Token doch auszuliefern.
    for (const status of [null, OFFEN, BEZAHLT, AUSGELIEFERT, GESCHEITERT]) {
      const { text, titel } = aussage(status);
      expect(`${titel} ${text}`).not.toMatch(/hier herunterladen|Download-Link|jetzt abrufen/i);
    }
  });
});

describe('Wann aufgehört wird zu fragen', () => {
  test('ein Endzustand wird nicht weiter abgefragt', () => {
    for (const status of [BEZAHLT, AUSGELIEFERT, GESCHEITERT]) {
      expect(weiterFragen(status, 0, 40)).toBe(false);
    }
  });

  test('solange offen und im Rahmen, wird weiter gefragt', () => {
    expect(weiterFragen(OFFEN, 0, 40)).toBe(true);
    expect(weiterFragen(null, 39, 40)).toBe(true);
  });

  test('die Schleife hat ein Ende', () => {
    // Ohne Obergrenze läuft sie, solange der Reiter offen ist.
    expect(weiterFragen(OFFEN, 40, 40)).toBe(false);
    expect(weiterFragen(OFFEN, 999, 40)).toBe(false);
  });
});
