/**
 * Der Anrechnungs-Hinweis beim Deal (L-100, ORDERS_08 Schritt 4).
 *
 * **Warum ausgerechnet hier eine Zusicherung.** Die Prüfroute im Backend kann
 * richtig rechnen — wenn niemand den Hinweis sieht, wird die Anrechnung
 * trotzdem vergessen, und der Kunde erinnert sich immer. Genau das ist die
 * Familie „gebaut, nicht angeschlossen", die diesen Bestand fünfmal gekostet
 * hat: eine Route ohne Knopf.
 *
 * **Die späte Antwort ist die unangenehmste Prüfung hier.** Wer die Firma
 * wechselt, während die erste Abfrage noch läuft, bekäme sonst die Anrechnung
 * des vorigen Kunden angezeigt — und die Abzugsposition landete im falschen
 * Angebot.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import React from 'react';

import AnrechnungsHinweis, {
  abzugsposition, euro,
} from '../components/AnrechnungsHinweis';

const WORKBOOK = {
  order_number: 'B-2026-0007',
  product_code: 'workbook_homepage_standard',
  betrag_cents: 14900,
  gueltig_bis: '2027-02-12',
  tage_uebrig: 120,
};
const CHECK_PLUS = {
  order_number: 'B-2026-0009',
  product_code: 'check_plus',
  betrag_cents: 24900,
  gueltig_bis: '2027-03-01',
  tage_uebrig: 137,
};

function antworte(anrechnungen) {
  global.fetch = jest.fn(() => Promise.resolve({
    ok: true,
    json: () => Promise.resolve({
      anrechnungen,
      summe_cents: anrechnungen.reduce((s, a) => s + a.betrag_cents, 0),
    }),
  }));
}

afterEach(() => { delete global.fetch; });

describe('Wann der Hinweis erscheint', () => {
  test('ohne E-Mail wird nicht einmal gefragt', () => {
    // Arrange
    antworte([]);

    // Act
    render(<AnrechnungsHinweis email="" onUebernehmen={() => {}} />);

    // Assert
    expect(global.fetch).not.toHaveBeenCalled();
    expect(screen.queryByTestId('anrechnung-hinweis')).toBeNull();
  });

  test('ohne offene Anrechnung bleibt das Formular unverändert', async () => {
    // Ein Kasten „keine Anrechnung" wäre Lärm bei jedem zweiten Deal.
    // Arrange
    antworte([]);

    // Act
    render(<AnrechnungsHinweis email="kunde@example.com"
                               onUebernehmen={() => {}} />);

    // Assert
    await waitFor(() => expect(global.fetch).toHaveBeenCalled());
    expect(screen.queryByTestId('anrechnung-hinweis')).toBeNull();
  });

  test('eine offene Anrechnung steht mit Betrag, Bestellung und Frist da',
    async () => {
      // Arrange
      antworte([WORKBOOK]);

      // Act
      render(<AnrechnungsHinweis email="kunde@example.com"
                                 onUebernehmen={() => {}} />);

      // Assert
      const kasten = await screen.findByTestId('anrechnung-hinweis');
      expect(kasten.textContent).toMatch(/149,00 €/);
      expect(kasten.textContent).toMatch(/B-2026-0007/);
      expect(kasten.textContent).toMatch(/2027-02-12/);
      expect(kasten.textContent).toMatch(/noch 120 Tage/);
    });

  test('zwei Anrechnungen werden beide gezeigt, mit ihrer Summe', async () => {
    // 149 € und 249 € sind zusammen 398 € — die Entscheidung gehört einem
    // Menschen, nicht der Reihenfolge einer Abfrage.
    // Arrange
    antworte([WORKBOOK, CHECK_PLUS]);

    // Act
    render(<AnrechnungsHinweis email="kunde@example.com"
                               onUebernehmen={() => {}} />);

    // Assert
    const kasten = await screen.findByTestId('anrechnung-hinweis');
    expect(kasten.textContent).toMatch(/398,00 €/);
    expect(kasten.textContent).toMatch(/B-2026-0007/);
    expect(kasten.textContent).toMatch(/B-2026-0009/);
  });

  test('ein Fehler beim Abruf stört das Formular nicht', async () => {
    // Arrange
    global.fetch = jest.fn(() => Promise.reject(new Error('offline')));

    // Act
    render(<AnrechnungsHinweis email="kunde@example.com"
                               onUebernehmen={() => {}} />);

    // Assert
    await waitFor(() => expect(global.fetch).toHaveBeenCalled());
    expect(screen.queryByTestId('anrechnung-hinweis')).toBeNull();
  });
});

describe('Die Übernahme ins Angebot', () => {
  test('der Knopf reicht alle offenen Anrechnungen weiter', async () => {
    // Arrange
    antworte([WORKBOOK, CHECK_PLUS]);
    const uebernommen = [];

    render(<AnrechnungsHinweis email="kunde@example.com"
                               onUebernehmen={(a) => uebernommen.push(a)} />);
    await screen.findByTestId('anrechnung-hinweis');

    // Act
    fireEvent.click(screen.getByRole('button',
      { name: /Im Angebot berücksichtigen/i }));

    // Assert
    expect(uebernommen).toHaveLength(1);
    expect(uebernommen[0].map((a) => a.order_number))
      .toEqual(['B-2026-0007', 'B-2026-0009']);
  });

  test('die Abzugsposition ist negativ und nennt die Bestellung', () => {
    // Ein stiller Rabatt auf die Summe ist für den Kunden nicht
    // nachvollziehbar; die Position steht im Angebot und im PDF.
    // Act
    const position = abzugsposition(WORKBOOK);

    // Assert
    expect(position.unit_price).toBe(-149);
    expect(position.position).toMatch(/B-2026-0007/);
    expect(position.quantity).toBe(1);
  });
});

describe('Der Firmenwechsel', () => {
  test('eine späte Antwort zur alten Firma setzt den Hinweis nicht mehr',
    async () => {
      // Sonst stünde im Angebot der neuen Firma die Anrechnung der alten.
      // Arrange
      let loesen;
      global.fetch = jest.fn(() => new Promise((r) => { loesen = r; }));

      const { unmount } = render(
        <AnrechnungsHinweis email="alt@example.com" onUebernehmen={() => {}} />);

      // Act — Formular weg, dann trifft die Antwort ein
      unmount();
      loesen({
        ok: true,
        json: () => Promise.resolve({
          anrechnungen: [WORKBOOK], summe_cents: 14900,
        }),
      });

      // Assert — kein Hinweis, und keine Warnung über einen Zustandswechsel
      // an einer abgebauten Komponente.
      await waitFor(() => expect(global.fetch).toHaveBeenCalled());
      expect(screen.queryByTestId('anrechnung-hinweis')).toBeNull();
    });
});

describe('Die Darstellung von Beträgen', () => {
  test('Cent werden zu deutschen Euro-Beträgen', () => {
    expect(euro(14900)).toBe('149,00 €');
    expect(euro(0)).toBe('0,00 €');
    expect(euro(null)).toBe('0,00 €');
  });
});
