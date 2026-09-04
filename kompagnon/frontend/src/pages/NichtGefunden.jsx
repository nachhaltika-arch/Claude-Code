import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import SeitenTitel from '../components/ui/SeitenTitel';

/**
 * Was bei einer unbekannten Adresse passiert (27.08.2026).
 *
 * **Vorher landete jeder unbekannte Pfad auf `/login`.** Wer sich vertippt
 * oder einem alten Lesezeichen folgt, sah die Anmeldemaske — und schloss
 * daraus, er sei abgemeldet worden. David ist genau darüber gestolpert:
 * `/app/admin/rollen` gibt es nicht (die Rollenverwaltung liegt unter
 * `/app/settings/roles`), und die Antwort darauf war ein Anmeldebildschirm.
 *
 * Das ist die Fehlerklasse aus L-64: **ein Weg, der still bei der Anmeldung
 * endet.** Eine falsche Adresse ist etwas anderes als eine abgelaufene
 * Sitzung, und die Seite muss beides auseinanderhalten.
 *
 * **Wer angemeldet ist, wird nicht ausgeloggt** — er bekommt einen Weg
 * zurück. Wer es nicht ist, wird zur Anmeldung geschickt, aber mit dem
 * Grund davor.
 */
export default function NichtGefunden() {
  const nav = useNavigate();
  const ort = useLocation();
  const { user } = useAuth();

  return (
    <div style={{
      minHeight: '100vh', background: 'var(--bg-app)', fontFamily: 'var(--font-sans)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20,
    }}>
      <SeitenTitel>Seite nicht gefunden</SeitenTitel>
      <div style={{
        width: '100%', maxWidth: 520, background: 'var(--bg-surface)',
        border: '1px solid var(--border-light)', borderRadius: 12, padding: 32,
      }}>
        <div style={{ fontSize: 40, marginBottom: 12 }} aria-hidden="true">🧭</div>
        <h1 style={{ fontSize: 22, fontWeight: 800, color: 'var(--text-primary)', margin: '0 0 10px' }}>
          Diese Seite gibt es nicht
        </h1>

        <p style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.75, margin: 0 }}>
          Die Adresse{' '}
          <code style={{
            background: 'var(--bg-app)', padding: '2px 6px', borderRadius: 4,
            fontSize: 13, wordBreak: 'break-all',
          }}>
            {ort.pathname}
          </code>{' '}
          führt nirgendwohin.
          {user
            ? ' Sie sind weiterhin angemeldet — es ist nur der Weg, den es nicht gibt.'
            : ' Möglicherweise müssen Sie sich zuerst anmelden.'}
        </p>

        <div style={{ display: 'flex', gap: 10, marginTop: 24, flexWrap: 'wrap' }}>
          <button
            onClick={() => nav(user ? '/app/dashboard' : '/login')}
            style={{
              flex: 1, minWidth: 180, background: 'var(--kc-dark)',
              color: 'var(--text-inverse)', border: 'none', borderRadius: 8,
              padding: '12px 20px', fontSize: 15, fontWeight: 700,
              cursor: 'pointer', minHeight: 48,
            }}
          >
            {user ? 'Zum Dashboard' : 'Zur Anmeldung'}
          </button>
          <button
            onClick={() => nav(-1)}
            style={{
              background: 'var(--bg-app)', color: 'var(--text-primary)',
              border: 'none', borderRadius: 8, padding: '12px 18px',
              fontSize: 14, cursor: 'pointer', minHeight: 48,
            }}
          >
            Zurück
          </button>
        </div>
      </div>
    </div>
  );
}
