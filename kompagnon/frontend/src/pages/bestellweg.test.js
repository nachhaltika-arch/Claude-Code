/**
 * L-64: Der Bestellweg endete auf der Anmeldeseite.
 *
 * Im Browser am Produktivsystem gemessen (21.08.2026):
 *
 *     kas.kompagnon.group/paket/premium       →  /login
 *     kas.kompagnon.group/checkout            →  /login
 *     kas.kompagnon.group/checkout/kompagnon  →  /login
 *
 * `App.jsx` führte 82 Routen und **keine einzige** für `/paket/…` oder
 * `/checkout`; die Auffangroute schickt alles Unbekannte zur Anmeldung.
 * `Checkout.jsx`, `CheckoutSuccess.jsx` und die drei Paketseiten lagen im
 * Quellbaum, wurden von nichts importiert und erreichten nicht einmal das
 * ausgelieferte Bündel.
 *
 * Betroffen waren drei Wege: der Bestelllink aus der Angebotsmail, die Knöpfe
 * „Paket wählen" — und der Rücksprung **nach bezahlter Rechnung**, denn
 * `create_checkout` schickt Stripe auf `/checkout/success` zurück.
 *
 * Dieser Test liest die Routen aus dem Quelltext. Er kann nicht rendern
 * (keine Testing-Library im Projekt) — er hält aber genau das fest, was
 * gefehlt hat: dass es die Adressen überhaupt gibt.
 */
const fs = require('fs');
const path = require('path');

const app = fs.readFileSync(path.join(__dirname, '..', 'App.jsx'), 'utf8');

const routen = [...app.matchAll(/<Route\s+path="([^"]+)"/g)].map((m) => m[1]);

describe('Der Bestellweg hat Adressen', () => {
  test.each([
    ['/paket/:slug',       'Bestelllink aus der Angebotsmail'],
    ['/checkout',          'Kasse ohne vorgewähltes Paket'],
    ['/checkout/:package', 'Kasse mit Paket'],
    ['/checkout/success',  'Rücksprung nach bezahlter Rechnung'],
  ])('%s — %s', (pfad) => {
    expect(routen).toContain(pfad);
  });

  test('die Erfolgsseite steht vor dem Platzhalter', () => {
    // Sonst liest React Router „success" als Paketnamen und zeigt die Kasse
    // statt der Bestätigung — dieselbe Falle wie /suggestions gegen
    // /{template_id} im Backend (L-28).
    expect(routen.indexOf('/checkout/success'))
      .toBeLessThan(routen.indexOf('/checkout/:package'));
  });

  test('die Auffangroute steht am Ende', () => {
    // Sie schickt alles Unbekannte zur Anmeldung. Stünde sie früher, würde
    // sie die Bestellwege wieder verschlucken.
    expect(routen[routen.length - 1]).toBe('*');
  });
});

describe('Kein Bestellweg ruft eine Adresse, die es nicht gibt', () => {
  // Die vollständige Prüfung gegen die registrierten Backend-Routen steht in
  // backend/tests/test_frontend_adressen.py. Hier nur die vier Stellen, die
  // im August vier Monate lang ins Leere zeigten.
  const lies = (datei) => fs.readFileSync(path.join(__dirname, datei), 'utf8');

  test('die Erfolgsseite fragt die Zahlungs-Schnittstelle, nicht „stripe"', () => {
    expect(lies('CheckoutSuccess.jsx')).toContain('/api/payments/session/');
    expect(lies('CheckoutSuccess.jsx')).not.toContain('/api/stripe/');
  });

  test.each(['PackageStarter.jsx', 'PackageKompagnon.jsx', 'PackagePremium.jsx'])(
    '%s startet die Kasse über den echten Endpunkt', (datei) => {
      expect(lies(datei)).toContain('/api/payments/create-checkout');
      expect(lies(datei)).not.toContain('/api/stripe/');
    });
});
