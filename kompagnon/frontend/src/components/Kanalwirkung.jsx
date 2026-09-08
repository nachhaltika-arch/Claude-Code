/**
 * „Welcher Kanal bringt Kunden?" — der Bericht aus L-84 bekommt einen Ort.
 *
 * **Warum hier und nicht im Dashboard.** Die Betriebsliste hat seit jeher
 * einen Quellenfilter; sie ist der Bildschirm, auf dem „Herkunft" etwas
 * bedeutet. Was fehlte, ist die Antwort darauf, welcher dieser Filter etwas
 * wert ist — die Zahl lag seit dem 24.08.2026 in `/api/leads/quellen/wirkung`
 * und wurde von keinem Bildschirm abgerufen (L-105, „der Knopf fehlt").
 *
 * **Erst auf Klick geladen.** Wer die Liste öffnet, um einen Betrieb zu
 * suchen, braucht die Auswertung nicht — und soll dafür keine zweite Abfrage
 * bezahlen. Beim Schließen bleibt sie stehen: ein zweites Öffnen lädt nicht
 * erneut.
 *
 * **Ein Ladefehler wird gezeigt, nicht als leere Tabelle ausgegeben.** Eine
 * Auswertung, die aussieht, als hätte kein Kanal gewirkt, ist schlimmer als
 * eine, die sagt, dass sie nicht kommen konnte.
 */
import { useCallback, useState } from 'react';
import API_BASE_URL from '../config';
import { apiRequest } from '../utils/apiRequest';
import { kanaeleAufbereiten, quoteText } from '../utils/kanalwirkung';

const zellStil = { padding: '6px 8px', textAlign: 'left', fontSize: 12 };
const zahlStil = { ...zellStil, textAlign: 'right', fontVariantNumeric: 'tabular-nums' };

export default function Kanalwirkung({ token }) {
  const [offen, setOffen] = useState(false);
  const [daten, setDaten] = useState(null);
  const [laedt, setLaedt] = useState(false);
  const [fehler, setFehler] = useState(null);

  const laden = useCallback(async () => {
    setLaedt(true);
    setFehler(null);
    try {
      const antwort = await apiRequest(`${API_BASE_URL}/api/leads/quellen/wirkung`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      setDaten(kanaeleAufbereiten(antwort));
    } catch (f) {
      setFehler(f.message);
    } finally {
      setLaedt(false);
    }
  }, [token]);

  const umschalten = () => {
    const naechster = !offen;
    setOffen(naechster);
    if (naechster && !daten && !laedt) laden();
  };

  return (
    <div style={{ margin: '4px 0' }}>
      <button
        type="button" onClick={umschalten}
        aria-expanded={offen}
        data-testid="kanalwirkung-schalter"
        style={{
          background: 'none', border: 'none', padding: 0, cursor: 'pointer',
          fontSize: 12, color: 'var(--brand-primary)', fontFamily: 'var(--font-sans)',
          textDecoration: 'underline', minHeight: 32,
        }}
      >
        {offen ? 'Kanalwirkung ausblenden' : 'Welcher Kanal bringt Kunden?'}
      </button>

      {offen && (
        <div style={{
          marginTop: 8, padding: '10px 12px', background: 'var(--bg-app)',
          border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)',
        }}
        >
          {laedt && <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>Wird berechnet…</div>}

          {fehler && (
            <div role="alert" style={{ fontSize: 12, color: 'var(--error)' }}>
              Die Auswertung konnte nicht geladen werden: {fehler}
            </div>
          )}

          {!laedt && !fehler && daten && (
            <>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <caption style={{ ...zellStil, color: 'var(--text-tertiary)', paddingLeft: 0 }}>
                  Nach Wirkung sortiert — Anteil der Betriebe, aus denen Kunden wurden
                </caption>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-light)' }}>
                    <th scope="col" style={zellStil}>Kanal</th>
                    <th scope="col" style={zahlStil}>Betriebe</th>
                    <th scope="col" style={zahlStil}>Kunden</th>
                    <th scope="col" style={zahlStil}>Quote</th>
                  </tr>
                </thead>
                <tbody>
                  {daten.kanaele.map((k) => (
                    <tr key={k.quelle} style={{ borderBottom: '1px solid var(--border-light)' }}>
                      <td style={zellStil}>
                        {k.name}
                        {/* Ein Wert, den der Wortschatz nicht kennt, wird
                            benannt statt stillschweigend mitgezählt: Entweder
                            schreibt ihn jemand ungepflegt, oder der Wortschatz
                            hinkt hinterher. Beides will man wissen. */}
                        {!k.bekannt && (
                          <span style={{ marginLeft: 6, fontSize: 11, color: 'var(--text-tertiary)' }}>
                            (unbekannte Herkunft)
                          </span>
                        )}
                      </td>
                      <td style={zahlStil}>{k.betriebe}</td>
                      <td style={zahlStil}>{k.kunden}</td>
                      <td style={{ ...zahlStil, fontWeight: 700 }}>{quoteText(k.quote)}</td>
                    </tr>
                  ))}
                  {daten.kanaele.length === 0 && (
                    <tr><td colSpan={4} style={zellStil}>Noch kein Betrieb mit Herkunft.</td></tr>
                  )}
                </tbody>
              </table>

              {/* **Beide Zahlen.** Die Summe der Kanäle ist nicht der
                  Gesamtbestand; dazwischen liegen die Betriebe ohne Herkunft.
                  Sie wegzulassen hieße, die Kanalsumme als Gesamt zu lesen. */}
              <p style={{ fontSize: 12, color: 'var(--text-tertiary)', margin: '8px 0 0' }}>
                {daten.summeKanaele} von {daten.gesamt} Betrieben haben eine
                Herkunft · {daten.ohneHerkunft} ohne Angabe
              </p>
            </>
          )}
        </div>
      )}
    </div>
  );
}
