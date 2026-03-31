import { useState } from 'react';

const PACKAGES = [
  {
    id: 'starter', name: 'Starter', price: 1500, priceLabel: '1.500', delivery: '7–10 Werktage',
    accentColor: '#008eaa', badgeBg: 'rgba(0,142,170,0.1)', badgeColor: '#006880',
    features: ['Kompakte WordPress-Webseite', 'Individuelle Texte (4 Seiten)', 'Mobiloptimierung', 'SEO-Basis', 'Impressum & Datenschutz', 'Go-live & Einweisung'],
  },
  {
    id: 'kompagnon', name: 'KOMPAGNON', price: 2000, priceLabel: '2.000', delivery: '14 Werktage',
    accentColor: '#d4a017', badgeBg: 'rgba(212,160,23,0.12)', badgeColor: '#b8960a', recommended: true,
    features: ['Individuelle WordPress-Webseite', 'Individuelle Texterstellung', 'SEO-Volloptimierung', 'GEO / KI-Optimierung', 'Wettbewerbs- & Sichtbarkeitsanalyse', 'Persönlicher Strategie-Workshop', 'Google Business Optimierung', 'Rechtssicherheit', 'Nachbetreuung nach Go-live'],
  },
  {
    id: 'premium', name: 'Premium', price: 2500, priceLabel: '2.500', delivery: '14–21 Werktage',
    accentColor: '#7c3aed', badgeBg: 'rgba(124,58,237,0.1)', badgeColor: '#6d28d9',
    features: ['Alles aus KOMPAGNON', 'Erweiterte Seitenstruktur', 'FAQ-, Partner- oder Karriere-Seite', 'Vertiefte GEO-Umsetzung', 'Stärkerer regionaler Bezug', 'Zweite Korrekturschleife', 'Erweiterte Nachbetreuung', 'Optionaler BFSG-Baustein'],
  },
];

const COMPARE = [
  { label: 'Preis netto', values: ['1.500 €', '2.000 €', '2.500 €'] },
  { label: 'Lieferzeit', values: ['7–10 Tage', '14 Tage', '14–21 Tage'] },
  { label: 'SEO-Optimierung', values: ['Basis', '✓ voll', '✓ voll'] },
  { label: 'GEO / KI', values: ['–', '✓', '✓'] },
  { label: 'Strategie-Workshop', values: ['–', '✓', '✓'] },
  { label: 'Google Business', values: ['–', '✓', '✓'] },
  { label: 'Zusatzseiten', values: ['–', '–', '✓'] },
  { label: 'Nachbetreuung', values: ['–', '✓', '✓ ext.'] },
];

export default function OfferTab({ lead, currentScore, currentLevel, isMobile }) {
  const [copied, setCopied] = useState(false);
  const [selectedPkg, setSelectedPkg] = useState('kompagnon');

  const recommended = currentScore === null ? 'kompagnon' : currentScore >= 70 ? 'premium' : currentScore >= 40 ? 'kompagnon' : 'starter';
  const scoreColor = (s) => s >= 70 ? 'var(--status-success-text)' : s >= 50 ? 'var(--status-warning-text)' : 'var(--status-danger-text)';

  const pkg = PACKAGES.find(p => p.id === selectedPkg) || PACKAGES[1];

  const copyOfferLink = () => {
    navigator.clipboard.writeText(`${window.location.origin}/paket/${selectedPkg}`);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const sendByEmail = () => {
    const company = lead.display_name || lead.company_name || 'Ihr Betrieb';
    const link = `${window.location.origin}/paket/${selectedPkg}`;
    const subject = encodeURIComponent('Ihr persönliches Angebot — KOMPAGNON');
    const body = encodeURIComponent(
      `Guten Tag,\n\nvielen Dank für Ihr Interesse an KOMPAGNON.\n\nBasierend auf unserer Analyse Ihrer Website empfehlen wir Ihnen das ${pkg.name}-Paket:\n\n✓ ${pkg.priceLabel} € netto (einmalig)\n✓ Fertigstellung in ${pkg.delivery}\n✓ Festpreis — keine versteckten Kosten\n\nIhr persönlicher Bestelllink:\n${link}\n\nBei Fragen stehen wir Ihnen gerne zur Verfügung.\n\nMit freundlichen Grüßen\nIhr KOMPAGNON Team\nhttps://kompagnon.eu`
    );
    window.location.href = `mailto:${lead.email || ''}?subject=${subject}&body=${body}`;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

      {/* Score Context */}
      {currentScore !== null && (
        <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: '14px 18px', display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap' }}>
          <div style={{ width: 48, height: 48, borderRadius: 'var(--radius-md)', background: `${scoreColor(currentScore)}18`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <span style={{ fontSize: 18, fontWeight: 700, color: scoreColor(currentScore) }}>{currentScore}</span>
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>
              Aktueller Score: <strong style={{ color: scoreColor(currentScore) }}>{currentScore}/100</strong> — {currentLevel}
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 2 }}>Empfehlung basierend auf Audit-Ergebnis</div>
          </div>
          <div style={{ background: `${pkg.accentColor}15`, border: `1px solid ${pkg.accentColor}40`, borderRadius: 'var(--radius-md)', padding: '6px 12px', fontSize: 12, fontWeight: 600, color: pkg.accentColor, flexShrink: 0 }}>
            → {pkg.name} empfohlen
          </div>
        </div>
      )}

      {/* Package Selection */}
      <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, 1fr)', gap: 12 }}>
        {PACKAGES.map(p => {
          const isSelected = selectedPkg === p.id;
          const isRec = recommended === p.id;
          return (
            <div key={p.id} onClick={() => setSelectedPkg(p.id)} style={{
              background: isSelected ? `${p.accentColor}08` : 'var(--bg-surface)',
              border: `2px solid ${isSelected ? p.accentColor : 'var(--border-light)'}`,
              borderRadius: 'var(--radius-lg)', padding: 16, cursor: 'pointer', transition: 'all 0.15s', position: 'relative', overflow: 'hidden',
            }}>
              {isRec && (
                <div style={{ position: 'absolute', top: 8, right: -20, background: p.accentColor, color: 'white', fontSize: 9, fontWeight: 700, padding: '3px 28px', transform: 'rotate(35deg)', letterSpacing: '0.06em', textTransform: 'uppercase' }}>Top</div>
              )}
              <div style={{ width: 18, height: 18, borderRadius: '50%', border: `2px solid ${isSelected ? p.accentColor : 'var(--border-medium)'}`, background: isSelected ? p.accentColor : 'transparent', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 10, transition: 'all 0.15s' }}>
                {isSelected && <div style={{ width: 6, height: 6, borderRadius: '50%', background: 'white' }} />}
              </div>
              <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>{p.name}</div>
              <div style={{ fontSize: 20, fontWeight: 700, color: isSelected ? p.accentColor : 'var(--text-primary)', marginBottom: 4, transition: 'color 0.15s' }}>{p.priceLabel} €</div>
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{p.delivery}</div>
            </div>
          );
        })}
      </div>

      {/* Offer Preview */}
      <div style={{ background: 'var(--bg-surface)', border: `2px solid ${pkg.accentColor}40`, borderRadius: 'var(--radius-xl)', overflow: 'hidden', boxShadow: `0 4px 24px ${pkg.accentColor}15` }}>
        <div style={{ background: 'linear-gradient(135deg, #0f1e3a 0%, #1a3a5c 100%)', padding: isMobile ? '24px 20px' : '28px 32px', color: 'white' }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
            <div>
              <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 6 }}>Persönliches Angebot für</div>
              <div style={{ fontSize: isMobile ? 18 : 22, fontWeight: 700, marginBottom: 4 }}>{lead.display_name || lead.company_name}</div>
              {lead.city && <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.55)' }}>📍 {lead.city}{lead.trade && ` · ${lead.trade}`}</div>}
            </div>
            <div style={{ background: `${pkg.accentColor}30`, border: `1px solid ${pkg.accentColor}60`, borderRadius: 'var(--radius-lg)', padding: '14px 20px', textAlign: 'center', backdropFilter: 'blur(8px)' }}>
              <div style={{ fontSize: isMobile ? 28 : 36, fontWeight: 700, color: pkg.accentColor === '#d4a017' ? '#f0c040' : 'white', lineHeight: 1 }}>{pkg.priceLabel}</div>
              <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', marginTop: 3 }}>netto · einmalig</div>
            </div>
          </div>
        </div>
        <div style={{ padding: isMobile ? 20 : '24px 32px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
            <div style={{ background: pkg.badgeBg, color: pkg.badgeColor, borderRadius: 20, padding: '4px 14px', fontSize: 12, fontWeight: 700 }}>{pkg.name}</div>
            <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>📅 Fertigstellung in {pkg.delivery}</div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: '6px 20px', marginBottom: 20 }}>
            {pkg.features.map((f, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                <div style={{ width: 16, height: 16, borderRadius: '50%', background: `${pkg.accentColor}18`, color: pkg.accentColor, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 9, fontWeight: 700, flexShrink: 0, marginTop: 2 }}>✓</div>
                <span style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.4 }}>{f}</span>
              </div>
            ))}
          </div>
          <div style={{ borderTop: '1px solid var(--border-light)', paddingTop: 16, marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
              <div>
                <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginBottom: 2 }}>Festpreis zzgl. MwSt.</div>
                <div style={{ fontSize: 24, fontWeight: 700, color: pkg.accentColor }}>{pkg.priceLabel} € netto</div>
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)', textAlign: 'right', lineHeight: 1.6 }}>Vorkasse vor Projektstart<br />Keine laufenden Kosten<br />Keine versteckten Gebühren</div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <button onClick={sendByEmail} style={{ flex: '1 1 140px', padding: '11px 16px', background: pkg.accentColor, color: 'white', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}>
              ✉️ Per E-Mail senden
            </button>
            <button onClick={copyOfferLink} style={{ flex: '1 1 120px', padding: '11px 16px', background: 'var(--bg-surface)', color: copied ? 'var(--status-success-text)' : 'var(--text-primary)', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, transition: 'all 0.2s' }}>
              {copied ? '✓ Kopiert!' : '📋 Link kopieren'}
            </button>
            <button onClick={() => window.open(`/paket/${pkg.id}`, '_blank')} style={{ flex: '1 1 120px', padding: '11px 16px', background: 'var(--bg-app)', color: 'var(--text-secondary)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}>
              ↗ Buchungsseite
            </button>
          </div>
          <div style={{ marginTop: 14, padding: '10px 14px', background: 'var(--bg-app)', borderRadius: 'var(--radius-md)', fontSize: 11, color: 'var(--text-tertiary)', lineHeight: 1.6 }}>
            💡 Nicht enthalten: Hosting, Domain, Fotografie. Optionales Pflegepaket ab 99 €/Monat verfügbar.
          </div>
        </div>
      </div>

      {/* Comparison Table */}
      <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
        <div style={{ background: '#0f1e3a', padding: '12px 16px', display: 'grid', gridTemplateColumns: '1fr 60px 60px 60px', gap: 8, fontSize: 11 }}>
          <div style={{ color: 'rgba(255,255,255,0.5)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Leistung</div>
          {PACKAGES.map(p => (
            <div key={p.id} style={{ textAlign: 'center', fontWeight: 700, color: selectedPkg === p.id ? (p.accentColor === '#d4a017' ? '#f0c040' : p.accentColor) : 'rgba(255,255,255,0.5)', fontSize: 10 }}>{p.name}</div>
          ))}
        </div>
        {COMPARE.map((row, i) => (
          <div key={row.label} style={{ display: 'grid', gridTemplateColumns: '1fr 60px 60px 60px', gap: 8, padding: '8px 16px', borderBottom: i < COMPARE.length - 1 ? '1px solid var(--border-light)' : 'none', background: i % 2 === 0 ? 'var(--bg-surface)' : 'var(--bg-app)', alignItems: 'center' }}>
            <div style={{ fontSize: 11, color: 'var(--text-secondary)', fontWeight: 500 }}>{row.label}</div>
            {row.values.map((val, j) => {
              const p = PACKAGES[j];
              const isSel = selectedPkg === p.id;
              return (
                <div key={j} style={{ textAlign: 'center', fontSize: 11, fontWeight: isSel ? 600 : 400, color: val === '–' ? 'var(--text-tertiary)' : isSel ? p.accentColor : val === '✓' ? 'var(--status-success-text)' : 'var(--text-secondary)' }}>{val}</div>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}
