import { render, screen, fireEvent } from '@testing-library/react';
import AnsichtReiter from './AnsichtReiter';
import { BETRIEB_ANSICHTEN } from '../utils/betriebAnsichten';

/**
 * Die Verdrahtung, nicht das Aussehen.
 *
 * Bei L-79 stand der Knopf „Freigabe anfordern" fertig da und hatte kein
 * `onClick` — niemand hatte je gepruefet, ob ein Klick etwas tut. Dieser Test
 * prueft genau das.
 */

const kunden = BETRIEB_ANSICHTEN.find((a) => a.id === 'kunden');

test('zeigt einen Reiter je Ansicht', () => {
  render(<AnsichtReiter zustand={{}} onWaehlen={() => {}} />);

  expect(screen.getAllByRole('tab')).toHaveLength(BETRIEB_ANSICHTEN.length);
});

test('ein Klick meldet die gewaehlte Ansicht', () => {
  const gewaehlt = [];

  render(<AnsichtReiter zustand={{}} onWaehlen={(id) => gewaehlt.push(id)} />);
  fireEvent.click(screen.getByRole('tab', { name: kunden.label }));

  expect(gewaehlt).toEqual(['kunden']);
});

test('der Reiter zum aktuellen Zustand ist ausgewaehlt', () => {
  render(<AnsichtReiter zustand={kunden.filter} onWaehlen={() => {}} />);

  expect(screen.getByRole('tab', { name: kunden.label }))
    .toHaveAttribute('aria-selected', 'true');
});

test('bei eigener Auswahl leuchtet keiner und es steht daneben', () => {
  const eigen = { status: 'won', quelle: 'csv_import', phase: 'kunde', sortierung: 'score' };

  render(<AnsichtReiter zustand={eigen} onWaehlen={() => {}} />);

  for (const reiter of screen.getAllByRole('tab')) {
    expect(reiter).toHaveAttribute('aria-selected', 'false');
  }
  expect(screen.getByText('Eigene Auswahl')).toBeInTheDocument();
});
