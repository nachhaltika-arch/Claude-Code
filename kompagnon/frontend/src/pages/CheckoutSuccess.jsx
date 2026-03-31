import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import API_BASE_URL from '../config';



export default function CheckoutSuccess() {
  const [searchParams] = useSearchParams();
  const nav = useNavigate();
  const sessionId = searchParams.get('session_id');
  const [session, setSession] = useState(null);

  useEffect(() => {
    if (sessionId) {
      fetch(`${API_BASE_URL}/api/payments/session/${sessionId}`)
        .then((r) => r.json())
        .then(setSession)
        .catch(() => {});
    }
  }, [sessionId]);

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-app)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20, fontFamily: 'var(--font-sans)' }}>
      <div style={{ background: 'var(--bg-surface)', borderRadius: 20, padding: 48, maxWidth: 520, width: '100%', textAlign: 'center', boxShadow: '0 4px 32px rgba(0,0,0,0.10)' }}>
        <div style={{ fontSize: 64, marginBottom: 16 }}>🎉</div>
        <h1 style={{ fontSize: 28, fontWeight: 900, color: 'var(--text-primary)', marginBottom: 12 }}>Zahlung erfolgreich!</h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: 16, lineHeight: 1.6, marginBottom: 24 }}>
          Vielen Dank fuer Ihren Auftrag. Wir melden uns innerhalb von 24 Stunden bei Ihnen.
        </p>

        {session && (
          <div style={{ background: 'var(--status-success-bg)', border: '1px solid #a8e6b8', borderRadius: 'var(--radius-lg)', padding: '16px 20px', marginBottom: 28, textAlign: 'left' }}>
            <div style={{ fontSize: 13, color: 'var(--status-success-text)', fontWeight: 700, marginBottom: 8 }}>Bestellbestaetigung</div>
            <div style={{ fontSize: 13, color: '#4a5a74' }}>
              <div>Betrag: <strong>{session.amount} EUR</strong></div>
              <div>Paket: <strong>{session.package}</strong></div>
              {session.customer_email && <div>E-Mail: <strong>{session.customer_email}</strong></div>}
            </div>
          </div>
        )}

        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <button onClick={() => nav('/login')} style={{ background: 'var(--brand-primary)', color: '#fff', border: 'none', borderRadius: 'var(--radius-md)', padding: 13, fontSize: 15, fontWeight: 700, cursor: 'pointer', minHeight: 48 }}>
            Zum Kundenbereich
          </button>
          <button onClick={() => nav('/')} style={{ background: 'transparent', color: 'var(--text-secondary)', border: 'none', fontSize: 14, cursor: 'pointer' }}>
            Zurueck zur Startseite
          </button>
        </div>
      </div>
    </div>
  );
}
