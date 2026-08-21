/**
 * L-29: Der Preis auf dem Bildschirm muss der sein, der abgebucht wird.
 *
 * Gemessen am 19.08.2026: Premium stand im Frontend zweimal mit 2.500,
 * in `products` mit 2.800. Der Kunde las die eine Zahl und zahlte die andere.
 */
import {
  paketeZusammenfuehren,
  preisAnzeige,
  preisZeile,
  PREIS_UNBEKANNT,
} from './paketpreise';

const DARSTELLUNG = [
  { id: 'starter', name: 'Starter', accentColor: 'blau' },
  { id: 'kompagnon', name: 'KOMPAGNON', accentColor: 'gelb' },
  { id: 'premium', name: 'Premium', accentColor: 'lila' },
];

describe('preisAnzeige', () => {
  test('schreibt 2000 als 2.000', () => {
    expect(preisAnzeige(2000)).toBe('2.000');
  });

  test('liefert null statt einer Null — kein Preis ist besser als 0 €', () => {
    expect(preisAnzeige(0)).toBeNull();
    expect(preisAnzeige(null)).toBeNull();
    expect(preisAnzeige('keine Zahl')).toBeNull();
  });
});

describe('paketeZusammenfuehren', () => {
  test('nimmt den Preis vom Server, nicht aus der Darstellung', () => {
    // Arrange — genau der Fall, der auseinandergelaufen war
    const ausApi = { premium: { name: 'Premium', price_eur: 2800 } };

    // Act
    const pakete = paketeZusammenfuehren(DARSTELLUNG, ausApi);

    // Assert
    expect(pakete.find((p) => p.id === 'premium').preisLabel).toBe('2.800');
  });

  test('behaelt Reihenfolge und Darstellung bei', () => {
    // Act
    const pakete = paketeZusammenfuehren(DARSTELLUNG, {
      starter: { price_eur: 1500 },
    });

    // Assert
    expect(pakete.map((p) => p.id)).toEqual(['starter', 'kompagnon', 'premium']);
    expect(pakete[0].accentColor).toBe('blau');
  });

  test('ohne Antwort des Servers steht dort kein Preis, nicht der alte', () => {
    // Act
    const pakete = paketeZusammenfuehren(DARSTELLUNG, null);

    // Assert
    expect(pakete.every((p) => p.preisBekannt === false)).toBe(true);
    expect(pakete.every((p) => p.preisLabel === null)).toBe(true);
  });

  test('ein Paket, das der Server nicht kennt, erfindet keinen Preis', () => {
    // Act
    const pakete = paketeZusammenfuehren(DARSTELLUNG, {
      starter: { price_eur: 1500 },
    });

    // Assert
    expect(pakete.find((p) => p.id === 'premium').preisBekannt).toBe(false);
  });
});

describe('preisZeile', () => {
  test('Karte und Vergleichstabelle koennen nicht getrennt veralten', () => {
    // Arrange
    const pakete = paketeZusammenfuehren(DARSTELLUNG, {
      starter: { price_eur: 1500 },
      kompagnon: { price_eur: 2000 },
      premium: { price_eur: 2800 },
    });

    // Act
    const zeile = preisZeile(pakete);

    // Assert
    expect(zeile).toEqual(['1.500 €', '2.000 €', '2.800 €']);
  });

  test('was der Server nicht kennt, steht als „auf Anfrage" da', () => {
    // Act
    const zeile = preisZeile(paketeZusammenfuehren(DARSTELLUNG, {}));

    // Assert
    expect(zeile).toEqual([PREIS_UNBEKANNT, PREIS_UNBEKANNT, PREIS_UNBEKANNT]);
  });
});

// ── Wächter: keine Preise mehr im Quelltext der Verkaufsflächen ──────
//
// Der Befund war nicht eine falsche Zahl, sondern **vier Quellen** für
// dieselbe. Ein Test auf die richtige Zahl würde die nächste Abweichung
// erst bemerken, wenn jemand sie einträgt. Dieser hier verbietet die
// zweite Quelle.

const fs = require('fs');
const path = require('path');

const VERKAUFSFLAECHEN = [
  'components/OfferTab.jsx',
  'components/PricingSection.jsx',
  'pages/Landing.jsx',
];

describe('keine zweite Preisquelle im Quelltext', () => {
  test.each(VERKAUFSFLAECHEN)('%s nennt keinen Paketpreis', (datei) => {
    // Arrange
    const quelle = fs.readFileSync(path.join(__dirname, '..', datei), 'utf8');

    // Nur Zeilen, die etwas anzeigen — Kommentare erinnern absichtlich an
    // die alten Zahlen (dieselbe Entscheidung wie bei PACKAGE_NAMES).
    // Block- und JSX-Kommentare gehen ueber mehrere Zeilen; deshalb erst
    // entfernen, dann zerlegen.
    const ohneKommentare = quelle
      .replace(/\{?\/\*[\s\S]*?\*\/\}?/g, '')
      .replace(/^\s*\/\/.*$/gm, '');
    const zeilen = ohneKommentare.split('\n');

    // Assert — die vier gemessenen Beträge und ihre Schreibweisen
    for (const betrag of ['1.500', '2.000', '2.500', '2.800', '3.500']) {
      const treffer = zeilen.filter((z) => z.includes(`${betrag} €`) || z.includes(`${betrag}€`));
      expect(treffer).toEqual([]);
    }
  });
});
