import React, { useEffect, useRef, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import API_BASE_URL from '../config';
import SeitenTitel from '../components/ui/SeitenTitel';
import { aufTaste } from '../utils/tastaturBedienung';

const AMBER = 'var(--brand-accent)';

/**
 * Die Seite, auf der der Link aus der Bestaetigungsmail landet.
 *
 * **Warum es sie gibt (27.08.2026).** `POST /api/auth/verify-email` gab es
 * seit jeher — mit **keinem einzigen Aufrufer**, weder in der Oberflaeche
 * noch in den E2E-Tests. Die Mail, die dorthin haette fuehren sollen, wurde
 * ebenfalls nie verschickt. Beide Haelften waren gebaut und keine mit der
 * anderen verbunden.
 *
 * Der Link zeigt auf **diese Seite** und nicht auf die Schnittstelle: Wer in
 * einer Mail auf einen Knopf drueckt, soll auf einer Seite landen, die ihm
 * etwas sagt, und nicht auf einer JSON-Antwort.
 */
export default function EmailBestaetigen() {
  const nav = useNavigate();
  const [suchParameter] = useSearchParams();
  const token = suchParameter.get('token');
  const [zustand, setZustand] = useState(token ? 'laeuft' : 'ohne-token');
  const [meldung, setMeldung] = useState('');

  // React 18 ruft Effekte im Entwicklungsmodus zweimal auf. Der Token ist ein
  // Einmalschluessel — der zweite Aufruf bekaeme 400, und der Mensch saehe
  // „Link ungueltig", obwohl seine Bestaetigung gerade geklappt hat.
  const bereitsGesendet = useRef(false);

  useEffect(() => {
    if (!token || bereitsGesendet.current) return;
    bereitsGesendet.current = true;

    (async () => {
      try {
        const antwort = await fetch(
          `${API_BASE_URL}/api/auth/verify-email?token=${encodeURIComponent(token)}`,
          { method: 'POST' },
        );
        if (antwort.ok) { setZustand('fertig'); return; }
        const daten = await antwort.json().catch(() => ({}));
        setMeldung(daten.detail || '');
        setZustand('ungueltig');
      } catch {
        setZustand('fehler');
      }
    })();
  }, [token]);

  const texte = {
    'laeuft':     { symbol: '⏳', titel: 'Einen Moment…', text: 'Wir bestaetigen Ihre E-Mail-Adresse.' },
    'fertig':     { symbol: '✅', titel: 'E-Mail bestaetigt', text: 'Danke — Ihre Adresse ist bestaetigt. Sie koennen sich jetzt anmelden.' },
    'ungueltig':  { symbol: '⚠️', titel: 'Dieser Link gilt nicht mehr', text: meldung || 'Der Link laesst sich genau einmal verwenden. Moeglicherweise haben Sie Ihre Adresse bereits bestaetigt — versuchen Sie einfach, sich anzumelden.' },
    'ohne-token': { symbol: '⚠️', titel: 'Es fehlt der Bestaetigungscode', text: 'Bitte oeffnen Sie den Link direkt aus der E-Mail, die wir Ihnen geschickt haben.' },
    'fehler':     { symbol: '⚠️', titel: 'Verbindung fehlgeschlagen', text: 'Wir konnten den Server gerade nicht erreichen. Bitte laden Sie die Seite neu.' },
  }[zustand];

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-app)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20, fontFamily: 'var(--font-sans)' }}>
      <SeitenTitel>E-Mail bestaetigen</SeitenTitel>
      <div style={{ width: '100%', maxWidth: 420 }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div
            role="button"
            tabIndex={0}
            onKeyDown={aufTaste(() => nav('/'))}
            onClick={() => nav('/')}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 10, cursor: 'pointer' }}
          >
            <div style={{ width: 44, height: 44, borderRadius: '50%', background: 'var(--brand-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <span style={{ color: AMBER, fontWeight: 900, fontSize: 14 }}>HS</span>
            </div>
            <span style={{ fontSize: 22, fontWeight: 800, color: 'var(--text-primary)' }}>KOMPAGNON</span>
          </div>
        </div>

        <div style={{ background: 'var(--bg-surface)', borderRadius: 'var(--radius-xl)', padding: 32, boxShadow: '0 4px 24px rgba(15,30,58,0.10)', textAlign: 'center' }}>
          <div style={{ fontSize: 48, marginBottom: 16 }} aria-hidden="true">{texte.symbol}</div>
          <h2 style={{ color: 'var(--text-primary)', marginBottom: 8, fontSize: 22, fontWeight: 800 }}>{texte.titel}</h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: 24, fontSize: 14, lineHeight: 1.7 }}>{texte.text}</p>

          {zustand !== 'laeuft' && (
            <button
              onClick={() => nav('/login')}
              style={{
                width: '100%', background: 'var(--brand-primary)', color: 'var(--text-on-brand)',
                border: 'none', borderRadius: 'var(--radius-md)', padding: '13px 28px',
                fontSize: 15, fontWeight: 700, cursor: 'pointer', minHeight: 48,
              }}
            >
              Zur Anmeldung
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
