/**
 * Der Zustand des Not-Aus fuer automatischen Mailversand — einmal geladen,
 * an zwei Stellen gezeigt.
 *
 * Warum ein Kontext und nicht zwei Abfragen: Der Schalter steht in den
 * Einstellungen, angezeigt wird er im Menue. Zwei getrennte Abfragen liefen
 * nach dem Umlegen auseinander — die Einstellungen saegten „aus", das Menue
 * zeigte weiter „an". Ein Schalter, dessen Anzeige hinterherhinkt, ist
 * schlimmer als keiner.
 *
 * Siehe `backend/services/versandsperre.py` fuer den Anlass.
 */
import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useAuth } from './AuthContext';
import API_BASE_URL from '../config';
import { apiRequest, loadJson } from '../utils/apiRequest';

const VersandContext = createContext(null);

export function VersandProvider({ children }) {
  const { token } = useAuth();
  const [erlaubt, setErlaubt] = useState(null); // null = noch unbekannt
  const [laedt, setLaedt] = useState(true);

  const kopf = useCallback(
    () => ({ 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) }),
    [token],
  );

  const laden = useCallback(async () => {
    if (!token) { setErlaubt(null); setLaedt(false); return; }
    setLaedt(true);
    // quiet: Der Zustand haengt im Menue. Scheitert die Abfrage, ist das kein
    // Grund, dem Nutzer bei jedem Seitenwechsel eine Meldung hinzuwerfen —
    // die Anzeige sagt dann „unbekannt", und das ist ehrlich.
    const antwort = await loadJson(`${API_BASE_URL}/api/versand/status`, { headers: kopf() }, { quiet: true });
    setErlaubt(typeof antwort?.erlaubt === 'boolean' ? antwort.erlaubt : null);
    setLaedt(false);
  }, [token, kopf]);

  useEffect(() => { laden(); }, [laden]);

  /** Legt den Schalter um. Wirft bei Fehlschlag — der Aufrufer meldet ihn. */
  const umschalten = useCallback(async (neuerWert) => {
    const antwort = await apiRequest(`${API_BASE_URL}/api/versand/status`, {
      method: 'PUT',
      headers: kopf(),
      body: JSON.stringify({ erlaubt: neuerWert }),
    });
    setErlaubt(Boolean(antwort?.erlaubt));
    return Boolean(antwort?.erlaubt);
  }, [kopf]);

  return (
    <VersandContext.Provider value={{ erlaubt, laedt, laden, umschalten }}>
      {children}
    </VersandContext.Provider>
  );
}

/**
 * @returns {{erlaubt: boolean|null, laedt: boolean, laden: Function, umschalten: Function}}
 *   `erlaubt === null` heisst „nicht bekannt" — nicht „aus". Der Unterschied
 *   gehoert in die Anzeige, nicht unter den Teppich.
 */
export const useVersand = () => useContext(VersandContext) || { erlaubt: null, laedt: false, laden: () => {}, umschalten: async () => {} };
