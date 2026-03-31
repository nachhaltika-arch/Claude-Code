import React, { useState } from 'react';

const CHECKLIST = [
  {
    area: 'Compliance', icon: '⚖️', color: 'var(--status-danger-text)', bg: '#fee2e2',
    items: [
      { id: 'impressum', label: 'Impressum', desc: 'Name, Adresse, Telefon, E-Mail — max. 2 Klicks erreichbar', law: 'TMG §5', critical: true, auditField: 'rc_impressum', maxScore: 6 },
      { id: 'datenschutz', label: 'Datenschutzerklaerung', desc: 'Erklaert welche Daten gesammelt werden und warum', law: 'DSGVO', critical: true, auditField: 'rc_datenschutz', maxScore: 6 },
      { id: 'cookie', label: 'Cookie-Banner', desc: 'Aktive Einwilligung bei nicht-technischen Cookies', law: 'TDDDG', critical: true, auditField: 'rc_cookie', maxScore: 6 },
      { id: 'agb', label: 'AGB & Widerrufsbelehrung', desc: 'Nur bei Online-Shops / E-Commerce', law: 'BGB §355', critical: false, auditField: 'rc_ecommerce', maxScore: 3 },
    ],
  },
  {
    area: 'SEO', icon: '🔍', color: '#1d4ed8', bg: '#eff6ff',
    items: [
      { id: 'h1', label: 'H1-Ueberschrift', desc: 'Genau eine H1 pro Seite mit Kernthema und Ort', law: 'Google Ranking', critical: true, auditField: 'se_seo', maxScore: 4 },
      { id: 'meta', label: 'Meta-Title & Meta-Description', desc: 'Titel und Beschreibung fuer Google-Suchergebnisse', law: 'Google Ranking', critical: true, auditField: 'se_seo', maxScore: 4 },
      { id: 'nap', label: 'NAP-Block (Name, Adresse, Tel.)', desc: 'Konsistente Kontaktdaten auf Website, Google Business, Impressum', law: 'Local SEO', critical: true, auditField: 'se_lokal', maxScore: 3 },
      { id: 'alt', label: 'Alt-Texte auf Bildern', desc: 'Textalternativen fuer alle informationstragenden Bilder', law: 'WCAG + SEO', critical: false, auditField: 'bf_screenreader', maxScore: 4 },
      { id: 'links', label: 'Interne Verlinkung', desc: 'Navigation + Footer zu allen wichtigen Unterseiten', law: 'SEO Best Practice', critical: false, auditField: 'se_seo', maxScore: 4 },
    ],
  },
  {
    area: 'UI', icon: '🖥️', color: '#7c3aed', bg: '#f5f3ff',
    items: [
      { id: 'logo', label: 'Logo + Firmenname im Header', desc: 'Nutzer muessen in 3 Sek. wissen wo sie sind', law: 'UX Standard', critical: true, auditField: 'ux_erstindruck', maxScore: 2 },
      { id: 'nav', label: 'Hauptnavigation', desc: 'Max. 5-7 Punkte, mobil als Hamburger-Menue', law: 'UX Standard', critical: true, auditField: 'ux_navigation', maxScore: 2 },
      { id: 'hero', label: 'Hero-Bereich', desc: 'Ueberschrift, Kernbotschaft und CTA-Button above the fold', law: 'Conversion', critical: true, auditField: 'ux_erstindruck', maxScore: 2 },
      { id: 'footer', label: 'Footer', desc: 'Impressum, Datenschutz, Kontakt auf jeder Seite', law: 'TMG + UX', critical: true, auditField: 'rc_impressum', maxScore: 6 },
      { id: 'contact_header', label: 'Kontakt sichtbar im Header', desc: 'Telefonnummer oder Button direkt im Header-Bereich', law: 'UX Standard', critical: true, auditField: 'ux_kontakt', maxScore: 1 },
    ],
  },
  {
    area: 'UX', icon: '🧭', color: '#047857', bg: '#ecfdf5',
    items: [
      { id: 'usp', label: 'Klares Leistungsversprechen', desc: 'Was? Fuer wen? Wo? — ohne Scrollen erkennbar', law: 'Conversion', critical: true, auditField: 'ux_erstindruck', maxScore: 2 },
      { id: 'trust', label: 'Vertrauenssignale', desc: 'Bewertungen, Zertifikate, Referenzen, Mitgliedschaften', law: 'Trust Marketing', critical: false, auditField: 'ux_vertrauen', maxScore: 2 },
      { id: 'cta', label: 'Klarer Call-to-Action', desc: 'Ein primaeres Ziel pro Seite: Anruf, Formular oder Anfrage', law: 'Conversion', critical: true, auditField: 'ux_cta', maxScore: 2 },
      { id: 'contact', label: 'Kontaktformular / Kontaktdaten', desc: 'Tel & E-Mail als klickbare tel: und mailto: Links', law: 'UX Standard', critical: true, auditField: 'ux_kontakt', maxScore: 1 },
      { id: 'mobile', label: 'Mobile Optimierung', desc: 'Responsives Design — ueber 60% der Besucher kommen per Handy', law: 'Google Mobile-First', critical: true, auditField: 'tp_mobile', maxScore: 3 },
      { id: 'speed', label: 'Ladezeit unter 3 Sekunden', desc: 'Schnelle Seite fuer Google und Besucher', law: 'Core Web Vitals', critical: true, auditField: 'tp_lcp', maxScore: 4 },
    ],
  },
];

function getStatus(score, maxScore) {
  if (score == null) return 'unknown';
  const pct = score / maxScore;
  if (pct >= 0.8) return 'ok';
  if (pct >= 0.4) return 'partial';
  return 'missing';
}

const S = {
  ok: { icon: '✓', color: '#059669', bg: '#d1fae5', label: 'Vorhanden' },
  partial: { icon: '~', color: '#d97706', bg: '#fef3c7', label: 'Unvollstaendig' },
  missing: { icon: '✗', color: '#dc2626', bg: '#fee2e2', label: 'Fehlt' },
  unknown: { icon: '?', color: 'var(--text-tertiary)', bg: '#f1f5f9', label: 'Nicht geprueft' },
};

export default function HomepageChecklist({ auditData }) {
  const [openArea, setOpenArea] = useState(null);

  const totalItems = CHECKLIST.reduce((s, a) => s + a.items.length, 0);
  const okItems = CHECKLIST.reduce((s, a) => s + a.items.filter((i) => getStatus(auditData?.[i.auditField], i.maxScore) === 'ok').length, 0);
  const criticalMissing = CHECKLIST.reduce((s, a) => s + a.items.filter((i) => i.critical && getStatus(auditData?.[i.auditField], i.maxScore) === 'missing').length, 0);

  return (
    <div style={{ background: 'var(--bg-surface)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-light)', overflow: 'hidden', marginBottom: 20 }}>
      {/* Header */}
      <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-light)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'var(--bg-app)', flexWrap: 'wrap', gap: 8 }}>
        <div>
          <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>Pflichtinhalte der Homepage</div>
          <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 2 }}>
            {auditData ? `${okItems} von ${totalItems} Punkten erfuellt` : 'Noch kein Audit durchgefuehrt'}
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {auditData && criticalMissing > 0 && (
            <span style={{ background: 'var(--status-danger-bg)', color: '#dc2626', borderRadius: 20, padding: '4px 10px', fontSize: 11, fontWeight: 700 }}>
              {criticalMissing} Pflicht fehlt
            </span>
          )}
          {auditData && (
            <span style={{ background: okItems === totalItems ? '#d1fae5' : '#f1f5f9', color: okItems === totalItems ? '#059669' : '#475569', borderRadius: 20, padding: '4px 10px', fontSize: 11, fontWeight: 700 }}>
              {Math.round((okItems / totalItems) * 100)}% erfuellt
            </span>
          )}
        </div>
      </div>

      {/* Areas */}
      {CHECKLIST.map((area) => {
        const isOpen = openArea === area.area;
        const areaOk = area.items.filter((i) => getStatus(auditData?.[i.auditField], i.maxScore) === 'ok').length;
        return (
          <div key={area.area}>
            <button onClick={() => setOpenArea(isOpen ? null : area.area)} style={{
              width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 20px',
              background: isOpen ? area.bg : '#fff', border: 'none', borderBottom: '1px solid var(--border-light)', cursor: 'pointer', textAlign: 'left', transition: 'background 0.15s',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span style={{ fontSize: 20 }}>{area.icon}</span>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 700, color: area.color }}>{area.area}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{areaOk}/{area.items.length} Punkte erfuellt</div>
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <div style={{ width: 60, height: 4, background: '#e2e8f0', borderRadius: 2, overflow: 'hidden' }}>
                  <div style={{ width: `${(areaOk / area.items.length) * 100}%`, height: '100%', background: area.color, borderRadius: 2, transition: 'width 0.6s ease' }} />
                </div>
                <span style={{ color: 'var(--text-tertiary)', fontSize: 12, transition: 'transform 0.2s', transform: isOpen ? 'rotate(180deg)' : 'rotate(0)' }}>▼</span>
              </div>
            </button>
            {isOpen && (
              <div style={{ borderBottom: '1px solid var(--border-light)' }}>
                {area.items.map((item, idx) => {
                  const score = auditData?.[item.auditField];
                  const status = getStatus(score, item.maxScore);
                  const cfg = S[status];
                  return (
                    <div key={item.id} style={{ display: 'flex', alignItems: 'flex-start', gap: 12, padding: '12px 20px', background: idx % 2 === 0 ? '#fafbfc' : '#fff', borderTop: idx > 0 ? '1px solid #f1f5f9' : 'none' }}>
                      <div style={{ width: 28, height: 28, borderRadius: '50%', background: cfg.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, fontWeight: 900, color: cfg.color, flexShrink: 0, marginTop: 1 }}>{cfg.icon}</div>
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3, flexWrap: 'wrap' }}>
                          <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>{item.label}</span>
                          {item.critical && <span style={{ fontSize: 10, fontWeight: 700, color: '#dc2626', background: 'var(--status-danger-bg)', padding: '1px 6px', borderRadius: 4 }}>PFLICHT</span>}
                          <span style={{ fontSize: 10, color: 'var(--text-tertiary)', background: 'var(--bg-app)', padding: '1px 6px', borderRadius: 4 }}>{item.law}</span>
                        </div>
                        <div style={{ fontSize: 12, color: 'var(--text-tertiary)', lineHeight: 1.4 }}>{item.desc}</div>
                      </div>
                      <div style={{ fontSize: 11, fontWeight: 700, color: cfg.color, background: cfg.bg, padding: '3px 8px', borderRadius: 6, flexShrink: 0, whiteSpace: 'nowrap' }}>{cfg.label}</div>
                    </div>
                  );
                })}
                {!auditData && (
                  <div style={{ padding: '12px 20px', background: '#fffbeb', fontSize: 12, color: '#92400e', display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span>💡</span> Fuehren Sie einen Audit durch um den Status zu ermitteln
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}

      <div style={{ padding: '12px 20px', background: 'var(--bg-app)', fontSize: 11, color: 'var(--text-tertiary)', display: 'flex', alignItems: 'center', gap: 6 }}>
        <span>ℹ️</span> Basierend auf TMG, DSGVO, WCAG 2.1 und Google Core Web Vitals. Stand: 2025.
      </div>
    </div>
  );
}
