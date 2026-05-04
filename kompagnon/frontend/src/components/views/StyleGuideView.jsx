/**
 * StyleGuideView — 2×2 Grid mit Style-Tokens (Farben/Typo/Buttons/Spacing).
 * Kontrolliert (controlled) — der Container hält den State, bekommt
 * onChange + onApprove und persistiert (Schritt G).
 *
 * Props:
 *   styleGuide        — { colors: {...}, typography: {...}, buttons: {...}, spacing: {...} }
 *   onChange(next)    — beim Verändern eines Tokens
 *   onApprove()       — "Freigabe an Kunden senden" Button (Brevo-Mail im Container)
 *   approved          — true → Lock entfernt, View 4 freigeschaltet
 */
import { useMemo } from 'react';

const KC_DARK = '#004F59';
const KC_MID = '#008EAA';
const KC_YELLOW = '#FAE600';

const FONT_OPTIONS = [
  { value: 'Noto Sans', label: 'Noto Sans (Default)' },
  { value: 'Inter',     label: 'Inter' },
  { value: 'Roboto',    label: 'Roboto' },
  { value: 'Open Sans', label: 'Open Sans' },
  { value: 'Montserrat',label: 'Montserrat' },
  { value: 'Lato',      label: 'Lato' },
  { value: 'Poppins',   label: 'Poppins' },
];

const RADIUS_OPTIONS = [
  { value: '0px',  label: 'Eckig (0px)' },
  { value: '6px',  label: 'Sanft (6px)' },
  { value: '12px', label: 'Weich (12px)' },
  { value: '999px',label: 'Rund (Pill)' },
];

const DEFAULT_STYLE_GUIDE = {
  colors: {
    primary:    KC_MID,
    secondary:  KC_DARK,
    accent:     KC_YELLOW,
    background: '#FFFFFF',
    text:       '#1a2332',
  },
  typography: {
    font_family:   'Noto Sans',
    headline_size: 32,
    body_size:     14,
  },
  buttons: {
    radius: '8px',
    style:  'solid',
  },
  spacing: {
    radius:  '8px',
    section: 64,
  },
};

export default function StyleGuideView({
  styleGuide,
  onChange,
  onApprove,
  approved,
}) {
  const sg = useMemo(() => ({ ...DEFAULT_STYLE_GUIDE, ...(styleGuide || {}) }), [styleGuide]);

  const set = (path, value) => {
    const [k1, k2] = path.split('.');
    const next = {
      ...sg,
      [k1]: { ...(sg[k1] || {}), [k2]: value },
    };
    onChange?.(next);
  };

  return (
    <div style={{ padding: 24, fontFamily: 'var(--font-sans, "Noto Sans", sans-serif)' }}>
      {/* Topbar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: 24,
          gap: 12,
          flexWrap: 'wrap',
        }}
      >
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 900, color: KC_DARK, margin: 0, textTransform: 'uppercase', letterSpacing: '-0.02em' }}>
            Style Guide
          </h1>
          <p style={{ fontSize: 13, color: '#64748b', marginTop: 4 }}>
            Farben, Typografie, Buttons — KI-Vorschlag aus dem Brand-Crawl. Anpassen, dann an Kunden zur Freigabe senden.
          </p>
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          {approved && (
            <span style={{ fontSize: 11, fontWeight: 700, color: '#1D9E75', background: '#D1FAE5', padding: '4px 10px', borderRadius: 12, textTransform: 'uppercase' }}>
              ✓ Vom Kunden freigegeben
            </span>
          )}
          <button
            type="button"
            onClick={onApprove}
            disabled={approved}
            style={{
              background: approved ? '#cbd5e1' : KC_YELLOW,
              color: '#000',
              border: 'none',
              borderRadius: 8,
              padding: '10px 18px',
              fontSize: 13,
              fontWeight: 800,
              cursor: approved ? 'default' : 'pointer',
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
            }}
          >
            {approved ? 'Bereits freigegeben' : 'Freigabe an Kunden senden'}
          </button>
        </div>
      </div>

      {/* 2×2 Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
          gap: 20,
        }}
      >
        {/* Karte 1 — Primärfarben */}
        <Card title="Primärfarben" badge="Aus Brand-Crawl extrahiert">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <ColorField label="Primär"     value={sg.colors.primary}    onChange={(v) => set('colors.primary', v)} />
            <ColorField label="Sekundär"   value={sg.colors.secondary}  onChange={(v) => set('colors.secondary', v)} />
            <ColorField label="Akzent"     value={sg.colors.accent}     onChange={(v) => set('colors.accent', v)} />
            <ColorField label="Hintergrund" value={sg.colors.background} onChange={(v) => set('colors.background', v)} />
          </div>
        </Card>

        {/* Karte 2 — Typografie */}
        <Card title="Typografie">
          <div style={{ marginBottom: 14 }}>
            <Label>Schriftart</Label>
            <select
              value={sg.typography.font_family}
              onChange={(e) => set('typography.font_family', e.target.value)}
              style={selectStyle}
            >
              {FONT_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, paddingTop: 12, borderTop: '1px solid #f1f5f9' }}>
            <div style={{ fontSize: 18, fontWeight: 700, fontFamily: sg.typography.font_family, color: KC_DARK }}>
              Headline-Sample (18px / 700)
            </div>
            <div style={{ fontSize: 13, fontFamily: sg.typography.font_family, color: '#475569' }}>
              Subline-Sample (13px) — die Lorem-ipsum-Variante.
            </div>
            <div style={{ fontSize: 11, fontFamily: sg.typography.font_family, color: '#94a3b8' }}>
              Body-Sample (11px) — kleiner Hilfetext, gedimmt.
            </div>
          </div>
        </Card>

        {/* Karte 3 — Buttons */}
        <Card title="Buttons">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div>
              <Label>Primär</Label>
              <button type="button" style={{
                background: sg.colors.primary, color: '#fff', border: 'none',
                borderRadius: sg.buttons.radius, padding: '10px 18px', fontSize: 13,
                fontWeight: 700, cursor: 'pointer', fontFamily: sg.typography.font_family,
              }}>
                Termin vereinbaren
              </button>
            </div>
            <div>
              <Label>Sekundär (Outline)</Label>
              <button type="button" style={{
                background: 'transparent', color: sg.colors.primary,
                border: `1.5px solid ${sg.colors.primary}`,
                borderRadius: sg.buttons.radius, padding: '10px 18px', fontSize: 13,
                fontWeight: 700, cursor: 'pointer', fontFamily: sg.typography.font_family,
              }}>
                Mehr erfahren
              </button>
            </div>
            <div>
              <Label>CTA (Akzent)</Label>
              <button type="button" style={{
                background: sg.colors.accent, color: '#000', border: 'none',
                borderRadius: sg.buttons.radius, padding: '10px 18px', fontSize: 13,
                fontWeight: 800, cursor: 'pointer', textTransform: 'uppercase',
                letterSpacing: '0.04em', fontFamily: sg.typography.font_family,
              }}>
                Kostenfrei anfragen
              </button>
            </div>
          </div>
        </Card>

        {/* Karte 4 — Border-Radius & Abstände */}
        <Card title="Border-Radius & Abstände">
          <div style={{ marginBottom: 14 }}>
            <Label>Element-Rundung</Label>
            <select
              value={sg.spacing.radius}
              onChange={(e) => {
                set('spacing.radius', e.target.value);
                set('buttons.radius', e.target.value);
              }}
              style={selectStyle}
            >
              {RADIUS_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
          <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end' }}>
            {[0, 6, 999].map((r, i) => (
              <div key={i} style={{ flex: 1, textAlign: 'center' }}>
                <div style={{
                  height: 60, background: KC_MID, borderRadius: r,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: '#fff', fontSize: 11, fontWeight: 700,
                }}>
                  {r === 999 ? 'Pill' : `${r}px`}
                </div>
              </div>
            ))}
          </div>
          <div style={{ marginTop: 14, fontSize: 11, color: '#64748b', lineHeight: 1.5 }}>
            <strong>KI-Empfehlung:</strong> Für Handwerk werden mittlere Rundungen (6–8 px) als seriös wahrgenommen — zu eckig wirkt kühl, zu rund verspielt.
          </div>
        </Card>
      </div>
    </div>
  );
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function Card({ title, badge, children }) {
  return (
    <section style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: 12, padding: 18 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
        <h2 style={{ fontSize: 14, fontWeight: 800, color: KC_DARK, margin: 0, textTransform: 'uppercase', letterSpacing: '-0.01em' }}>
          {title}
        </h2>
        {badge && (
          <span style={{ fontSize: 9, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 700 }}>
            {badge}
          </span>
        )}
      </div>
      {children}
    </section>
  );
}

function Label({ children }) {
  return (
    <div style={{ fontSize: 10, fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>
      {children}
    </div>
  );
}

function ColorField({ label, value, onChange }) {
  return (
    <div>
      <Label>{label}</Label>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <input
          type="color"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          style={{
            width: 40, height: 40, border: '1px solid #cbd5e1', borderRadius: 6,
            cursor: 'pointer', background: 'transparent', padding: 0, flexShrink: 0,
          }}
          aria-label={`${label} Farbe wählen`}
        />
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          style={{
            flex: 1, padding: '6px 8px', border: '1px solid #e2e8f0', borderRadius: 4,
            fontSize: 11, fontFamily: 'ui-monospace, monospace', color: '#334155',
            outline: 'none',
          }}
        />
      </div>
    </div>
  );
}

const selectStyle = {
  width: '100%',
  padding: '7px 10px',
  border: '1px solid #cbd5e1',
  borderRadius: 6,
  fontSize: 12,
  background: '#fff',
  color: '#334155',
  outline: 'none',
};
