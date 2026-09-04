/**
 * Zwei Exporte, die es gab und die niemand anbot (BUCH-12, FIX-3 — L-115).
 *
 * **Der Befund war kleiner notiert, als er ist.** BUCH-12 nennt eine Kachel:
 * „Audit-Bericht PDF" trage „Bald verfügbar", obwohl `/api/audit/{id}/pdf`
 * existiert. Am 29.08.2026 nachgemessen: **alle sechs** Kacheln in
 * `MassExport` trugen das Etikett, und **zwei** davon gibt es wirklich —
 * `/api/audit/{id}/pdf` und `/api/audit/{id}/angebot`. Die anderen vier
 * (Excel, WordPress-Theme, Serienbrief, Auswertung) haben keinen Endpunkt.
 *
 * **Warum das ein Verkaufsproblem ist und nicht nur eine Schlamperei.** Du
 * bietest eine Funktion nicht an, die du hast — und das Werkzeug wirkt
 * unfertiger, als es ist, ausgerechnet dort, wo Kunden hinsehen.
 *
 * **Warum eine Auswahl nötig war.** Beide Endpunkte brauchen ein Audit. Die
 * Seite heißt „Massen-Export" und kennt keins; die Kachel einfach zu
 * verdrahten hätte einen Knopf ergeben, der nicht weiß, worüber er berichtet.
 *
 * **Ein Export, der leer ausgeht, muss das sagen.** Wer noch kein Audit
 * gefahren hat, bekommt einen Satz — nicht eine leere Liste, die aussieht wie
 * ein Ladefehler.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import React from 'react';

import AuditExportWahl from '../components/AuditExportWahl';

const AUDITS = [
  {
    id: 7, company_name: 'Mustermann Heizung GmbH',
    website_url: 'https://mustermann-heizung.de',
    total_score: 62, created_at: '2026-08-20T10:00:00',
  },
  {
    id: 9, company_name: 'Schmidt & Söhne',
    website_url: 'https://schmidt.de',
    total_score: 81, created_at: '2026-08-22T09:30:00',
  },
];

function antworte(audits) {
  global.fetch = jest.fn(() => Promise.resolve({
    ok: true,
    json: () => Promise.resolve(audits),
  }));
}

afterEach(() => { delete global.fetch; });

describe('Die Auswahl', () => {
  test('listet die letzten Audits mit Betrieb und Punktzahl', async () => {
    // Arrange
    antworte(AUDITS);

    // Act
    render(<AuditExportWahl art="pdf" kopfzeilen={{}} onSchliessen={() => {}} />);

    // Assert
    expect(await screen.findByText(/Mustermann Heizung GmbH/)).toBeInTheDocument();
    expect(screen.getByText(/Schmidt & Söhne/)).toBeInTheDocument();
    expect(screen.getByText(/62/)).toBeInTheDocument();
  });

  test('ohne Audit steht ein Satz da, keine leere Liste', async () => {
    // Eine leere Liste sieht aus wie ein Ladefehler.
    // Arrange
    antworte([]);

    // Act
    render(<AuditExportWahl art="pdf" kopfzeilen={{}} onSchliessen={() => {}} />);

    // Assert
    expect(await screen.findByText(/noch kein.*Audit/i)).toBeInTheDocument();
  });

  test('ein Fehler beim Laden wird gesagt, nicht verschwiegen', async () => {
    // Arrange
    global.fetch = jest.fn(() => Promise.reject(new Error('offline')));

    // Act
    render(<AuditExportWahl art="pdf" kopfzeilen={{}} onSchliessen={() => {}} />);

    // Assert
    expect(await screen.findByRole('alert')).toBeInTheDocument();
  });

  test('die Überschrift sagt, welcher Export gemeint ist', async () => {
    // Beide Kacheln öffnen dieselbe Auswahl; ohne Überschrift weiß niemand,
    // ob er gerade den Bericht oder das Angebot zieht.
    // Arrange
    antworte(AUDITS);

    // Act
    render(<AuditExportWahl art="angebot" kopfzeilen={{}}
                            onSchliessen={() => {}} />);

    // Assert
    expect(await screen.findByText(/Angebot/i)).toBeInTheDocument();
  });
});

describe('Der Abruf', () => {
  test('holt den Bericht unter der Adresse des gewählten Audits', async () => {
    // Arrange
    antworte(AUDITS);
    render(<AuditExportWahl art="pdf" kopfzeilen={{ Authorization: 'Bearer x' }}
                            onSchliessen={() => {}} />);
    await screen.findByText(/Mustermann Heizung GmbH/);

    global.fetch = jest.fn(() => Promise.resolve({
      ok: true, blob: () => Promise.resolve(new Blob(['pdf'])),
    }));

    // Act
    fireEvent.click(screen.getByText(/Mustermann Heizung GmbH/));

    // Assert
    await waitFor(() => expect(global.fetch).toHaveBeenCalled());
    expect(global.fetch.mock.calls[0][0]).toMatch(/\/api\/audit\/7\/pdf$/);
    // Beide Endpunkte stehen hinter `require_innendienst` — ohne Kopfzeile
    // käme eine 401 zurück, und der Nutzer sähe einen leeren Download.
    expect(global.fetch.mock.calls[0][1].headers.Authorization)
      .toBe('Bearer x');
  });

  test('das Angebot nimmt die andere Adresse', async () => {
    // Arrange
    antworte(AUDITS);
    render(<AuditExportWahl art="angebot" kopfzeilen={{}}
                            onSchliessen={() => {}} />);
    await screen.findByText(/Schmidt & Söhne/);

    global.fetch = jest.fn(() => Promise.resolve({
      ok: true, blob: () => Promise.resolve(new Blob(['pdf'])),
    }));

    // Act
    fireEvent.click(screen.getByText(/Schmidt & Söhne/));

    // Assert
    await waitFor(() => expect(global.fetch).toHaveBeenCalled());
    expect(global.fetch.mock.calls[0][0]).toMatch(/\/api\/audit\/9\/angebot$/);
  });

  test('ein gescheiterter Abruf meldet sich, statt still zu bleiben', async () => {
    // Ein Knopf, der nichts tut, ist schlimmer als ein Knopf mit Fehlermeldung.
    // Arrange
    antworte(AUDITS);
    render(<AuditExportWahl art="pdf" kopfzeilen={{}} onSchliessen={() => {}} />);
    await screen.findByText(/Mustermann Heizung GmbH/);

    global.fetch = jest.fn(() => Promise.resolve({ ok: false, status: 500 }));

    // Act
    fireEvent.click(screen.getByText(/Mustermann Heizung GmbH/));

    // Assert
    expect(await screen.findByRole('alert')).toBeInTheDocument();
  });
});
