/**
 * Fetch-Helfer, der Fehler sichtbar macht.
 *
 * Warum es das gibt: Das Frontend hatte 83 leere catch-Bloecke. Ein Ladefehler
 * fuehrte damit zu einer leeren Ansicht ohne jeden Hinweis — vier der fuenf
 * Fehler, die am 07./08.08.2026 gefunden wurden, waren deshalb monatelang
 * unsichtbar (Lücke L-36).
 *
 * Drei Ebenen, je nach Aufrufer:
 *   apiRequest  — wirft. Fuer Aufrufer, die den Fehler selbst behandeln.
 *   loadJson    — meldet und liefert einen Ersatzwert. Fuer Lade-Pfade.
 *   saveJson    — meldet und liefert true/false. Fuer Speichern im Hintergrund.
 */
import toast from 'react-hot-toast';

import { parseApiError, parseResponseJson } from './apiError';

const NETWORK_ERROR_MESSAGE = 'Keine Verbindung zum Server — bitte Internetverbindung prüfen.';
const UNEXPECTED_ERROR_MESSAGE = 'Unerwarteter Fehler — bitte Seite neu laden.';
const NETWORK_ERROR_STATUS = 0;

/** Ein Fehler, dessen Meldung bereits fuer die Anzeige uebersetzt ist. */
export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

/**
 * @param {string} url
 * @param {RequestInit} [options]
 * @returns {Promise<any>} Rumpf der Antwort; {} bei leerem Rumpf
 * @throws {ApiError} bei Netzfehler oder Status >= 400
 */
export async function apiRequest(url, options = {}) {
  let response;
  try {
    response = await fetch(url, options);
  } catch {
    throw new ApiError(NETWORK_ERROR_MESSAGE, NETWORK_ERROR_STATUS);
  }

  const data = await parseResponseJson(response);
  if (!response.ok) {
    throw new ApiError(parseApiError(data, response.status), response.status);
  }
  return data;
}

function messageFor(error) {
  if (error instanceof ApiError) return error.message;
  // axios legt die Serverantwort unter error.response ab. Diese Dateien mischen
  // axios und fetch, also muss beides hier ankommen koennen.
  if (error?.response) return parseApiError(error.response.data, error.response.status);
  return UNEXPECTED_ERROR_MESSAGE;
}

/**
 * Zeigt einen Fehler an. Gleiche Meldungen ueberlagern sich, statt sich zu
 * stapeln — sonst begraebt ein Serverausfall den Bildschirm unter Toasts.
 */
export function reportApiError(error, context) {
  const message = messageFor(error);
  const text = context ? `${context}: ${message}` : message;
  toast.error(text, { id: context || text });
}

/**
 * Laden mit Ersatzwert. `emptyOn` nennt die Status, die einen legitimen
 * Leerzustand bedeuten — ein noch nicht angelegter Datensatz ist kein Fehler
 * und darf den Nutzer nicht behelligen.
 *
 * `quiet` schweigt bewusst. Nur fuer Nebensaechliches, dessen Ausfall an
 * anderer Stelle ohnehin auffaellt: ein Keepalive-Ping, ein Titel in der
 * Brotkrumenleiste. Der Schalter existiert, damit solche Faelle im Code
 * benannt und auffindbar sind, statt als leeres catch zu verschwinden.
 */
export async function loadJson(
  url,
  options = {},
  { context, fallback = null, emptyOn = [404], quiet = false } = {},
) {
  try {
    return await apiRequest(url, options);
  } catch (error) {
    if (quiet) return fallback;
    if (error instanceof ApiError && emptyOn.includes(error.status)) return fallback;
    reportApiError(error, context);
    return fallback;
  }
}

/**
 * Speichern im Hintergrund. `onError` ist der Platz fuer das Zuruecksetzen
 * einer optimistisch gesetzten Anzeige.
 *
 * @returns {Promise<boolean>} ob gespeichert wurde
 */
export async function saveJson(url, options = {}, { context, onError } = {}) {
  try {
    await apiRequest(url, options);
    return true;
  } catch (error) {
    reportApiError(error, context);
    if (onError) onError(error);
    return false;
  }
}
