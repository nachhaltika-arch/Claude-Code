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

// ── Wächter: keine Preise mehr im Quelltext ─────────────────────────
//
// Der Befund war nicht eine falsche Zahl, sondern **mehrere Quellen** für
// dieselbe. Ein Test auf die richtige Zahl würde die nächste Abweichung erst
// bemerken, wenn jemand sie einträgt. Dieser hier verbietet die zweite Quelle.
//
// **Er lief zuerst über eine feste Liste von drei Dateien — und genau diese
// Beschränkung war die Lücke.** Über alle Dateien gezählt standen weitere
// feste Beträge in `AuditHook.jsx` (dem eingebetteten Widget, also auf fremden
// Seiten), in `CustomerProjects.jsx` und in drei Paketseiten. Seitdem prüft er
// den ganzen Baum; was ausgenommen ist, steht namentlich darunter.

const fs = require('fs');
const path = require('path');

const WURZEL = path.join(__dirname, '..');

/**
 * Stellen, an denen ein Betrag stehen darf. Jede ist nachgesehen worden.
 */
const GEPRUEFTE_AUSNAHMEN = [
  // Platzhalter-Beispiel für die Preisangabe **des Kunden** auf seiner
  // eigenen Leistungsseite — nicht unser Paketpreis.
  'components/LeistungsseitenWizard.jsx',
  // Die drei Paketseiten standen hier, solange /paket/… keine Route hatte.
  // Seit dem 21.08.2026 sind sie erreichbar (L-64) und holen ihre Preise
  // über `usePakete` — die Ausnahme ist damit hinfällig.
];

function dateienEinsammeln(verzeichnis, treffer = []) {
  for (const eintrag of fs.readdirSync(verzeichnis, { withFileTypes: true })) {
    const voll = path.join(verzeichnis, eintrag.name);
    if (eintrag.isDirectory()) dateienEinsammeln(voll, treffer);
    else if (/\.jsx?$/.test(eintrag.name) && !eintrag.name.includes('.test.')) treffer.push(voll);
  }
  return treffer;
}

describe('keine zweite Preisquelle im Quelltext', () => {
  test('kein Paketpreis steht fest im Code', () => {
    // Die fünf gemessenen Beträge und ihre Schreibweisen.
    const BETRAEGE = ['1.500', '2.000', '2.500', '2.800', '3.500'];
    const fund = [];

    for (const datei of dateienEinsammeln(WURZEL)) {
      const relativ = path.relative(WURZEL, datei).split(path.sep).join('/');
      if (GEPRUEFTE_AUSNAHMEN.includes(relativ)) continue;

      // Kommentare erinnern absichtlich an die alten Zahlen — dieselbe
      // Entscheidung wie bei PACKAGE_NAMES. Block- und JSX-Kommentare gehen
      // über mehrere Zeilen, deshalb erst entfernen, dann zerlegen.
      const zeilen = fs.readFileSync(datei, 'utf8')
        .replace(/\{?\/\*[\s\S]*?\*\/\}?/g, '')
        .replace(/^\s*\/\/.*$/gm, '')
        .split('\n');

      zeilen.forEach((zeile, i) => {
        for (const betrag of BETRAEGE) {
          if (zeile.includes(`${betrag} €`) || zeile.includes(`${betrag}€`)) {
            fund.push(`${relativ}:${i + 1}`);
          }
        }
      });
    }

    expect(fund).toEqual([]);
  });
});

describe('verkaeuflich — was die Kasse auch annimmt', () => {
  /**
   * Der Endpunkt `/api/payments/packages` liefert ausschliesslich Pakete mit
   * Status `live`; `create-checkout` nimmt ebenfalls nur solche an. Fehlt ein
   * Paket in der Antwort, ist es nicht kaeuflich — und eine Seite, die
   * trotzdem einen Kauf anbietet, laeuft in einen 400er.
   *
   * Das war beim Wechsel auf die Websprint-Produkte am 23.08.2026 der Fall
   * (L-97): Drei Verkaufsseiten trugen die Paketkennung fest im Aufruf,
   * waehrend ihre Produkte archiviert wurden.
   */
  test('ein Paket, das der Server liefert, ist verkaeuflich', () => {
    // Arrange
    const darstellung = [{ id: 'websprint_neubau', name: 'Neubau' }];
    const ausApi = { websprint_neubau: { name: 'Websprint Neubau', price_eur: 9401 } };

    // Act
    const pakete = paketeZusammenfuehren(darstellung, ausApi);

    // Assert
    expect(pakete[0].verkaeuflich).toBe(true);
  });

  test('ein Paket, das der Server nicht kennt, ist nicht verkaeuflich', () => {
    // Arrange — archiviert oder Entwurf: der Server liefert es nicht
    const darstellung = [{ id: 'websprint_system', name: 'System' }];

    // Act
    const pakete = paketeZusammenfuehren(darstellung, {});

    // Assert
    expect(pakete[0].verkaeuflich).toBe(false);
  });

  test('ohne Antwort vom Server ist nichts verkaeuflich', () => {
    // Arrange
    const darstellung = [{ id: 'websprint_neubau' }, { id: 'websprint_relaunch' }];

    // Act
    const pakete = paketeZusammenfuehren(darstellung, null);

    // Assert — lieber kein Kauf als ein Kauf, der scheitert
    expect(pakete.every((p) => p.verkaeuflich === false)).toBe(true);
  });
});
