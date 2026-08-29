/**
 * Die Pflichtangaben vor dem Kauf (ORDERS_05, Schritt 3).
 *
 * **Der unangenehmste Fund beim Nachlesen.** Im Verzichts-Häkchen stand ein
 * **selbst geschriebener Rechtssatz** — „Ich verlange die sofortige
 * Bereitstellung und weiß, dass ich damit mein Widerrufsrecht verliere…".
 * Genau das verbietet ORDERS_05: *„Erfinde keine Rechtstexte — auch keine
 * Platzhalter, die aussehen wie echte Texte."* Der Satz war plausibel, und
 * das ist das Problem: Niemand hätte ihn geprüft, weil er geprüft aussah.
 * Er kommt jetzt aus `inhalte/rechtstexte.js` und steht dort bis zur
 * anwaltlichen Fassung als Markierung.
 *
 * **Keine Vorbelegung bei privat/geschäftlich.** ORDERS_05 verlangt eine
 * Pflichtauswahl. Vorher war es ein Häkchen „Ich kaufe als Unternehmen", das
 * unangehakt „Privatperson" bedeutete — also eine Vorbelegung, die über das
 * Widerrufsrecht entscheidet, ohne dass jemand sie getroffen hat.
 *
 * **Ein Häkchen auf einen Text, den man nicht lesen kann, ist keine
 * Einbeziehung.** Die AGB brauchen einen Verweis, die Widerrufsbelehrung
 * auch — und beide in einem neuen Fenster, damit die eingegebenen Daten nicht
 * verloren gehen.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import React from 'react';

import KaufFormular from '../components/KaufFormular';
import { AUSSTEHEND } from '../inhalte/rechtstexte';

const PRODUKT = {
  slug: 'workbook_homepage_standard',
  name: 'Workbook Homepage-Standard',
  price_brutto: 149,
  price_netto: 139.25,
  tax_rate: 7,
};

function zeige() {
  return render(<KaufFormular produkt={PRODUKT} onAbbrechen={() => {}} />);
}

describe('Die Auswahl privat oder geschäftlich', () => {
  test('ist zu Beginn nicht vorbelegt', () => {
    // Arrange & Act
    zeige();

    // Assert
    expect(screen.getByLabelText(/Privatperson/i)).not.toBeChecked();
    expect(screen.getByLabelText(/Unternehmen/i)).not.toBeChecked();
  });

  test('ohne getroffene Auswahl wird nicht bestellt, und es steht warum da',
    () => {
      // Arrange
      zeige();

      // Act
      fireEvent.click(screen.getByRole('button',
        { name: /Zahlungspflichtig bestellen/i }));

      // Assert
      const meldung = screen.getByRole('alert').textContent;
      expect(meldung).toMatch(/Privatperson/i);
      expect(meldung).toMatch(/Unternehmen/i);
      // Und sie sagt, warum es darauf ankommt — nicht nur „Pflichtfeld".
      expect(meldung).toMatch(/Widerrufsrecht/i);
    });

  test('erst „privat" zeigt das Verzichts-Häkchen', () => {
    // Arrange
    zeige();
    expect(screen.queryByTestId('verzicht')).toBeNull();

    // Act
    fireEvent.click(screen.getByLabelText(/Privatperson/i));

    // Assert
    expect(screen.getByTestId('verzicht')).toBeInTheDocument();
  });

  test('„geschäftlich" zeigt kein Verzichts-Häkchen, aber die USt-IdNr.', () => {
    // Ein Unternehmen hat kein Widerrufsrecht nach § 355 BGB; ein Häkchen für
    // den Verzicht auf ein Recht, das man nicht hat, führt in die Irre.
    // Arrange
    zeige();

    // Act
    fireEvent.click(screen.getByLabelText(/Unternehmen/i));

    // Assert
    expect(screen.queryByTestId('verzicht')).toBeNull();
    expect(screen.getByLabelText(/USt-IdNr/i)).toBeInTheDocument();
  });
});

describe('Kein Häkchen ist vorbelegt', () => {
  test('AGB und Verzicht starten leer', () => {
    // Vorangekreuzte Zustimmungen sind unwirksam.
    // Arrange & Act
    zeige();
    fireEvent.click(screen.getByLabelText(/Privatperson/i));

    // Assert
    expect(screen.getByTestId('agb')).not.toBeChecked();
    expect(screen.getByTestId('verzicht')).not.toBeChecked();
  });
});

describe('Die Verweise', () => {
  test('die AGB sind verlinkt und öffnen in einem neuen Fenster', () => {
    // Arrange & Act
    zeige();
    const verweis = screen.getByRole('link', { name: /AGB/i });

    // Assert
    expect(verweis).toHaveAttribute('href', '/agb');
    expect(verweis).toHaveAttribute('target', '_blank');
    // Ohne noopener bekommt die geöffnete Seite Zugriff auf `window.opener`.
    expect(verweis.getAttribute('rel')).toMatch(/noopener/);
  });

  test('die Widerrufsbelehrung ist für Verbraucher verlinkt', () => {
    // Arrange
    zeige();

    // Act
    fireEvent.click(screen.getByLabelText(/Privatperson/i));

    // Assert
    expect(screen.getByRole('link', { name: /Widerrufsbelehrung/i }))
      .toHaveAttribute('href', '/widerruf');
  });
});

describe('Der Verzichtstext', () => {
  test('kommt aus den Rechtstexten und ist nicht im Formular formuliert', () => {
    // Solange die Kanzlei nicht geliefert hat, steht dort die Markierung —
    // sichtbar, statt eines plausiblen Satzes, den niemand geprüft hat.
    // Arrange & Act
    zeige();
    fireEvent.click(screen.getByLabelText(/Privatperson/i));

    // Assert
    expect(screen.getByTestId('verzicht-text').textContent).toContain(AUSSTEHEND);
  });

  test('das Formular schreibt keinen eigenen Widerrufssatz', () => {
    // Die Gegenprobe zum Fund: Der alte Wortlaut darf nicht zurückkommen.
    // Arrange & Act
    zeige();
    fireEvent.click(screen.getByLabelText(/Privatperson/i));

    // Assert
    expect(document.body.textContent)
      .not.toMatch(/verliere, sobald die Bereitstellung beginnt/i);
  });
});

describe('Die Schaltfläche', () => {
  test('benennt die Zahlungspflicht', () => {
    // „Weiter" oder „Absenden" genügt nicht (§ 312j Abs. 3 BGB).
    // Arrange & Act
    zeige();

    // Assert
    expect(screen.getByRole('button',
      { name: /^Zahlungspflichtig bestellen$/i })).toBeInTheDocument();
  });
});
