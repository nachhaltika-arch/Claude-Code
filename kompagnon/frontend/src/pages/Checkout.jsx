import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useScreenSize } from '../utils/responsive';
import API_BASE_URL from '../config';

const N = '#0F1E3A';
const A = '#D4A017';
const G = '#6a7a9a';

const PACKAGES = {
  starter: { name: 'Starter', price: '1.500', pages: '5 Seiten', features: ['SEO Basic', 'Mobile-optimiert', 'DSGVO-konform'] },
  kompagnon: { name: 'Kompagnon', price: '2.000', pages: '8 Seiten', features: ['SEO Komplett', 'GEO-Optimierung', 'Strategie-Workshop', 'Nachbetreuung'] },
  premium: { name: 'Premium', price: '2.800', pages: '12 Seiten', features: ['SEO + GEO Komplett', 'Shop-Ready', 'Fotoshooting', '3 Monate Betreuung'] },
};

const TRADES = ['Elektriker', 'Klempner', 'Maler', 'Schreiner', 'Dachdecker', 'Heizung', 'Sanitaer', 'Fliesenleger', 'Sonstiges'];

export default function Checkout() {
  const { package: pkgParam } = useParams();
  const nav = useNavigate();
  const { isMobile } = useScreenSize();
  const [step, setStep] = useState(1);
  const [selectedPkg, setSelectedPkg] = useState(pkgParam || 'kompagnon');
  const [form, setForm] = useState({ company_name: '', contact_name: '', phone: '', email: '', website_url: '', city: '', trade: '', notes: '' });
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState('');

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));
  const pkg = PACKAGES[selectedPkg] || PACKAGES.kompagnon;

  const submit = async () => {
    setError('');
    setSubmitting(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/leads/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...form,
          lead_source: 'landing_page',
          notes: `Paket: ${pkg.name} (${pkg.price} Euro)\n${form.notes}`,
        }),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Fehler beim Absenden');
      }
      setDone(true);
    } catch (e) {
      setError(e.message);
    } finally {
      setSubmitting(false);
    }
  };

  const inputStyle = { width: '100%', padding: '12px 14px', border: '1.5px solid #d4d8e8', borderRadius: 8, fontSize: 16, boxSizing: 'border-box', outline: 'none' };

  if (done) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f8f9fc', padding: 20 }}>
        <div style={{ background: '#fff', borderRadius: 16, padding: '48px 36px', maxWidth: 500, width: '100%', textAlign: 'center', boxShadow: '0 4px 24px rgba(0,0,0,0.06)' }}>
          <div style={{ fontSize: 64, marginBottom: 20 }}>✅</div>
          <h2 style={{ fontSize: 24, color: N, fontWeight: 800, marginBottom: 12 }}>Vielen Dank!</h2>
          <p style={{ fontSize: 16, color: G, lineHeight: 1.6, marginBottom: 24 }}>
            Ihre Anfrage ist eingegangen. Wir melden uns innerhalb von 24 Stunden bei Ihnen.
          </p>
          <div style={{ background: '#f0f7ff', borderRadius: 10, padding: 20, marginBottom: 24, textAlign: 'left' }}>
            <div style={{ fontSize: 13, color: G, marginBottom: 4 }}>Gewaehltes Paket:</div>
            <div style={{ fontSize: 18, fontWeight: 800, color: N }}>{pkg.name} — {pkg.price} Euro</div>
          </div>
          <button onClick={() => nav('/')} style={{ background: N, color: '#fff', border: 'none', borderRadius: 8, padding: '12px 32px', fontSize: 16, fontWeight: 700, cursor: 'pointer', minHeight: 48 }}>
            Zurueck zur Startseite
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', background: '#f8f9fc' }}>
      {/* Header */}
      <div style={{ background: N, padding: '16px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ color: '#fff', fontWeight: 900, fontSize: 20, cursor: 'pointer' }} onClick={() => nav('/')}>KOMPAGNON</div>
        <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: 13 }}>Sichere Bestellung</div>
      </div>

      {/* Progress */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: 8, padding: '24px 20px 0' }}>
        {[1, 2, 3].map((s) => (
          <div key={s} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{
              width: 32, height: 32, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontWeight: 700, fontSize: 14, background: step >= s ? N : '#d4d8e8', color: step >= s ? '#fff' : G,
            }}>{s}</div>
            <span style={{ fontSize: 13, color: step >= s ? N : G, fontWeight: step === s ? 700 : 400, display: isMobile && s !== step ? 'none' : 'inline' }}>
              {s === 1 ? 'Paket' : s === 2 ? 'Kontakt' : 'Bestaetigung'}
            </span>
            {s < 3 && !isMobile && <div style={{ width: 40, height: 2, background: step > s ? N : '#d4d8e8' }} />}
          </div>
        ))}
      </div>

      {/* Content */}
      <div style={{ maxWidth: 560, margin: '24px auto', padding: '0 20px' }}>
        <div style={{ background: '#fff', borderRadius: 16, padding: isMobile ? '24px 20px' : '32px', boxShadow: '0 2px 12px rgba(0,0,0,0.04)' }}>
          {/* Step 1 */}
          {step === 1 && (
            <div>
              <h2 style={{ fontSize: 20, fontWeight: 800, color: N, marginBottom: 20 }}>Paket waehlen</h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {Object.entries(PACKAGES).map(([key, p]) => (
                  <label key={key} onClick={() => setSelectedPkg(key)} style={{
                    display: 'flex', alignItems: 'center', gap: 14, padding: '16px 18px', borderRadius: 10, cursor: 'pointer',
                    border: selectedPkg === key ? `2px solid ${N}` : '2px solid #eef0f8', background: selectedPkg === key ? '#f0f4ff' : '#fff',
                  }}>
                    <div style={{
                      width: 22, height: 22, borderRadius: '50%', border: `2px solid ${selectedPkg === key ? N : '#d4d8e8'}`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                    }}>
                      {selectedPkg === key && <div style={{ width: 12, height: 12, borderRadius: '50%', background: N }} />}
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 700, fontSize: 16, color: N }}>{p.name} {key === 'kompagnon' && <span style={{ background: A, color: N, fontSize: 10, padding: '2px 8px', borderRadius: 10, fontWeight: 800, marginLeft: 8 }}>EMPFOHLEN</span>}</div>
                      <div style={{ fontSize: 13, color: G }}>{p.pages} · {p.features[0]}</div>
                    </div>
                    <div style={{ fontWeight: 800, fontSize: 18, color: N }}>{p.price} Euro</div>
                  </label>
                ))}
              </div>
              <button onClick={() => setStep(2)} style={{ width: '100%', marginTop: 20, padding: '14px', background: N, color: '#fff', border: 'none', borderRadius: 8, fontSize: 16, fontWeight: 700, cursor: 'pointer', minHeight: 48 }}>
                Weiter
              </button>
            </div>
          )}

          {/* Step 2 */}
          {step === 2 && (
            <div>
              <h2 style={{ fontSize: 20, fontWeight: 800, color: N, marginBottom: 20 }}>Ihre Kontaktdaten</h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                <div>
                  <label style={{ fontSize: 13, fontWeight: 600, color: '#4a5a74', display: 'block', marginBottom: 4 }}>Firmenname *</label>
                  <input style={inputStyle} value={form.company_name} onChange={set('company_name')} required placeholder="z.B. Mueller Sanitaer GmbH" />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: 12 }}>
                  <div>
                    <label style={{ fontSize: 13, fontWeight: 600, color: '#4a5a74', display: 'block', marginBottom: 4 }}>Ansprechpartner *</label>
                    <input style={inputStyle} value={form.contact_name} onChange={set('contact_name')} required placeholder="Vor- und Nachname" />
                  </div>
                  <div>
                    <label style={{ fontSize: 13, fontWeight: 600, color: '#4a5a74', display: 'block', marginBottom: 4 }}>Telefon *</label>
                    <input style={inputStyle} type="tel" value={form.phone} onChange={set('phone')} required placeholder="+49 ..." />
                  </div>
                </div>
                <div>
                  <label style={{ fontSize: 13, fontWeight: 600, color: '#4a5a74', display: 'block', marginBottom: 4 }}>E-Mail *</label>
                  <input style={inputStyle} type="email" value={form.email} onChange={set('email')} required placeholder="info@firma.de" />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: 12 }}>
                  <div>
                    <label style={{ fontSize: 13, fontWeight: 600, color: '#4a5a74', display: 'block', marginBottom: 4 }}>Website (falls vorhanden)</label>
                    <input style={inputStyle} value={form.website_url} onChange={set('website_url')} placeholder="www.firma.de" />
                  </div>
                  <div>
                    <label style={{ fontSize: 13, fontWeight: 600, color: '#4a5a74', display: 'block', marginBottom: 4 }}>Stadt</label>
                    <input style={inputStyle} value={form.city} onChange={set('city')} placeholder="z.B. Koblenz" />
                  </div>
                </div>
                <div>
                  <label style={{ fontSize: 13, fontWeight: 600, color: '#4a5a74', display: 'block', marginBottom: 4 }}>Gewerk</label>
                  <select style={inputStyle} value={form.trade} onChange={set('trade')}>
                    <option value="">Bitte waehlen...</option>
                    {TRADES.map((t) => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: 13, fontWeight: 600, color: '#4a5a74', display: 'block', marginBottom: 4 }}>Nachricht (optional)</label>
                  <textarea style={{ ...inputStyle, resize: 'vertical', minHeight: 60 }} value={form.notes} onChange={set('notes')} placeholder="Besondere Wuensche..." rows={2} />
                </div>
              </div>
              <div style={{ display: 'flex', gap: 10, marginTop: 20 }}>
                <button onClick={() => setStep(1)} style={{ padding: '14px 24px', background: '#f0f2f8', color: N, border: 'none', borderRadius: 8, fontSize: 15, fontWeight: 700, cursor: 'pointer', minHeight: 48 }}>
                  Zurueck
                </button>
                <button onClick={() => { if (!form.company_name || !form.contact_name || !form.phone || !form.email) { setError('Bitte Pflichtfelder ausfuellen'); return; } setError(''); setStep(3); }}
                  style={{ flex: 1, padding: '14px', background: N, color: '#fff', border: 'none', borderRadius: 8, fontSize: 16, fontWeight: 700, cursor: 'pointer', minHeight: 48 }}>
                  Weiter
                </button>
              </div>
              {error && <div style={{ color: '#c03030', fontSize: 13, marginTop: 10 }}>{error}</div>}
            </div>
          )}

          {/* Step 3 */}
          {step === 3 && (
            <div>
              <h2 style={{ fontSize: 20, fontWeight: 800, color: N, marginBottom: 20 }}>Zusammenfassung</h2>
              <div style={{ background: '#f8f9fc', borderRadius: 10, padding: 20, marginBottom: 20 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
                  <span style={{ fontWeight: 700, color: N }}>{pkg.name}-Paket</span>
                  <span style={{ fontWeight: 800, fontSize: 20, color: N }}>{pkg.price} Euro</span>
                </div>
                <div style={{ fontSize: 13, color: G }}>
                  {pkg.pages} · {pkg.features.join(' · ')}
                </div>
                <div style={{ borderTop: '1px solid #eef0f8', marginTop: 12, paddingTop: 12, fontSize: 13, color: G }}>
                  zzgl. 19% MwSt. · Zahlbar per Vorkasse
                </div>
              </div>
              <div style={{ background: '#f8f9fc', borderRadius: 10, padding: 20, marginBottom: 20, fontSize: 14 }}>
                <div style={{ fontWeight: 700, color: N, marginBottom: 8 }}>Kontaktdaten</div>
                {[
                  ['Firma', form.company_name],
                  ['Kontakt', form.contact_name],
                  ['Telefon', form.phone],
                  ['E-Mail', form.email],
                  form.city && ['Stadt', form.city],
                  form.trade && ['Gewerk', form.trade],
                ].filter(Boolean).map(([label, val], i) => (
                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span style={{ color: G }}>{label}</span>
                    <span style={{ color: N, fontWeight: 600 }}>{val}</span>
                  </div>
                ))}
              </div>
              <div style={{ display: 'flex', gap: 10 }}>
                <button onClick={() => setStep(2)} style={{ padding: '14px 24px', background: '#f0f2f8', color: N, border: 'none', borderRadius: 8, fontSize: 15, fontWeight: 700, cursor: 'pointer', minHeight: 48 }}>
                  Zurueck
                </button>
                <button onClick={submit} disabled={submitting} style={{
                  flex: 1, padding: '14px', background: A, color: N, border: 'none', borderRadius: 8, fontSize: 16, fontWeight: 700, cursor: 'pointer', minHeight: 48,
                  opacity: submitting ? 0.6 : 1,
                }}>
                  {submitting ? 'Wird gesendet...' : 'Verbindlich anfragen'}
                </button>
              </div>
              {error && <div style={{ color: '#c03030', fontSize: 13, marginTop: 10 }}>{error}</div>}
              <p style={{ fontSize: 11, color: G, marginTop: 16, textAlign: 'center' }}>
                Mit dem Absenden akzeptieren Sie unsere AGB und Datenschutzerklaerung.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
