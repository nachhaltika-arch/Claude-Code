/**
 * Der Sinn dieses Moduls ist, dass Fehler NICHT verschwinden — genau das
 * prüfen diese Tests. Hintergrund: 83 leere catch-Blöcke im Frontend haben
 * dafür gesorgt, dass vier Fehler monatelang unbemerkt liefen (L-36).
 */
import toast from 'react-hot-toast';
import { ApiError, apiRequest, loadJson, reportApiError, saveJson } from './apiRequest';

jest.mock('react-hot-toast', () => ({ __esModule: true, default: { error: jest.fn() } }));

const jsonResponse = (status, body) => ({
  ok: status >= 200 && status < 300,
  status,
  text: async () => JSON.stringify(body),
});

beforeEach(() => {
  jest.clearAllMocks();
  global.fetch = jest.fn();
});

describe('apiRequest', () => {
  test('gibt den Rumpf zurück, wenn der Server zustimmt', async () => {
    global.fetch.mockResolvedValue(jsonResponse(200, { id: 7 }));

    await expect(apiRequest('/api/projects/7')).resolves.toEqual({ id: 7 });
  });

  test('wirft mit übersetzter Meldung, wenn der Server ablehnt', async () => {
    global.fetch.mockResolvedValue(jsonResponse(404, { detail: 'Projekt nicht gefunden' }));

    await expect(apiRequest('/api/projects/7')).rejects.toThrow('Projekt nicht gefunden — bitte Seite neu laden.');
  });

  test('trägt den Statuscode am Fehler', async () => {
    global.fetch.mockResolvedValue(jsonResponse(403, { detail: 'Forbidden' }));

    await expect(apiRequest('/api/projects/7')).rejects.toMatchObject({ status: 403 });
  });

  test('macht aus einem Netzabbruch einen lesbaren Fehler', async () => {
    global.fetch.mockRejectedValue(new TypeError('Failed to fetch'));

    await expect(apiRequest('/api/projects/7')).rejects.toThrow(/Keine Verbindung/);
  });

  test('verträgt eine leere Antwort ohne JSON', async () => {
    global.fetch.mockResolvedValue({ ok: true, status: 204, text: async () => '' });

    await expect(apiRequest('/api/x', { method: 'DELETE' })).resolves.toEqual({});
  });
});

describe('loadJson', () => {
  test('meldet den Fehler und liefert den Ersatzwert', async () => {
    global.fetch.mockResolvedValue(jsonResponse(500, { detail: 'Internal Server Error' }));

    const result = await loadJson('/api/screenshots', {}, { context: 'Screenshots', fallback: [] });

    expect(result).toEqual([]);
    expect(toast.error).toHaveBeenCalledTimes(1);
    expect(toast.error.mock.calls[0][0]).toMatch(/^Screenshots: /);
  });

  test('ein fehlender optionaler Datensatz ist kein Fehler', async () => {
    global.fetch.mockResolvedValue(jsonResponse(404, { detail: 'Not found' }));

    const result = await loadJson('/api/hosting-info', {}, { context: 'Hosting', fallback: null });

    expect(result).toBeNull();
    expect(toast.error).not.toHaveBeenCalled();
  });

  test('404 kann als echter Fehler behandelt werden', async () => {
    global.fetch.mockResolvedValue(jsonResponse(404, { detail: 'Not found' }));

    await loadJson('/api/projects/7', {}, { context: 'Projekt', emptyOn: [] });

    expect(toast.error).toHaveBeenCalledTimes(1);
  });

  test('gleiche Meldungen überlagern sich statt sich zu stapeln', async () => {
    global.fetch.mockResolvedValue(jsonResponse(500, { detail: 'Internal Server Error' }));

    await loadJson('/api/a', {}, { context: 'Screenshots' });
    await loadJson('/api/a', {}, { context: 'Screenshots' });

    expect(toast.error.mock.calls[0][1]).toEqual({ id: 'Screenshots' });
    expect(toast.error.mock.calls[1][1]).toEqual({ id: 'Screenshots' });
  });
});

describe('saveJson', () => {
  test('meldet true, wenn gespeichert wurde', async () => {
    global.fetch.mockResolvedValue(jsonResponse(200, { ok: true }));

    await expect(saveJson('/api/x', { method: 'PATCH' })).resolves.toBe(true);
    expect(toast.error).not.toHaveBeenCalled();
  });

  test('meldet false und ruft onError — dort hängt das Zurücksetzen', async () => {
    global.fetch.mockResolvedValue(jsonResponse(500, { detail: 'Internal Server Error' }));
    const onError = jest.fn();

    const saved = await saveJson('/api/x', { method: 'PATCH' }, { context: 'Checkliste', onError });

    expect(saved).toBe(false);
    expect(onError).toHaveBeenCalledTimes(1);
    expect(toast.error).toHaveBeenCalledTimes(1);
  });
});

describe('reportApiError', () => {
  test('unbekannte Ausnahmen bekommen eine allgemeine, aber sichtbare Meldung', () => {
    reportApiError(new Error('irgendwas Internes'), 'Projekt');

    expect(toast.error).toHaveBeenCalledTimes(1);
    expect(toast.error.mock.calls[0][0]).toMatch(/Projekt: /);
  });

  test('ApiError behält seine Meldung', () => {
    reportApiError(new ApiError('Sitzung abgelaufen', 401));

    expect(toast.error.mock.calls[0][0]).toBe('Sitzung abgelaufen');
  });

  test('axios-Fehler werden genauso übersetzt — die Dateien mischen beides', () => {
    const axiosError = Object.assign(new Error('Request failed'), {
      response: { status: 404, data: { detail: 'Projekt nicht gefunden' } },
    });

    reportApiError(axiosError, 'Kundendaten');

    expect(toast.error.mock.calls[0][0]).toBe('Kundendaten: Projekt nicht gefunden — bitte Seite neu laden.');
  });
});
