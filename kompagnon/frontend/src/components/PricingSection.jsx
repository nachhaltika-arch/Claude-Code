import { useNavigate } from 'react-router-dom';

const PACKAGES = [
  {
    id: 'starter',
    badge: 'Einstieg',
    badgeColor: '#008eaa',
    badgeBg: 'rgba(0,142,170,0.12)',
    name: 'Starter',
    tagline: 'Schnell. Sauber. Professionell.',
    price: '1.500',
    delivery: '7–10 Werktage',
    accentColor: '#008eaa',
    ctaBg: '#008eaa',
    ctaLabel: 'Starter wählen',
    features: [
      'Kompakte WordPress-Webseite',
      'Individuelle Texte (4 Seiten)',
      'Mobiloptimierung',
      'SEO-Basis',
      'Impressum & Datenschutz',
      'Go-live & Einweisung',
    ],
    missing: [
      'Strategie-Workshop',
      'GEO / KI-Optimierung',
      'Google Business',
    ],
  },
  {
    id: 'kompagnon',
    badge: '⭐ Meistgewählt',
    badgeColor: '#b8960a',
    badgeBg: 'rgba(212,160,23,0.15)',
    name: 'KOMPAGNON',
    tagline: 'Individuell. Vertriebsstark. Zukunftssicher.',
    price: '2.000',
    delivery: '14 Werktage',
    accentColor: '#d4a017',
    ctaBg: '#d4a017',
    ctaLabel: 'KOMPAGNON wählen',
    recommended: true,
    features: [
      'Individuelle WordPress-Webseite',
      'Individuelle Texterstellung',
      'SEO-Volloptimierung',
      'GEO / KI-Optimierung',
      'Wettbewerbs- & Sichtbarkeitsanalyse',
      'Strategie-Workshop',
      'Google Business Optimierung',
      'Rechtssicherheit',
      'Nachbetreuung nach Go-live',
    ],
  },
  {
    id: 'premium',
    badge: '💎 Premium',
    badgeColor: '#7c3aed',
    badgeBg: 'rgba(124,58,237,0.12)',
    name: 'Premium',
    tagline: 'Sichtbar. Führend. Ausbaufähig.',
    price: '2.500',
    delivery: '14–21 Werktage',
    accentColor: '#7c3aed',
    ctaBg: '#7c3aed',
    ctaLabel: 'Premium wählen',
    features: [
      'Alles aus KOMPAGNON',
      'Erweiterte Seitenstruktur',
      'FAQ-, Partner- oder Karriere-Seite',
      'Vertiefte GEO-Umsetzung',
      'Schema-Markup & strukturierte Daten',
      'Stärkerer regionaler Bezug',
      'Zweite Korrekturschleife',
      'Erweiterte Nachbetreuung',
      'Optionaler BFSG-Baustein',
    ],
  },
];

const COMPARE_ROWS = [
  { label: 'Lieferzeit', values: ['7–10 Tage', '14 Tage', '14–21 Tage'] },
  { label: 'WordPress-Webseite', values: ['✓', '✓', '✓'] },
  { label: 'Individuelle Texte', values: ['4 Seiten', '✓ voll', '✓ erweitert'] },
  { label: 'SEO-Optimierung', values: ['Basis', '✓ voll', '✓ voll'] },
  { label: 'GEO / KI-Optimierung', values: ['–', '✓', '✓ vertieft'] },
  { label: 'Strategie-Workshop', values: ['–', '✓', '✓'] },
  { label: 'Google Business', values: ['–', '✓', '✓'] },
  { label: 'Wettbewerbsanalyse', values: ['–', '✓', '✓'] },
  { label: 'Zusatzseiten (FAQ, Standorte)', values: ['–', '–', '✓'] },
  { label: 'Korrekturschleifen', values: ['1', '1', '2'] },
  { label: 'Barrierefreiheit (BFSG)', values: ['–', '–', 'optional'] },
  { label: 'Nachbetreuung', values: ['–', '✓', '✓ erweitert'] },
];

export default function PricingSection() {
  const navigate = useNavigate();

  return (
    <section id="pakete" style={{
      background: '#f4f6f8',
      padding: '80px 20px',
      fontFamily: 'var(--font-sans, system-ui)',
    }}>
      <style>{`
        @keyframes fadeUpCard {
          from { opacity:0; transform:translateY(20px); }
          to   { opacity:1; transform:translateY(0); }
        }
        .pkg-card { animation: fadeUpCard 0.5s ease both; transition: box-shadow 0.2s, transform 0.2s !important; }
        .pkg-card:hover { transform: translateY(-4px) !important; box-shadow: 0 16px 48px rgba(15,30,58,0.14) !important; }
        .pkg-cta { transition: all 0.2s ease !important; }
        .pkg-cta:hover { filter: brightness(1.08); transform: translateY(-1px); }
        .compare-row { transition: background 0.1s !important; }
        .compare-row:hover { background: #f0fafa !important; }
      `}</style>

      {/* Header */}
      <div style={{ textAlign: 'center', maxWidth: 600, margin: '0 auto 56px' }}>
        <div style={{
          display: 'inline-block',
          background: 'rgba(0,142,170,0.1)',
          border: '1px solid rgba(0,142,170,0.25)',
          color: '#006880', borderRadius: 20,
          padding: '4px 16px', fontSize: 11,
          fontWeight: 700, letterSpacing: '0.1em',
          textTransform: 'uppercase', marginBottom: 16,
        }}>
          Transparente Preise
        </div>
        <h2 style={{
          fontSize: 'clamp(26px, 4vw, 40px)',
          fontWeight: 700, color: '#0f1e3a',
          margin: '0 0 14px', letterSpacing: '-0.02em', lineHeight: 1.2,
        }}>
          Das richtige Paket für Ihren Betrieb
        </h2>
        <p style={{ fontSize: 15, color: '#4a6470', lineHeight: 1.65, margin: 0 }}>
          Alle Pakete sind Festpreise — keine versteckten Kosten,
          keine laufenden Gebühren. Einmalig bezahlen, dauerhaft profitieren.
        </p>
      </div>

      {/* Paket-Karten */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: 20, maxWidth: 1020,
        margin: '0 auto 48px', alignItems: 'flex-start',
      }}>
        {PACKAGES.map((pkg, idx) => (
          <div key={pkg.id} className="pkg-card" style={{
            animationDelay: `${idx * 0.1}s`,
            background: 'white', borderRadius: 20,
            border: `2px solid ${pkg.recommended ? pkg.accentColor : '#e8eef2'}`,
            overflow: 'hidden',
            boxShadow: pkg.recommended
              ? '0 8px 32px rgba(212,160,23,0.15)'
              : '0 2px 12px rgba(0,0,0,0.06)',
            position: 'relative',
          }}>
            {pkg.recommended && (
              <div style={{
                background: '#d4a017', color: 'white',
                textAlign: 'center', padding: '6px 16px',
                fontSize: 11, fontWeight: 700,
                letterSpacing: '0.08em', textTransform: 'uppercase',
              }}>
                ⭐ Meistgewählt — Beste Wahl
              </div>
            )}
            <div style={{ padding: '28px 24px' }}>
              <div style={{
                display: 'inline-block',
                background: pkg.badgeBg, color: pkg.badgeColor,
                borderRadius: 20, padding: '3px 12px',
                fontSize: 11, fontWeight: 700, marginBottom: 12,
              }}>
                {pkg.badge}
              </div>
              <h3 style={{
                fontSize: 22, fontWeight: 700, color: '#0f1e3a',
                margin: '0 0 6px', letterSpacing: '-0.02em',
              }}>
                {pkg.name}
              </h3>
              <p style={{ fontSize: 12, color: '#8fa8b0', margin: '0 0 20px', lineHeight: 1.4 }}>
                {pkg.tagline}
              </p>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, marginBottom: 4 }}>
                <span style={{ fontSize: 42, fontWeight: 700, color: pkg.accentColor, letterSpacing: '-0.03em', lineHeight: 1 }}>
                  {pkg.price} €
                </span>
                <span style={{ fontSize: 13, color: '#8fa8b0' }}>netto</span>
              </div>
              <div style={{ fontSize: 12, color: '#8fa8b0', marginBottom: 22 }}>
                📅 {pkg.delivery} · zzgl. MwSt.
              </div>

              <div style={{ marginBottom: 20 }}>
                {pkg.features.map((f, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 8, marginBottom: 7 }}>
                    <div style={{
                      width: 16, height: 16, borderRadius: '50%',
                      background: `${pkg.accentColor}18`, color: pkg.accentColor,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: 9, fontWeight: 700, flexShrink: 0, marginTop: 2,
                    }}>✓</div>
                    <span style={{ fontSize: 12, color: '#4a6470', lineHeight: 1.4 }}>{f}</span>
                  </div>
                ))}
                {pkg.missing && (
                  <div style={{ marginTop: 10, paddingTop: 10, borderTop: '1px solid #f0f4f6' }}>
                    {pkg.missing.map((f, i) => (
                      <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 8, marginBottom: 5 }}>
                        <div style={{
                          width: 16, height: 16, borderRadius: '50%',
                          background: '#f4f6f8', color: '#c0ccd4',
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          fontSize: 9, flexShrink: 0, marginTop: 2,
                        }}>–</div>
                        <span style={{ fontSize: 11, color: '#b0c4cc', lineHeight: 1.4 }}>{f}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <button className="pkg-cta" onClick={() => navigate(`/paket/${pkg.id}`)} style={{
                width: '100%', padding: '13px 20px',
                background: pkg.ctaBg, color: 'white', border: 'none',
                borderRadius: 12, fontSize: 14, fontWeight: 700,
                cursor: 'pointer', fontFamily: 'inherit',
                letterSpacing: '-0.01em', marginBottom: 10,
              }}>
                {pkg.ctaLabel} →
              </button>
              <button onClick={() => navigate(`/paket/${pkg.id}`)} style={{
                width: '100%', padding: '8px', background: 'transparent',
                color: '#8fa8b0', border: 'none', borderRadius: 8,
                fontSize: 12, cursor: 'pointer', fontFamily: 'inherit',
              }}>
                Alle Details ansehen →
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Vergleichstabelle */}
      <div style={{
        maxWidth: 900, margin: '0 auto 48px',
        background: 'white', borderRadius: 16,
        overflow: 'hidden',
        boxShadow: '0 2px 16px rgba(0,0,0,0.07)',
        border: '1px solid #e8eef2',
      }}>
        <div style={{
          background: '#0f1e3a', padding: '18px 28px',
          display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr',
          gap: 8, alignItems: 'center',
        }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'rgba(255,255,255,0.6)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            Leistung
          </div>
          {PACKAGES.map(pkg => (
            <div key={pkg.id} style={{ fontSize: 13, fontWeight: 700, color: pkg.recommended ? '#f0c040' : 'white', textAlign: 'center' }}>
              {pkg.name}
            </div>
          ))}
        </div>
        <div style={{
          background: '#f4f6f8', padding: '12px 28px',
          display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr',
          gap: 8, borderBottom: '2px solid #e8eef2',
        }}>
          <div style={{ fontSize: 12, color: '#8fa8b0', fontWeight: 600 }}>Festpreis netto</div>
          {PACKAGES.map(pkg => (
            <div key={pkg.id} style={{ textAlign: 'center', fontSize: 14, fontWeight: 700, color: pkg.accentColor }}>
              {pkg.price} €
            </div>
          ))}
        </div>
        {COMPARE_ROWS.map((row, i) => (
          <div key={i} className="compare-row" style={{
            padding: '10px 28px',
            display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr',
            gap: 8, alignItems: 'center',
            borderBottom: i < COMPARE_ROWS.length - 1 ? '1px solid #f0f4f6' : 'none',
            background: 'white',
          }}>
            <div style={{ fontSize: 12, color: '#4a6470', fontWeight: 500 }}>{row.label}</div>
            {row.values.map((val, j) => (
              <div key={j} style={{
                textAlign: 'center', fontSize: 12,
                color: val === '–' ? '#c0ccd4' : val === '✓' ? '#1a7a3a' : PACKAGES[j].accentColor,
                fontWeight: val === '✓' ? 700 : 400,
              }}>
                {val}
              </div>
            ))}
          </div>
        ))}
      </div>

      {/* Hinweise */}
      <div style={{
        maxWidth: 900, margin: '0 auto 40px',
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: 12,
      }}>
        {[
          { icon: '💳', title: 'Einmalige Zahlung', text: 'Kein Abo, keine monatlichen Kosten. Einmal bezahlen — Website gehört Ihnen.' },
          { icon: '📦', title: 'Nicht enthalten', text: 'Hosting, Domain, Fotografie und WooCommerce sind separat. Pflegepaket ab 99 €/Monat optional.' },
          { icon: '🔒', title: 'Sicher bezahlen', text: 'Zahlung über Stripe — Kreditkarte, SEPA-Überweisung oder Lastschrift möglich.' },
        ].map(hint => (
          <div key={hint.icon} style={{
            background: 'white', borderRadius: 12,
            padding: '14px 16px', border: '1px solid #e8eef2',
            display: 'flex', gap: 12, alignItems: 'flex-start',
          }}>
            <span style={{ fontSize: 20 }}>{hint.icon}</span>
            <div>
              <div style={{ fontSize: 12, fontWeight: 700, color: '#0f1e3a', marginBottom: 3 }}>{hint.title}</div>
              <div style={{ fontSize: 11, color: '#8fa8b0', lineHeight: 1.5 }}>{hint.text}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Abschluss CTA */}
      <div style={{ textAlign: 'center', maxWidth: 480, margin: '0 auto' }}>
        <p style={{ fontSize: 13, color: '#8fa8b0', marginBottom: 16, lineHeight: 1.6 }}>
          Unsicher welches Paket passt? Wir beraten Sie gerne — kostenlos und unverbindlich.
        </p>
        <a href="mailto:hallo@kompagnon.eu" style={{
          display: 'inline-flex', alignItems: 'center', gap: 8,
          padding: '10px 24px', background: 'transparent',
          color: '#008eaa', border: '1.5px solid #008eaa',
          borderRadius: 10, fontSize: 13, fontWeight: 600,
          textDecoration: 'none', fontFamily: 'inherit',
        }}>
          ✉️ Kostenlos beraten lassen
        </a>
      </div>
    </section>
  );
}
