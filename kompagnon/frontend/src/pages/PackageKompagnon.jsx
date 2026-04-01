import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import Logo from '../components/Logo';
import API_BASE_URL from '../config';

export default function PackageKompagnon() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const cancelled = params.get('cancelled');
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleCheckout = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE_URL}/api/stripe/create-checkout-session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ package: 'kompagnon', email }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail);
      window.location.href = data.checkout_url;
    } catch {
      setError('Checkout konnte nicht gestartet werden.');
      setLoading(false);
    }
  };

  const FEATURES = [
    'Professionelle Handwerker-Website',
    'Responsive Design (Mobil + Desktop)',
    'Rechtlich konform (DSGVO, Impressum)',
    'SSL-Zertifikat & Hosting-Setup',
    'Google Maps Integration',
    'Kontaktformular',
    'Persönlicher Strategie-Workshop',
    'SEO + GEO Volloptimierung',
    'Google Business Optimierung',
    'Wettbewerbs- & Sichtbarkeitsanalyse',
    'Content-Erstellung durch KI + Redaktion',
    'Eine Korrekturschleife',
    'Nachbetreuung nach Go-Live',
  ];

  return (
    <div style={{ minHeight: '100vh', background: '#f4f6f8', fontFamily: "'DM Sans', system-ui, sans-serif" }}>
      <style>{`
        @keyframes fadeUp { from { opacity:0; transform:translateY(16px); } to { opacity:1; transform:translateY(0); } }
        .fade1 { animation: fadeUp 0.5s ease both; }
        .fade2 { animation: fadeUp 0.5s 0.1s ease both; }
        .fade3 { animation: fadeUp 0.5s 0.2s ease both; }
        .fade4 { animation: fadeUp 0.5s 0.3s ease both; }
        .cta-btn:hover { background: #b8860b !important; transform: translateY(-1px); box-shadow: 0 8px 24px rgba(212,160,23,0.4) !important; }
        .cta-btn { transition: all 0.2s ease !important; }
        input:focus { border-color: #d4a017 !important; box-shadow: 0 0 0 3px rgba(212,160,23,0.12) !important; outline: none !important; }
      `}</style>

      <nav style={{ background: 'white', borderBottom: '1px solid #e8eef2', padding: '14px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', position: 'sticky', top: 0, zIndex: 50 }}>
        <div style={{ cursor: 'pointer' }} onClick={() => navigate('/')}><Logo size="small" /></div>
        <div style={{ display: 'flex', gap: 8 }}>
          {[
            { label: 'Starter', path: '/paket/starter' },
            { label: 'KOMPAGNON', path: '/paket/kompagnon', active: true },
            { label: 'Premium', path: '/paket/premium' },
          ].map(p => (
            <button key={p.label} onClick={() => navigate(p.path)} style={{
              padding: '5px 14px', borderRadius: 20, border: 'none',
              background: p.active ? '#d4a017' : 'transparent',
              color: p.active ? 'white' : '#8fa8b0',
              fontSize: 12, fontWeight: p.active ? 600 : 400, cursor: 'pointer', fontFamily: 'inherit',
            }}>{p.label}</button>
          ))}
        </div>
      </nav>

      {cancelled && (
        <div style={{ background: '#fff8e6', borderBottom: '1px solid #fde68a', padding: '12px 24px', textAlign: 'center', fontSize: 13, color: '#a06800' }}>
          Zahlung abgebrochen — kein Betrag wurde berechnet.
        </div>
      )}

      <div style={{ background: 'linear-gradient(135deg, #1a1000 0%, #3a2800 100%)', padding: '60px 24px 80px', textAlign: 'center', position: 'relative', overflow: 'hidden' }}>
        <div style={{ position: 'absolute', inset: 0, backgroundImage: 'radial-gradient(circle at 30% 50%, rgba(212,160,23,0.15) 0%, transparent 60%)' }} />
        <div style={{ position: 'relative', maxWidth: 640, margin: '0 auto' }}>
          <div className="fade1" style={{ display: 'inline-block', background: 'rgba(212,160,23,0.25)', border: '1px solid rgba(212,160,23,0.5)', color: '#fde68a', borderRadius: 20, padding: '4px 14px', fontSize: 11, fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 16 }}>
            ⭐ Empfohlen
          </div>
          <h1 className="fade2" style={{ fontSize: 'clamp(28px, 5vw, 44px)', fontWeight: 700, color: 'white', margin: '0 0 16px', lineHeight: 1.2, letterSpacing: '-0.02em' }}>
            Das Komplett-Paket<br />für Ihren Betrieb.
          </h1>
          <p className="fade3" style={{ fontSize: 16, color: 'rgba(255,255,255,0.65)', maxWidth: 480, margin: '0 auto 32px', lineHeight: 1.6 }}>
            Website, SEO, Google Business und Strategie-Workshop — alles aus einer Hand für maximale Sichtbarkeit.
          </p>
          <div className="fade4" style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'center', gap: 8 }}>
            <span style={{ fontSize: 52, fontWeight: 700, color: '#fde68a', letterSpacing: '-0.03em' }}>2.000 €</span>
            <span style={{ fontSize: 14, color: 'rgba(255,255,255,0.5)' }}>netto</span>
          </div>
          <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.45)', marginTop: 4 }}>14 Werktage · Vorkasse · zzgl. MwSt.</div>
        </div>
      </div>

      <div style={{ maxWidth: 880, margin: '0 auto', padding: '0 20px 80px', marginTop: -40 }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 20, alignItems: 'flex-start' }}>
          <div style={{ background: 'white', borderRadius: 20, padding: 32, boxShadow: '0 8px 40px rgba(212,160,23,0.15)', border: '2px solid #d4a017' }}>
            <div style={{ display: 'inline-block', background: '#d4a017', color: 'white', fontSize: 10, fontWeight: 700, padding: '3px 10px', borderRadius: 10, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 12 }}>Empfohlen</div>
            <div style={{ fontSize: 18, fontWeight: 700, color: '#0f1c20', marginBottom: 4 }}>KOMPAGNON Standard — 2.000 € netto</div>
            <div style={{ fontSize: 12, color: '#8fa8b0', marginBottom: 24 }}>Einmalige Zahlung · keine laufenden Kosten</div>
            {error && <div style={{ background: '#fef0f0', color: '#b02020', borderRadius: 8, padding: '10px 12px', fontSize: 12, marginBottom: 16 }}>{error}</div>}
            <form onSubmit={handleCheckout}>
              <div style={{ marginBottom: 16 }}>
                <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: '#8fa8b0', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>Ihre geschäftliche E-Mail</label>
                <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="kontakt@ihrbetrieb.de" required style={{ width: '100%', padding: '11px 14px', border: '1.5px solid #e0eaee', borderRadius: 10, fontSize: 14, fontFamily: 'inherit', color: '#0f1c20', background: '#f8fafc', boxSizing: 'border-box', transition: 'all 0.15s' }} />
              </div>
              <button type="submit" disabled={loading} className="cta-btn" style={{ width: '100%', padding: '14px', background: loading ? '#8fa8b0' : '#d4a017', color: 'white', border: 'none', borderRadius: 12, fontSize: 15, fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer', fontFamily: 'inherit' }}>
                {loading ? 'Wird weitergeleitet...' : 'Jetzt sicher bezahlen →'}
              </button>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, marginTop: 12, fontSize: 11, color: '#b0c4cc' }}>🔒 Sichere Zahlung via Stripe · SSL-verschlüsselt</div>
            </form>
            <div style={{ marginTop: 20, paddingTop: 20, borderTop: '1px solid #f0f4f6', display: 'flex', flexDirection: 'column', gap: 8 }}>
              {['✓ Projekt startet binnen 24h', '✓ Fertigstellung in 14 Werktagen', '✓ Strategie-Workshop inklusive', '✓ Nachbetreuung nach Go-Live'].map(t => (
                <div key={t} style={{ fontSize: 12, color: '#4a6470' }}>{t}</div>
              ))}
            </div>
          </div>
          <div style={{ background: 'white', borderRadius: 16, padding: 24, boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: '#8fa8b0', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 12 }}>✅ Im KOMPAGNON Paket enthalten</div>
            {FEATURES.map(item => (
              <div key={item} style={{ display: 'flex', alignItems: 'flex-start', gap: 10, marginBottom: 8 }}>
                <div style={{ width: 18, height: 18, borderRadius: '50%', background: '#eaf5ee', color: '#1a7a3a', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, flexShrink: 0, marginTop: 1, fontWeight: 700 }}>✓</div>
                <span style={{ fontSize: 13, color: '#4a6470', lineHeight: 1.4 }}>{item}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
