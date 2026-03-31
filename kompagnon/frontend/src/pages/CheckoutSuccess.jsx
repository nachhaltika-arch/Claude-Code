import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import Logo from '../components/Logo';
import API_BASE_URL from '../config';

const PACKAGE_NAMES = {
  starter: 'Starter',
  kompagnon: 'KOMPAGNON Standard',
  premium: 'Premium',
};

export default function CheckoutSuccess() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const sessionId = params.get('session_id');
  const packageId = params.get('package');
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (sessionId) {
      fetch(`${API_BASE_URL}/api/stripe/session/${sessionId}`)
        .then(r => r.json())
        .then(d => { setSession(d); setLoading(false); })
        .catch(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [sessionId]);

  const pkgName = PACKAGE_NAMES[packageId] || 'Ihr Paket';

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #0f1e3a 0%, #1a3a5c 100%)',
      fontFamily: "'DM Sans', system-ui, sans-serif",
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center', padding: 24,
    }}>
      <style>{`
        @keyframes checkPop { 0% { transform: scale(0); opacity: 0; } 70% { transform: scale(1.2); } 100% { transform: scale(1); opacity: 1; } }
        @keyframes fadeUp { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }
        .check-anim { animation: checkPop 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) both; }
        .content-anim { animation: fadeUp 0.5s 0.4s ease both; }
      `}</style>

      <div style={{ maxWidth: 500, width: '100%', textAlign: 'center' }}>
        <div style={{ marginBottom: 32, cursor: 'pointer' }} onClick={() => navigate('/')}>
          <Logo size="default" />
        </div>

        {loading ? (
          <div style={{ color: 'rgba(255,255,255,0.6)', fontSize: 14 }}>Wird verifiziert...</div>
        ) : (
          <>
            <div className="check-anim" style={{
              width: 80, height: 80, borderRadius: '50%',
              background: 'linear-gradient(135deg, #1a7a3a, #22c55e)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 36, margin: '0 auto 24px', color: 'white',
              boxShadow: '0 8px 32px rgba(34,197,94,0.4)',
            }}>✓</div>

            <div className="content-anim">
              <h1 style={{ fontSize: 28, fontWeight: 700, color: 'white', margin: '0 0 8px', letterSpacing: '-0.02em' }}>
                Zahlung erfolgreich!
              </h1>
              <p style={{ fontSize: 15, color: 'rgba(255,255,255,0.65)', marginBottom: 32, lineHeight: 1.6 }}>
                Vielen Dank für Ihr Vertrauen.{' '}
                {session?.customer_email && (
                  <>Eine Bestätigung wurde an <strong style={{ color: 'white' }}>{session.customer_email}</strong> gesendet.</>
                )}
              </p>

              <div style={{
                background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.15)',
                backdropFilter: 'blur(12px)', borderRadius: 16, padding: '20px 24px',
                marginBottom: 24, textAlign: 'left',
              }}>
                <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 12 }}>
                  Ihre Bestellung
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontSize: 16, fontWeight: 600, color: 'white' }}>{pkgName}</div>
                    {session?.package_name && session.package_name !== pkgName && (
                      <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.5)', marginTop: 2 }}>{session.package_name}</div>
                    )}
                  </div>
                  <div style={{ fontSize: 20, fontWeight: 700, color: '#67d4e8' }}>
                    {session?.amount ? `${(session.amount / 100).toLocaleString('de-DE')} €` : '—'}
                  </div>
                </div>
              </div>

              <div style={{
                background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: 16, padding: '20px 24px', marginBottom: 28, textAlign: 'left',
              }}>
                <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 14 }}>
                  Wie geht es weiter?
                </div>
                {[
                  { icon: '📧', text: 'Sie erhalten eine Auftragsbestätigung per E-Mail' },
                  { icon: '📞', text: 'Wir melden uns innerhalb von 24h für den Projekt-Kickoff' },
                  { icon: '🚀', text: 'Ihr Projekt startet — wir halten Sie auf dem Laufenden' },
                  { icon: '✅', text: 'Fertigstellung gemäß vereinbarter Lieferzeit' },
                ].map((s, i) => (
                  <div key={i} style={{ display: 'flex', gap: 12, marginBottom: i < 3 ? 12 : 0 }}>
                    <span style={{ fontSize: 16, flexShrink: 0 }}>{s.icon}</span>
                    <span style={{ fontSize: 13, color: 'rgba(255,255,255,0.7)', lineHeight: 1.5 }}>{s.text}</span>
                  </div>
                ))}
              </div>

              <button onClick={() => window.location.href = 'https://www.kompagnon.eu'} style={{
                padding: '12px 28px', background: '#008eaa', color: 'white', border: 'none',
                borderRadius: 12, fontSize: 14, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit',
              }}>
                Zurück zu KOMPAGNON →
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
