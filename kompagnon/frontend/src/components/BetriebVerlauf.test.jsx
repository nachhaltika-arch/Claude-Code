import { render, screen, waitFor } from '@testing-library/react';
import BetriebVerlauf from './BetriebVerlauf';
import * as apiRequest from '../utils/apiRequest';

/**
 * Der Verlauf muss drei Zustaende unterscheiden, die leicht gleich aussehen:
 * geladen mit Inhalt, geladen und leer, und gar nicht geladen. Das Zweite
 * heisst „hier war nichts", das Dritte „wir wissen es nicht" — und die zu
 * verwechseln ist genau die Art Fehler, die niemandem auffaellt.
 */

const ereignis = (art, titel, zeitpunkt, quellen = ['leads']) =>
  ({ art, titel, zeitpunkt, quellen });

afterEach(() => jest.restoreAllMocks());

test('zeigt die Ereignisse in der Reihenfolge, die der Server liefert', async () => {
  jest.spyOn(apiRequest, 'loadJson').mockResolvedValue({
    ereignisse: [
      ereignis('email', 'E-Mail: Ihr Angebot', '2026-08-19T10:00:00'),
      ereignis('angelegt', 'Betrieb angelegt', '2026-08-12T10:00:00'),
    ],
  });

  render(<BetriebVerlauf leadId={7} token="tok" />);

  await waitFor(() => expect(screen.getByText('E-Mail: Ihr Angebot')).toBeInTheDocument());
  const eintraege = screen.getAllByRole('listitem');
  expect(eintraege[0]).toHaveTextContent('Ihr Angebot');
  expect(eintraege[1]).toHaveTextContent('Betrieb angelegt');
});

test('ein leerer Verlauf sagt, dass nichts vermerkt ist', async () => {
  jest.spyOn(apiRequest, 'loadJson').mockResolvedValue({ ereignisse: [] });

  render(<BetriebVerlauf leadId={7} token="tok" />);

  await waitFor(() =>
    expect(screen.getByText(/noch nichts vermerkt/i)).toBeInTheDocument());
});

test('ein Ladefehler wird gezeigt und nicht als leerer Verlauf getarnt', async () => {
  jest.spyOn(apiRequest, 'loadJson').mockRejectedValue(new Error('Netz weg'));

  render(<BetriebVerlauf leadId={7} token="tok" />);

  await waitFor(() => expect(screen.getByText('Netz weg')).toBeInTheDocument());
  expect(screen.queryByText(/noch nichts vermerkt/i)).not.toBeInTheDocument();
});

test('nennt die Quelle eines Ereignisses — auch wenn es zwei sind', async () => {
  jest.spyOn(apiRequest, 'loadJson').mockResolvedValue({
    ereignisse: [ereignis('email', 'E-Mail: Ihr Angebot', '2026-08-19T10:00:00',
                          ['email_logs', 'communications'])],
  });

  render(<BetriebVerlauf leadId={7} token="tok" />);

  await waitFor(() => expect(
    screen.getByTitle('Quelle: email_logs, communications')).toBeInTheDocument());
});
