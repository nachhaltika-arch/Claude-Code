import React, { useState, useEffect } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { useScreenSize } from '../utils/responsive';
import API_BASE_URL from '../config';


const A = '#D4A017';

export default function Checkout() {
  const nav = useNavigate();
  const { package: pkgParam } = useParams();
  const [searchParams] = useSearchParams();
  const { isMobile } = useScreenSize();
  const cancelled = searchParams.get('cancelled');

  const [packages, setPackages] = useState([]);
  const [step, setStep] = useState(1);
  const [selected, setSelected] = useState(pkgParam || searchParams.get('package') || 'kompagnon');
  const [form, setForm] = useState({ name: '', company: '', email: '', phone: '', message: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/products/public`)
      .then(r => r.json())
      .then(data => {
        const list = data.map(p => ({
          id:        p.slug,
          name:      p.name,
          price:     parseFloat(p.price_brutto).toLocaleString('de-DE', { minimumFractionDigits: 0, maximumFractionDigits: 0 }),
          desc:      p.short_desc || '',
          highlight: p.highlighted,
          features:  Array.isArray(p.features) ? p.features : [],
        }));
        setPackages(list);
        // Auto-select highlighted package if none pre-selected
        if (!pkgParam && !searchParams.get('package') && list.length > 0) {
          const highlighted = list.find(p => p.highlight);
          setSelected((highlighted || list[0]).id);
        }
      })
      .catch(() => {});
  }, []); // eslint-disable-line

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));
  const pkg = packages.find((p) => p.id === selected) || packages[0] || { name: '', price: '', features: [] };

  const handleCheckout = async () => {
    if (!form.email || !form.name || !form.company) { setError('Bitte alle Pflichtfelder ausfuellen'); return; }
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE_URL}/api/payments/create-checkout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ package: selected, email: form.email, name: form.name, company: form.company }),
      });
      const data = await res.json();
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
      } else {
        setError(data.detail || 'Fehler beim Erstellen der Zahlung');
      }
    } catch { setError('Verbindungsfehler. Bitte erneut versuchen.'); }
    finally { setLoading(false); }
  };

  const inp = { width: '100%', padding: '11px 14px', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', fontSize: 15, boxSizing: 'border-box', outline: 'none', fontFamily: 'var(--font-sans)' };
  const lbl = { display: 'block', fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.07em' };

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-app)', fontFamily: 'var(--font-sans)' }}>
      {/* Header */}
      <div style={{ background: 'var(--brand-primary)', padding: '16px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div onClick={() => nav('/')} style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer' }}>
          <div style={{ width: 36, height: 36, borderRadius: '50%', background: A, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ color: 'var(--text-primary)', fontWeight: 900, fontSize: 13 }}>HS</span>
          </div>
          <span style={{ color: '#fff', fontWeight: 800, fontSize: 18 }}>KOMPAGNON</span>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {['Paket', 'Kontakt', 'Zahlung'].map((s, i) => (
            <React.Fragment key={s}>
              {i > 0 && <div style={{ width: 20, height: 1, background: 'rgba(255,255,255,0.3)' }} />}
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <div style={{
                  width: 24, height: 24, borderRadius: '50%', fontSize: 11, fontWeight: 700, color: '#fff',
                  background: step > i + 1 ? '#27ae60' : step === i + 1 ? A : 'rgba(255,255,255,0.2)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  {step > i + 1 ? '✓' : i + 1}
                </div>
                {!isMobile && <span style={{ color: step === i + 1 ? '#fff' : 'rgba(255,255,255,0.75)', fontSize: 13, fontWeight: step === i + 1 ? 600 : 400 }}>{s}</span>}
              </div>
            </React.Fragment>
          ))}
        </div>
      </div>

      {cancelled && (
        <div style={{ background: '#fff8e1', color: '#c07820', padding: '12px 24px', textAlign: 'center', fontSize: 14, borderBottom: '1px solid #fde68a' }}>
          Zahlung abgebrochen — Sie koennen es erneut versuchen.
        </div>
      )}

      <div style={{ maxWidth: 900, margin: '0 auto', padding: '32px 20px' }}>
        {/* Step 1 — Package */}
        {step === 1 && (
          <div>
            <h2 style={{ fontSize: 24, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 8, textAlign: 'center' }}>Waehlen Sie Ihr Paket</h2>
            <p style={{ textAlign: 'center', color: 'var(--text-secondary)', marginBottom: 32, fontSize: 15 }}>Alle Preise zzgl. 19% MwSt. · Einmaliger Festpreis</p>
            <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr 1fr', gap: 16, marginBottom: 32 }}>
              {packages.map((p) => (
                <div key={p.id} onClick={() => setSelected(p.id)} style={{
                  background: 'var(--bg-surface)', borderRadius: 'var(--radius-xl)', padding: 24, cursor: 'pointer', position: 'relative',
                  border: `2px solid ${selected === p.id ? 'var(--brand-primary)' : p.highlight ? A + '60' : '#e8eaf2'}`,
                  transform: p.highlight ? 'scale(1.02)' : 'none',
                  boxShadow: selected === p.id ? '0 4px 20px rgba(15,30,58,0.15)' : '0 2px 8px rgba(0,0,0,0.06)',
                  transition: 'all 0.2s',
                }}>
                  {p.highlight && <div style={{ position: 'absolute', top: -12, left: '50%', transform: 'translateX(-50%)', background: A, color: 'var(--text-primary)', fontSize: 11, fontWeight: 800, padding: '4px 14px', borderRadius: 20, whiteSpace: 'nowrap' }}>EMPFOHLEN</div>}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
                    <div>
                      <div style={{ fontSize: 18, fontWeight: 800, color: 'var(--text-primary)' }}>{p.name}</div>
                      <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 2 }}>{p.desc}</div>
                    </div>
                    <div style={{ width: 24, height: 24, borderRadius: '50%', border: `2px solid ${selected === p.id ? 'var(--brand-primary)' : '#d0d8e8'}`, background: selected === p.id ? 'var(--brand-primary)' : 'transparent', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                      {selected === p.id && <span style={{ color: '#fff', fontSize: 12 }}>✓</span>}
                    </div>
                  </div>
                  <div style={{ fontSize: 28, fontWeight: 900, color: 'var(--text-primary)', marginBottom: 16 }}>{p.price} Euro</div>
                  {p.features.map((f) => (
                    <div key={f} style={{ display: 'flex', gap: 8, fontSize: 13, color: '#4a5a74', marginBottom: 6 }}>
                      <span style={{ color: '#27ae60', fontWeight: 700, flexShrink: 0 }}>✓</span> {f}
                    </div>
                  ))}
                </div>
              ))}
            </div>
            <div style={{ textAlign: 'center' }}>
              <button onClick={() => setStep(2)} style={{ background: 'var(--brand-primary)', color: '#fff', border: 'none', borderRadius: 10, padding: '14px 40px', fontSize: 16, fontWeight: 700, cursor: 'pointer', minHeight: 48 }}>
                Weiter mit {pkg.name}
              </button>
              <p style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 12 }}>Sichere Zahlung via Stripe · DSGVO-konform</p>
            </div>
          </div>
        )}

        {/* Step 2 — Contact + Stripe redirect */}
        {step === 2 && (
          <div style={{ maxWidth: 560, margin: '0 auto' }}>
            <h2 style={{ fontSize: 24, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 8 }}>Ihre Kontaktdaten</h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: 28, fontSize: 14 }}>Wir brauchen diese Angaben um Ihr Projekt zu starten.</p>

            {error && <div style={{ background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)', borderRadius: 'var(--radius-md)', padding: '12px 16px', fontSize: 14, marginBottom: 20 }}>{error}</div>}

            <div style={{ background: 'var(--bg-surface)', borderRadius: 'var(--radius-xl)', padding: 28, boxShadow: '0 2px 16px rgba(0,0,0,0.06)' }}>
              <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: 16, marginBottom: 16 }}>
                <div><label style={lbl}>Ihr Name *</label><input style={inp} value={form.name} onChange={set('name')} placeholder="Max Mustermann" /></div>
                <div><label style={lbl}>Firma *</label><input style={inp} value={form.company} onChange={set('company')} placeholder="Mustermann GmbH" /></div>
              </div>
              <div style={{ marginBottom: 16 }}><label style={lbl}>E-Mail *</label><input style={inp} type="email" value={form.email} onChange={set('email')} placeholder="ihre@email.de" /></div>
              <div style={{ marginBottom: 16 }}><label style={lbl}>Telefon</label><input style={inp} type="tel" value={form.phone} onChange={set('phone')} placeholder="089 123 456" /></div>
              <div style={{ marginBottom: 24 }}>
                <label style={lbl}>Nachricht (optional)</label>
                <textarea style={{ ...inp, resize: 'vertical', minHeight: 60 }} value={form.message} onChange={set('message')} placeholder="Besondere Wuensche..." rows={3} />
              </div>

              {/* Package summary */}
              <div style={{ background: '#f8f9fc', borderRadius: 10, padding: '14px 18px', marginBottom: 20, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div><div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>{pkg.name}-Paket</div><div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Einmaliger Festpreis zzgl. MwSt.</div></div>
                <div style={{ fontSize: 22, fontWeight: 900, color: 'var(--text-primary)' }}>{pkg.price} Euro</div>
              </div>

              <div style={{ display: 'flex', gap: 12 }}>
                <button onClick={() => setStep(1)} style={{ background: 'var(--bg-app)', color: 'var(--text-primary)', border: 'none', borderRadius: 'var(--radius-md)', padding: '12px 20px', fontSize: 14, fontWeight: 600, cursor: 'pointer', minHeight: 48 }}>Zurueck</button>
                <button onClick={handleCheckout} disabled={loading} style={{
                  flex: 1, background: loading ? '#64748b' : 'var(--brand-primary)', color: '#fff', border: 'none', borderRadius: 'var(--radius-md)',
                  padding: '12px', fontSize: 15, fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer', minHeight: 48,
                }}>
                  {loading ? 'Wird vorbereitet...' : 'Weiter zur Zahlung'}
                </button>
              </div>
              <p style={{ fontSize: 11, color: 'var(--text-tertiary)', textAlign: 'center', marginTop: 12 }}>Sie werden zu Stripe weitergeleitet. Kreditkarte und SEPA-Lastschrift moeglich.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
