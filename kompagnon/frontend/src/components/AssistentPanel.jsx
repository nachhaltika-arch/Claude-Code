/**
 * Der Projekt-Assistent — eine Komponente, zwei Einbauorte.
 *
 * Entscheidung 3.1 der Anforderungen: fester Bereich neben den Briefing-Feldern,
 * aufklappbares Widget im Kundenportal. Beides dieselbe Technik; `kompakt`
 * schaltet auf die schmale Darstellung um, die auf dem Telefon vollwertig
 * bedienbar bleibt — das Portal wird überwiegend mobil genutzt.
 *
 * Was diese Komponente bewusst **nicht** tut: selbst ins Briefing schreiben.
 * Entscheidung 1.3 — der Assistent schlägt vor, der Mensch übernimmt per Klick.
 * Deshalb reicht sie einen Vorschlag über `onUebernehmen` nach oben und ändert
 * nichts von sich aus.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import API_BASE_URL from '../config';
import { useAuth } from '../context/AuthContext';
import { hinweisSchluessel, zeigeHinweis } from '../utils/assistentUebernahme';

const LILA = '#7c3aed';
const LILA_HELL = '#faf5ff';
const LILA_RAND = '#d8b4fe';

// Unten rechts sitzt bereits der Support-Chat (52 px, 24 px Abstand). Der
// Assistent stapelt sich darüber, statt sich mit ihm zu überlagern.
const ABSTAND_UNTEN = 88;

export default function AssistentPanel({
  leadId,
  projektId = null,
  feld = '',
  schritt = '',
  wert = '',
  onUebernehmen,
  kompakt = false,
  titel = 'Assistent',
}) {
  const { token } = useAuth();
  const headers = useMemo(
    () => ({ 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) }),
    [token],
  );

  const [offen, setOffen] = useState(!kompakt);
  const [verlauf, setVerlauf] = useState([]);
  const [frage, setFrage] = useState('');
  const [laeuft, setLaeuft] = useState(false);
  const [fehler, setFehler] = useState('');
  const [hinweis, setHinweis] = useState('');
  const [vorschlag, setVorschlag] = useState(null);
  const [gespraech, setGespraech] = useState(null);
  const [eskaliert, setEskaliert] = useState(false);
  const [feldHinweis, setFeldHinweis] = useState('');

  // Ein Hinweis, den der Nutzer schon gesehen hat, erscheint nicht wieder —
  // § 2.3 verlangt ausdrücklich eine Ablage dafür.
  const gesehen = useRef(new Set());
  const ende = useRef(null);

  useEffect(() => {
    if (ende.current) ende.current.scrollIntoView({ block: 'nearest' });
  }, [verlauf, laeuft]);

  // ── Proaktiver Hinweis zum aktiven Feld (ohne Modellaufruf) ──────────────
  const pruefeFeld = useCallback(async () => {
    if (!feld) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/assistant/field-check`, {
        method: 'POST', headers, body: JSON.stringify({ feld, wert }),
      });
      if (!res.ok) return;
      const befund = await res.json();
      const text = zeigeHinweis(feld, befund, gesehen.current);
      if (!text) {
        setFeldHinweis('');
        return;
      }
      gesehen.current.add(hinweisSchluessel(feld, befund.hinweise));
      setFeldHinweis(text);
    } catch {
      // Ein ausgefallener Hinweis ist kein Fehler, den der Nutzer sehen muss.
      setFeldHinweis('');
    }
  }, [feld, wert, headers]);

  useEffect(() => { setFeldHinweis(''); }, [feld]);

  const fragen = async (text) => {
    const gestellt = (text ?? frage).trim();
    if (!gestellt || laeuft) return;
    setLaeuft(true);
    setFehler('');
    setVorschlag(null);
    setVerlauf((v) => [...v, { rolle: 'nutzer', inhalt: gestellt }]);
    setFrage('');
    try {
      const res = await fetch(`${API_BASE_URL}/api/assistant/chat`, {
        method: 'POST', headers,
        body: JSON.stringify({
          lead_id: leadId, projekt_id: projektId, frage: gestellt,
          feld, schritt, conversation_id: gespraech,
        }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = body?.detail;
        throw new Error(typeof detail === 'string' ? detail : `Fehler ${res.status}`);
      }
      setGespraech(body.conversation_id);
      setVerlauf((v) => [...v, { rolle: 'assistent', inhalt: body.antwort }]);
      setHinweis(body.hinweis || '');
      if (body.vorschlag) setVorschlag({ text: body.vorschlag, feld: body.feld || feld });
    } catch (e) {
      setFehler(e.message || 'Der Assistent ist gerade nicht erreichbar.');
    } finally {
      setLaeuft(false);
    }
  };

  const anTeam = async () => {
    if (!gespraech || eskaliert) return;
    // Steht nichts im Eingabefeld, ist das Anliegen die zuletzt gestellte
    // Frage — sonst landet beim Team eine Nachricht ohne Betreff.
    const letzteFrage = [...verlauf].reverse().find((n) => n.rolle === 'nutzer');
    const anliegen = frage.trim() || letzteFrage?.inhalt || '';
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/assistant/conversations/${gespraech}/escalate`,
        { method: 'POST', headers, body: JSON.stringify({ anliegen }) },
      );
      if (!res.ok) throw new Error(`Fehler ${res.status}`);
      setEskaliert(true);
      setVerlauf((v) => [...v, {
        rolle: 'system',
        inhalt: 'Ihre Frage liegt jetzt beim Team — wir melden uns persönlich.',
      }]);
    } catch (e) {
      setFehler(e.message || 'Die Übergabe hat nicht geklappt.');
    }
  };

  if (kompakt && !offen) {
    return (
      <button
        type="button" onClick={() => setOffen(true)}
        style={{
          position: 'fixed', right: 16, bottom: ABSTAND_UNTEN, zIndex: 900,
          background: LILA, color: '#fff', border: 'none', borderRadius: 999,
          padding: '12px 18px', fontSize: 13, fontWeight: 700,
          fontFamily: 'inherit', cursor: 'pointer',
          boxShadow: '0 6px 20px rgba(124,58,237,0.35)',
        }}
      >✨ {titel}</button>
    );
  }

  return (
    <aside
      aria-label="Projekt-Assistent"
      style={{
        display: 'flex', flexDirection: 'column',
        background: LILA_HELL, border: `1px solid ${LILA_RAND}`, borderRadius: 10,
        fontFamily: 'inherit',
        ...(kompakt ? {
          position: 'fixed', right: 12, bottom: ABSTAND_UNTEN, zIndex: 900,
          width: 'min(380px, calc(100vw - 24px))', maxHeight: 'min(70vh, 560px)',
          boxShadow: '0 12px 40px rgba(0,0,0,0.18)',
        } : { height: '100%', minHeight: 320 }),
      }}
    >
      <header style={{
        display: 'flex', alignItems: 'center', gap: 8, padding: '10px 12px',
        borderBottom: `1px solid ${LILA_RAND}`,
      }}>
        <span style={{ fontSize: 12, fontWeight: 800, color: '#6b21a8',
                       textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          ✨ {titel}
        </span>
        <span style={{ flex: 1 }} />
        {kompakt && (
          <button type="button" onClick={() => setOffen(false)} aria-label="Schließen"
            style={{ background: 'none', border: 'none', cursor: 'pointer',
                     fontSize: 18, lineHeight: 1, color: '#6b21a8' }}>×</button>
        )}
      </header>

      <div style={{ flex: 1, overflowY: 'auto', padding: 12, display: 'flex',
                    flexDirection: 'column', gap: 10, minHeight: 0 }}>
        {verlauf.length === 0 && !feldHinweis && (
          <p style={{ fontSize: 12, color: '#6b21a8', margin: 0, lineHeight: 1.5 }}>
            Fragen Sie mich zu jedem Feld — warum es gebraucht wird und wie eine
            gute Antwort aussieht. Ich fülle nichts selbst aus; Sie übernehmen
            meinen Vorschlag per Klick.
          </p>
        )}

        {feldHinweis && (
          <div style={{
            fontSize: 12, lineHeight: 1.5, padding: 10, borderRadius: 8,
            background: '#FEF3C7', border: '1px solid #FCD34D', color: '#92400e',
          }}>
            {feldHinweis}
            <button
              type="button"
              onClick={() => fragen(`Wie formuliere ich „${feld}" besser?`)}
              style={{
                display: 'block', marginTop: 6, background: 'none', border: 'none',
                padding: 0, color: '#92400e', fontWeight: 700, fontSize: 12,
                textDecoration: 'underline', cursor: 'pointer', fontFamily: 'inherit',
              }}
            >Vorschlag dazu anfordern</button>
          </div>
        )}

        {verlauf.map((n, i) => (
          <div
            key={`${n.rolle}-${i}`}
            style={{
              alignSelf: n.rolle === 'nutzer' ? 'flex-end' : 'flex-start',
              maxWidth: '92%',
              background: n.rolle === 'nutzer' ? LILA
                : n.rolle === 'system' ? '#dcfce7' : '#fff',
              color: n.rolle === 'nutzer' ? '#fff'
                : n.rolle === 'system' ? '#166534' : '#3b0764',
              border: n.rolle === 'assistent' ? `1px solid ${LILA_RAND}` : 'none',
              borderRadius: 10, padding: '8px 10px', fontSize: 12.5, lineHeight: 1.5,
              whiteSpace: 'pre-wrap',
            }}
          >{n.inhalt}</div>
        ))}

        {laeuft && (
          <div style={{ fontSize: 12, color: '#6b21a8' }}>Der Assistent überlegt…</div>
        )}

        {/* Ohne Übernahmeziel — etwa im Kundenportal — wird der Vorschlag
            trotzdem gezeigt. Sonst verschwände der halbe Rat des Assistenten,
            weil ihn niemand in ein Feld schreiben kann. */}
        {vorschlag && !onUebernehmen && (
          <div style={{
            alignSelf: 'flex-start', maxWidth: '92%', background: '#fff',
            border: `1px solid ${LILA_RAND}`, borderLeft: `3px solid ${LILA}`,
            borderRadius: 10, padding: '8px 10px', fontSize: 12.5,
            lineHeight: 1.5, color: '#3b0764', whiteSpace: 'pre-wrap',
          }}>{vorschlag.text}</div>
        )}

        {vorschlag && onUebernehmen && (
          <div style={{
            background: '#fff', border: `1px solid ${LILA_RAND}`, borderRadius: 8,
            padding: 10, display: 'flex', flexDirection: 'column', gap: 8,
          }}>
            <div style={{ fontSize: 10, fontWeight: 800, color: '#6b21a8',
                          textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Vorschlag für „{vorschlag.feld || feld}"
            </div>
            <div style={{ fontSize: 12.5, color: '#3b0764', lineHeight: 1.5 }}>
              {vorschlag.text}
            </div>
            <div style={{ display: 'flex', gap: 6 }}>
              <button
                type="button"
                onClick={() => { onUebernehmen(vorschlag.text, vorschlag.feld); setVorschlag(null); }}
                style={{
                  flex: 1, padding: '7px 10px', background: '#10b981', color: '#fff',
                  border: 'none', borderRadius: 6, fontSize: 11.5, fontWeight: 700,
                  cursor: 'pointer', fontFamily: 'inherit',
                }}
              >✓ Übernehmen</button>
              <button
                type="button" onClick={() => setVorschlag(null)}
                style={{
                  padding: '7px 10px', background: '#fff', border: '1px solid #cbd5e1',
                  borderRadius: 6, fontSize: 11.5, fontWeight: 700, cursor: 'pointer',
                  fontFamily: 'inherit',
                }}
              >Verwerfen</button>
            </div>
          </div>
        )}

        {hinweis && (
          <div style={{ fontSize: 11, color: '#92400e' }}>{hinweis}</div>
        )}
        {fehler && (
          <div style={{
            fontSize: 12, padding: 8, borderRadius: 6, background: '#fef2f2',
            border: '1px solid #fca5a5', color: '#991b1b',
          }}>{fehler}</div>
        )}
        <div ref={ende} />
      </div>

      <div style={{ padding: 10, borderTop: `1px solid ${LILA_RAND}`,
                    display: 'flex', flexDirection: 'column', gap: 6 }}>
        <div style={{ display: 'flex', gap: 6 }}>
          <input
            type="text" value={frage} onChange={(e) => setFrage(e.target.value)}
            onFocus={pruefeFeld}
            onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); fragen(); } }}
            placeholder={feld ? `Frage zu „${feld}"…` : 'Ihre Frage…'}
            aria-label="Frage an den Assistenten"
            style={{
              flex: 1, minWidth: 0, padding: '8px 10px', borderRadius: 6,
              border: `1px solid ${LILA_RAND}`, fontSize: 12.5, fontFamily: 'inherit',
              outline: 'none',
            }}
          />
          <button
            type="button" onClick={() => fragen()} disabled={laeuft || !frage.trim()}
            style={{
              padding: '8px 14px', background: laeuft || !frage.trim() ? '#c4b5fd' : LILA,
              color: '#fff', border: 'none', borderRadius: 6, fontSize: 12,
              fontWeight: 700, fontFamily: 'inherit',
              cursor: laeuft || !frage.trim() ? 'not-allowed' : 'pointer',
            }}
          >Fragen</button>
        </div>
        {/* Der Weg zum Menschen ist immer sichtbar — Entscheidung 4.2. */}
        <button
          type="button" onClick={anTeam} disabled={!gespraech || eskaliert}
          style={{
            background: 'none', border: 'none', padding: 0, textAlign: 'left',
            fontSize: 11, fontFamily: 'inherit',
            color: !gespraech || eskaliert ? '#a78bfa' : '#6b21a8',
            textDecoration: 'underline',
            cursor: !gespraech || eskaliert ? 'default' : 'pointer',
          }}
        >
          {eskaliert ? 'Ihre Frage liegt beim Team.' : 'Lieber einen Menschen fragen'}
        </button>
      </div>
    </aside>
  );
}
