import { useState } from 'react';
import Logo from '../components/Logo';
import API_BASE_URL from '../config';

// KOMPAGNON Brand Tokens
const PRIMARY   = '#004F59';
const MID       = '#008EAA';
const ACCENT    = '#FAE600';
const LIGHT_BG  = '#F0F4F5';
const WHITE     = '#ffffff';

export default function PackageImpuls() {
  const [form, setForm] = useState({
    name:    '',
    company: '',
    email:   '',
    phone:   '',
    message: '',
  });
  const [loading,  setLoading]  = useState(false);
  const [success,  setSuccess]  = useState(false);
  const [error,    setError]    = useState('');

  const set = (field) => (e) =>
    setForm(prev => ({ ...prev, [field]: e.target.value }));

  const handleSubmit = async () => {
    if (!form.name || !form.company || !form.email) {
      setError('Bitte Name, Firma und E-Mail ausfüllen.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE_URL}/api/impuls/anfrage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Fehler beim Senden');
      setSuccess(true);
    } catch (err) {
      setError(err.message || 'Verbindungsfehler. Bitte erneut versuchen.');
    }
    setLoading(false);
  };

  return (
    <div style={{ minHeight: '100vh', background: LIGHT_BG, fontFamily: 'Noto Sans, sans-serif' }}>

      {/* Header */}
      <div style={{ background: PRIMARY, padding: '16px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Logo variant="white" />
        <span style={{ color: 'rgba(255,255,255,0.6)', fontSize: 12, fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase' }}>
          IMPULS by KOMPAGNON
        </span>
      </div>

      {/* Hero */}
      <div style={{ background: `linear-gradient(135deg, ${PRIMARY} 0%, ${MID} 100%)`, color: WHITE, padding: '64px 24px 56px', textAlign: 'center' }}>
        <div style={{ display: 'inline-block', background: ACCENT, color: PRIMARY, fontSize: 11, fontWeight: 900, letterSpacing: '0.12em', textTransform: 'uppercase', padding: '5px 14px', borderRadius: 20, marginBottom: 20 }}>
          ISB Betriebsberatungsprogramm 158 · Rheinland-Pfalz
        </div>
        <h1 style={{ fontSize: 'clamp(32px, 5vw, 56px)', fontWeight: 900, margin: '0 0 16px', lineHeight: 1.1, letterSpacing: '-0.02em' }}>
          50 % vom Land.<br />Den Rest in Raten.
        </h1>
        <p style={{ fontSize: 18, color: 'rgba(255,255,255,0.8)', maxWidth: 560, margin: '0 auto 32px' }}>
          Professionelle Unternehmensberatung — gefördert, finanziert, sofort wirksam.
          Für KMU in Rheinland-Pfalz.
        </p>
        <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap', fontSize: 13, color: 'rgba(255,255,255,0.65)' }}>
          {['KMU-Förderung', 'De-minimis-Beihilfe', 'MMV Leasing', 'Akkreditierter ISB-Berater'].map(tag => (
            <span key={tag} style={{ background: 'rgba(255,255,255,0.12)', padding: '4px 12px', borderRadius: 20 }}>{tag}</span>
          ))}
        </div>
      </div>

      {/* Hauptinhalt */}
      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '48px 24px', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 48 }}>

        {/* Links: Infos */}
        <div>

          {/* Wie funktioniert es */}
          <h2 style={{ fontSize: 22, fontWeight: 900, color: PRIMARY, marginBottom: 24 }}>Wie funktioniert das Modell?</h2>
          {[
            { nr: '1', title: 'Förderantrag stellen', text: 'Gemeinsam mit KOMPAGNON stellen Sie den Antrag bei der ISB — bevor die Beratung beginnt. Erst nach Bewilligung geht es los.' },
            { nr: '2', title: 'Beratung & Zahlung', text: 'KOMPAGNON erbringt die Beratungsleistung. Sie zahlen das volle Honorar und erhalten alle Ergebnisse strukturiert aufbereitet.' },
            { nr: '3', title: '50 % zurück + Leasing', text: 'Die ISB erstattet Ihnen 50 % direkt auf Ihr Konto. Den Eigenanteil finanzieren Sie bequem in 36 Monatsraten über MMV Leasing.' },
          ].map(step => (
            <div key={step.nr} style={{ display: 'flex', gap: 16, marginBottom: 24 }}>
              <div style={{ width: 40, height: 40, borderRadius: '50%', background: MID, color: WHITE, fontWeight: 900, fontSize: 16, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                {step.nr}
              </div>
              <div>
                <div style={{ fontWeight: 700, color: PRIMARY, marginBottom: 4 }}>{step.title}</div>
                <div style={{ color: '#555', fontSize: 14, lineHeight: 1.6 }}>{step.text}</div>
              </div>
            </div>
          ))}

          {/* Rechenbeispiel */}
          <div style={{ background: WHITE, border: `1px solid ${MID}30`, borderRadius: 12, padding: 24, marginTop: 32 }}>
            <div style={{ fontWeight: 900, color: PRIMARY, marginBottom: 16, fontSize: 15 }}>Beispielrechnung: 10.000 € Honorar</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
              {[
                { label: 'Gesamthonorar', value: '10.000 €', sub: 'Sie zahlen zunächst', color: '#334155' },
                { label: 'ISB erstattet', value: '5.000 €', sub: 'Direkt auf Ihr Konto', color: MID },
                { label: 'Ihre Rate', value: '~145 €', sub: 'Pro Monat / 36 Monate', color: '#9a7c00' },
              ].map(c => (
                <div key={c.label} style={{ textAlign: 'center', padding: '12px 8px', background: LIGHT_BG, borderRadius: 8 }}>
                  <div style={{ fontSize: 11, color: '#888', marginBottom: 4 }}>{c.label}</div>
                  <div style={{ fontSize: 22, fontWeight: 900, color: c.color }}>{c.value}</div>
                  <div style={{ fontSize: 11, color: '#aaa', marginTop: 4 }}>{c.sub}</div>
                </div>
              ))}
            </div>
            <div style={{ marginTop: 16, padding: '10px 14px', background: `${MID}15`, borderRadius: 8, fontSize: 13, color: PRIMARY, fontWeight: 600 }}>
              → Effektive Belastung: nur ~145 €/Monat für vollwertige Unternehmensberatung
            </div>
          </div>

          {/* Features */}
          <h2 style={{ fontSize: 18, fontWeight: 900, color: PRIMARY, margin: '32px 0 16px' }}>Was ist enthalten?</h2>
          {[
            'ISB-158 Förderung: 50 % vom Land Rheinland-Pfalz',
            'Bis zu 20 Tagewerke à 8 Stunden Beratung',
            'Strategie, Marketing & Vertriebsoptimierung',
            'Digitalisierung & KI-Einsatz im Unternehmen',
            'Kommunikations- & Designberatung (max. 3 TW)',
            'Persönliches Ergebnis-Portal (passwortgeschützt)',
            'Leasingfinanzierung: ~145 €/Monat über MMV',
            'Wir übernehmen Antragstellung & Dokumentation',
          ].map(f => (
            <div key={f} style={{ display: 'flex', gap: 10, marginBottom: 10, fontSize: 14, color: '#444' }}>
              <span style={{ color: MID, fontWeight: 900, flexShrink: 0 }}>✓</span>
              {f}
            </div>
          ))}

          {/* Wer ist förderfähig */}
          <div style={{ background: `${PRIMARY}08`, border: `1px solid ${PRIMARY}20`, borderRadius: 10, padding: 20, marginTop: 24 }}>
            <div style={{ fontWeight: 700, color: PRIMARY, marginBottom: 10 }}>Wer ist förderfähig?</div>
            {[
              'Betriebsstätte in Rheinland-Pfalz',
              'Weniger als 250 Mitarbeiter & unter 50 Mio. € Umsatz',
              'Kein laufendes Insolvenzverfahren',
              'Antrag VOR Beratungsbeginn bei der ISB',
            ].map(c => (
              <div key={c} style={{ display: 'flex', gap: 8, marginBottom: 6, fontSize: 13, color: '#555' }}>
                <span style={{ color: '#1D9E75', fontWeight: 900 }}>✓</span>{c}
              </div>
            ))}
          </div>
        </div>

        {/* Rechts: Formular */}
        <div>
          <div style={{ background: WHITE, borderRadius: 16, border: `1px solid ${MID}30`, boxShadow: '0 4px 24px rgba(0,79,89,0.08)', padding: 32, position: 'sticky', top: 24 }}>

            {success ? (
              <div style={{ textAlign: 'center', padding: '32px 16px' }}>
                <div style={{ fontSize: 48, marginBottom: 16 }}>✅</div>
                <h3 style={{ color: PRIMARY, fontWeight: 900, marginBottom: 12 }}>Anfrage erhalten!</h3>
                <p style={{ color: '#555', fontSize: 15, lineHeight: 1.6 }}>
                  Vielen Dank. Wir melden uns innerhalb von <strong>24 Stunden</strong> bei Ihnen für das kostenlose Erstgespräch.
                </p>
                <div style={{ marginTop: 24, padding: '12px 16px', background: LIGHT_BG, borderRadius: 8, fontSize: 13, color: '#666' }}>
                  📞 +49 (0) 261 884470<br />
                  ✉ info@kompagnon.eu
                </div>
              </div>
            ) : (
              <>
                <div style={{ textAlign: 'center', marginBottom: 24 }}>
                  <div style={{ display: 'inline-block', background: ACCENT, color: PRIMARY, fontSize: 11, fontWeight: 900, letterSpacing: '0.1em', textTransform: 'uppercase', padding: '4px 12px', borderRadius: 20, marginBottom: 12 }}>
                    15 Minuten · Kostenlos & unverbindlich
                  </div>
                  <h3 style={{ color: PRIMARY, fontWeight: 900, fontSize: 20, margin: 0 }}>
                    Jetzt Förderung sichern
                  </h3>
                  <p style={{ color: '#888', fontSize: 13, marginTop: 8 }}>
                    Wir prüfen Ihre Förderfähigkeit und berechnen Ihre individuelle Rate.
                  </p>
                </div>

                {/* Formularfelder */}
                {[
                  { field: 'name',    label: 'Name *',           placeholder: 'Max Mustermann',        type: 'text' },
                  { field: 'company', label: 'Unternehmen *',    placeholder: 'Mustermann GmbH',       type: 'text' },
                  { field: 'email',   label: 'E-Mail *',         placeholder: 'max@mustermann.de',     type: 'email' },
                  { field: 'phone',   label: 'Telefon',          placeholder: '+49 261 ...',           type: 'tel' },
                ].map(f => (
                  <div key={f.field} style={{ marginBottom: 14 }}>
                    <label style={{ display: 'block', fontSize: 11, fontWeight: 700, color: '#888', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 5 }}>
                      {f.label}
                    </label>
                    <input
                      type={f.type}
                      placeholder={f.placeholder}
                      value={form[f.field]}
                      onChange={set(f.field)}
                      style={{ width: '100%', padding: '10px 12px', border: '1.5px solid #e2e8f0', borderRadius: 8, fontSize: 14, fontFamily: 'inherit', boxSizing: 'border-box', outline: 'none', color: '#1e293b' }}
                    />
                  </div>
                ))}

                <div style={{ marginBottom: 20 }}>
                  <label style={{ display: 'block', fontSize: 11, fontWeight: 700, color: '#888', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 5 }}>
                    Ihre Situation (optional)
                  </label>
                  <textarea
                    placeholder="Was möchten Sie erreichen? Welche Herausforderungen haben Sie?"
                    value={form.message}
                    onChange={set('message')}
                    rows={3}
                    style={{ width: '100%', padding: '10px 12px', border: '1.5px solid #e2e8f0', borderRadius: 8, fontSize: 14, fontFamily: 'inherit', resize: 'vertical', boxSizing: 'border-box', outline: 'none', color: '#1e293b' }}
                  />
                </div>

                {error && (
                  <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 8, padding: '10px 14px', fontSize: 13, color: '#dc2626', marginBottom: 14 }}>
                    {error}
                  </div>
                )}

                <button
                  onClick={handleSubmit}
                  disabled={loading}
                  style={{ width: '100%', padding: '14px', background: loading ? '#94a3b8' : PRIMARY, color: WHITE, border: 'none', borderRadius: 10, fontSize: 15, fontWeight: 900, cursor: loading ? 'not-allowed' : 'pointer', letterSpacing: '0.02em', fontFamily: 'inherit' }}
                >
                  {loading ? '⏳ Wird gesendet...' : '→ Kostenloses Erstgespräch anfragen'}
                </button>

                <p style={{ fontSize: 11, color: '#aaa', textAlign: 'center', marginTop: 12 }}>
                  Kein Risiko · Kein Aufwand · 100 % kostenlos
                </p>

                {/* Vertrauenselemente */}
                <div style={{ borderTop: '1px solid #f1f5f9', marginTop: 20, paddingTop: 16 }}>
                  {[
                    '✅ Akkreditierter ISB-Berater',
                    '✅ Komplette Förderabwicklung durch KOMPAGNON',
                    '✅ B2B-Expertise seit 2005',
                  ].map(t => (
                    <div key={t} style={{ fontSize: 12, color: '#64748b', marginBottom: 6 }}>{t}</div>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div style={{ background: PRIMARY, color: 'rgba(255,255,255,0.5)', padding: '20px 24px', textAlign: 'center', fontSize: 12 }}>
        KOMPAGNON communications BP GmbH · Koblenz · Akkreditierter Berater der ISB Rheinland-Pfalz
        <br />
        <a href="/impressum" style={{ color: 'rgba(255,255,255,0.4)', textDecoration: 'none', margin: '0 8px' }}>Impressum</a>
        <a href="/datenschutz" style={{ color: 'rgba(255,255,255,0.4)', textDecoration: 'none', margin: '0 8px' }}>Datenschutz</a>
      </div>
    </div>
  );
}
