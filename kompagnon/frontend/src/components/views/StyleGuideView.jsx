/**
 * StyleGuideView — Phase C Redesign (Relume-Style Concept-Cards).
 *
 * Statt freier Token-Picker (V1): kuratierte Konzept-Karten fuer Farbe,
 * Typografie und UI-Style. User klickt sich durch und sieht rechts eine
 * Live-Preview einer Wireframe-Section mit den gewaehlten Tokens.
 *
 * Schema-Strategie:
 *   - Neue Felder: color_concept_id, light_dark, typography_pairing_id, ui_style_id
 *   - Existierende Felder (colors/typography/buttons/spacing) bleiben — werden
 *     beim Concept-Wechsel automatisch derived. Andere Consumer (DesignView,
 *     Export-Pipeline) lesen weiter colors.primary etc., ohne aenderung.
 *   - User kann advance-mode oeffnen und Tokens manuell ueberschreiben.
 *
 * Props:
 *   styleGuide        — { color_concept_id, light_dark, ..., colors, typography, ... }
 *   onChange(next)    — beim Token-Wechsel
 *   onApprove()       — "Freigabe an Kunden senden" (Brevo-Mail im Container)
 *   approved          — true → Lock entfernt
 */
import { useMemo, useState } from 'react';

const KC_DARK = '#004F59';
const KC_MID = '#008EAA';
const KC_YELLOW = '#FAE600';

// ─────────────────────────────────────────────────────────────────────────────
// Color Concepts — kuratierte Paletten
// ─────────────────────────────────────────────────────────────────────────────
//
// Jedes Konzept liefert Light + Dark Varianten. Light = Standard fuer
// Marketing-Sites; Dark als Variante fuer Tech-/Premium-Seiten.
// Tokens, die ein Wireframe braucht:
//   bg_primary, bg_surface, text_primary, text_muted,
//   border, accent_1, accent_2 (optional), accent_3 (optional)

const COLOR_CONCEPTS = [
  {
    id: 'industrial', label: 'Industrial',
    description: 'Schwarz-Weiss-Grau, ein Akzent. Klar, sachlich, Handwerk-tauglich.',
    light: {
      bg_primary: '#FFFFFF', bg_surface: '#F5F5F5',
      text_primary: '#0A0A0A', text_muted: '#6B7280',
      border: '#E5E5E5',
      accent_1: '#0A0A0A', accent_2: '#FACC15', accent_3: '#6B7280',
    },
    dark: {
      bg_primary: '#0A0A0A', bg_surface: '#171717',
      text_primary: '#FAFAFA', text_muted: '#A3A3A3',
      border: '#262626',
      accent_1: '#FACC15', accent_2: '#FAFAFA', accent_3: '#737373',
    },
  },
  {
    id: 'premium_trust', label: 'Premium Trust',
    description: 'Navy + Gold — fuer hochwertige Beratungs-/Premium-Services.',
    light: {
      bg_primary: '#FFFFFF', bg_surface: '#F8FAFC',
      text_primary: '#0F172A', text_muted: '#475569',
      border: '#E2E8F0',
      accent_1: '#1E3A8A', accent_2: '#D4A017', accent_3: '#3B82F6',
    },
    dark: {
      bg_primary: '#0F172A', bg_surface: '#1E293B',
      text_primary: '#F8FAFC', text_muted: '#94A3B8',
      border: '#334155',
      accent_1: '#D4A017', accent_2: '#60A5FA', accent_3: '#F8FAFC',
    },
  },
  {
    id: 'modern_shk', label: 'Modern SHK',
    description: 'Teal + Amber — Energie-Vibe, perfekt fuer Heizung/Wallbox/Solar.',
    light: {
      bg_primary: '#FFFFFF', bg_surface: '#F0FDFA',
      text_primary: '#042F2E', text_muted: '#5F8584',
      border: '#A7F3D0',
      accent_1: '#0E7490', accent_2: '#F59E0B', accent_3: '#10B981',
    },
    dark: {
      bg_primary: '#042F2E', bg_surface: '#134E4A',
      text_primary: '#ECFDF5', text_muted: '#99F6E4',
      border: '#115E59',
      accent_1: '#22D3EE', accent_2: '#FBBF24', accent_3: '#34D399',
    },
  },
  {
    id: 'friendly_warm', label: 'Friendly Warm',
    description: 'Warmer Braun-Ton + Creme — sympathisch, GaLa-Bau, Maler.',
    light: {
      bg_primary: '#FFFBF5', bg_surface: '#FEF3E2',
      text_primary: '#3F2812', text_muted: '#8B6F47',
      border: '#FDE5C2',
      accent_1: '#A0522D', accent_2: '#65A30D', accent_3: '#D97706',
    },
    dark: {
      bg_primary: '#3F2812', bg_surface: '#5A3A1F',
      text_primary: '#FEF3E2', text_muted: '#D4B895',
      border: '#7A5230',
      accent_1: '#FB923C', accent_2: '#A3E635', accent_3: '#FBBF24',
    },
  },
  {
    id: 'tech_forward', label: 'Tech Forward',
    description: 'Schwarz + Neon-Gruen — Tech, KFZ/E-Auto, IT.',
    light: {
      bg_primary: '#FFFFFF', bg_surface: '#FAFAFA',
      text_primary: '#0A0A0A', text_muted: '#525252',
      border: '#E5E5E5',
      accent_1: '#22C55E', accent_2: '#0A0A0A', accent_3: '#737373',
    },
    dark: {
      bg_primary: '#0A0A0A', bg_surface: '#1A1A1A',
      text_primary: '#FAFAFA', text_muted: '#A3A3A3',
      border: '#262626',
      accent_1: '#22C55E', accent_2: '#84CC16', accent_3: '#F4F4F5',
    },
  },
  {
    id: 'classic_engineering', label: 'Classic Engineering',
    description: 'Dunkelblau + Rot-Akzent — klassisch deutsche Ingenieurskunst.',
    light: {
      bg_primary: '#FFFFFF', bg_surface: '#F1F5F9',
      text_primary: '#1E293B', text_muted: '#64748B',
      border: '#CBD5E1',
      accent_1: '#1E40AF', accent_2: '#DC2626', accent_3: '#475569',
    },
    dark: {
      bg_primary: '#1E293B', bg_surface: '#334155',
      text_primary: '#F1F5F9', text_muted: '#94A3B8',
      border: '#475569',
      accent_1: '#60A5FA', accent_2: '#F87171', accent_3: '#CBD5E1',
    },
  },
  {
    id: 'eco_green', label: 'Eco Green',
    description: 'Tiefes Gruen + Sand — Nachhaltigkeit, Bio, Garten.',
    light: {
      bg_primary: '#FFFFFF', bg_surface: '#F0FDF4',
      text_primary: '#14532D', text_muted: '#4F8B5E',
      border: '#BBF7D0',
      accent_1: '#15803D', accent_2: '#CA8A04', accent_3: '#16A34A',
    },
    dark: {
      bg_primary: '#14532D', bg_surface: '#1F6B3D',
      text_primary: '#F0FDF4', text_muted: '#86EFAC',
      border: '#256B45',
      accent_1: '#86EFAC', accent_2: '#FACC15', accent_3: '#FFFFFF',
    },
  },
  {
    id: 'bold_yellow', label: 'Bold Yellow',
    description: 'Gelb + Schwarz — kontrastreich, KOMPAGNON-typisch.',
    light: {
      bg_primary: '#FFFFFF', bg_surface: '#FEFCE8',
      text_primary: '#0A0A0A', text_muted: '#525252',
      border: '#FDE68A',
      accent_1: '#FAE600', accent_2: '#0A0A0A', accent_3: '#737373',
    },
    dark: {
      bg_primary: '#0A0A0A', bg_surface: '#1A1A1A',
      text_primary: '#FAE600', text_muted: '#A3A3A3',
      border: '#404040',
      accent_1: '#FAE600', accent_2: '#FFFFFF', accent_3: '#737373',
    },
  },
];

// ─────────────────────────────────────────────────────────────────────────────
// Typography Pairings
// ─────────────────────────────────────────────────────────────────────────────

const TYPO_PAIRINGS = [
  {
    id: 'modern_sans', label: 'Modern Sans',
    description: 'Inter durchgehend — neutral, professionell, Tech-tauglich.',
    heading: 'Inter', body: 'Inter',
    heading_weight: 700, body_weight: 400,
  },
  {
    id: 'editorial_serif', label: 'Editorial Serif',
    description: 'Playfair Display Heading + Inter Body — elegant, Premium-Feel.',
    heading: 'Playfair Display', body: 'Inter',
    heading_weight: 700, body_weight: 400,
  },
  {
    id: 'friendly_round', label: 'Friendly Round',
    description: 'Poppins + Lato — sympathisch, Handwerk, Service.',
    heading: 'Poppins', body: 'Lato',
    heading_weight: 700, body_weight: 400,
  },
  {
    id: 'tech_confident', label: 'Tech Confident',
    description: 'Space Grotesk + DM Sans — moderner Tech-Look, KFZ/IT.',
    heading: 'Space Grotesk', body: 'DM Sans',
    heading_weight: 600, body_weight: 400,
  },
  {
    id: 'classic_pro', label: 'Classic Pro',
    description: 'Roboto + Open Sans — bewaehrt, neutral, Industrial.',
    heading: 'Roboto', body: 'Open Sans',
    heading_weight: 700, body_weight: 400,
  },
  {
    id: 'bold_statement', label: 'Bold Statement',
    description: 'Montserrat + Roboto — kraftvoll, Statement-driven.',
    heading: 'Montserrat', body: 'Roboto',
    heading_weight: 800, body_weight: 400,
  },
];

// ─────────────────────────────────────────────────────────────────────────────
// UI-Style Konzepte (Buttons, Karten, Borders)
// ─────────────────────────────────────────────────────────────────────────────

const UI_STYLES = [
  {
    id: 'soft_cards', label: 'Soft Cards',
    description: 'Mittlere Rundung, dezente Schatten — freundlich, modern.',
    button_radius: '8px', card_radius: '12px',
    shadow: '0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04)',
    border_width: '1px',
  },
  {
    id: 'sharp_modern', label: 'Sharp Modern',
    description: 'Eckig, kein Schatten — minimal, Tech, Editorial.',
    button_radius: '0px', card_radius: '0px',
    shadow: 'none',
    border_width: '1px',
  },
  {
    id: 'pill_rounded', label: 'Pill Rounded',
    description: 'Pill-Buttons, runde Karten — verspielt, Service, Wellness.',
    button_radius: '999px', card_radius: '16px',
    shadow: '0 2px 6px rgba(0,0,0,0.08)',
    border_width: '1px',
  },
  {
    id: 'heavy_border', label: 'Heavy Border',
    description: 'Dicke Borders, kein Schatten — Brutalist, Tech, Bold.',
    button_radius: '4px', card_radius: '4px',
    shadow: 'none',
    border_width: '2px',
  },
];

// ─────────────────────────────────────────────────────────────────────────────
// Default Style-Guide & Derivation
// ─────────────────────────────────────────────────────────────────────────────

const DEFAULT_CONCEPT = COLOR_CONCEPTS[0]; // Industrial
const DEFAULT_TYPO    = TYPO_PAIRINGS[0];  // Modern Sans
const DEFAULT_UI      = UI_STYLES[0];      // Soft Cards

function findColorConcept(id) {
  return COLOR_CONCEPTS.find((c) => c.id === id) || DEFAULT_CONCEPT;
}
function findTypoPairing(id) {
  return TYPO_PAIRINGS.find((t) => t.id === id) || DEFAULT_TYPO;
}
function findUIStyle(id) {
  return UI_STYLES.find((u) => u.id === id) || DEFAULT_UI;
}

// Aus Concept-Auswahl die Legacy-Felder ableiten (backwards-compat fuer
// DesignView, Export-Pipeline, etc., die colors.primary etc. erwarten).
function deriveLegacyTokens(concept, lightDark, typoPairing, uiStyle) {
  const palette = lightDark === 'dark' ? concept.dark : concept.light;
  return {
    colors: {
      primary:    palette.accent_1,
      secondary:  palette.text_primary,
      accent:     palette.accent_2,
      background: palette.bg_primary,
      text:       palette.text_primary,
    },
    typography: {
      font_family:   typoPairing.body,
      headline_size: 32,
      body_size:     14,
    },
    buttons: {
      radius: uiStyle.button_radius,
      style:  'solid',
    },
    spacing: {
      radius:  uiStyle.card_radius,
      section: 64,
    },
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Component
// ─────────────────────────────────────────────────────────────────────────────

export default function StyleGuideView({ styleGuide, onChange, onApprove, approved }) {
  // Aktuelle Auswahl aus dem persistierten Style-Guide ableiten — oder Defaults
  const conceptId = styleGuide?.color_concept_id || DEFAULT_CONCEPT.id;
  const lightDark = styleGuide?.light_dark || 'light';
  const typoId    = styleGuide?.typography_pairing_id || DEFAULT_TYPO.id;
  const uiId      = styleGuide?.ui_style_id || DEFAULT_UI.id;

  const concept     = findColorConcept(conceptId);
  const typoPairing = findTypoPairing(typoId);
  const uiStyle     = findUIStyle(uiId);
  const palette     = lightDark === 'dark' ? concept.dark : concept.light;

  const updateSelection = (updates) => {
    const merged = {
      ...(styleGuide || {}),
      color_concept_id:        updates.conceptId       || conceptId,
      light_dark:              updates.lightDark       || lightDark,
      typography_pairing_id:   updates.typoId          || typoId,
      ui_style_id:             updates.uiId            || uiId,
    };
    const newConcept = findColorConcept(merged.color_concept_id);
    const newTypo    = findTypoPairing(merged.typography_pairing_id);
    const newUI      = findUIStyle(merged.ui_style_id);
    const derived    = deriveLegacyTokens(newConcept, merged.light_dark, newTypo, newUI);
    onChange?.({ ...merged, ...derived });
  };

  const shuffle = () => {
    const randConcept = COLOR_CONCEPTS[Math.floor(Math.random() * COLOR_CONCEPTS.length)];
    const randTypo    = TYPO_PAIRINGS[Math.floor(Math.random() * TYPO_PAIRINGS.length)];
    const randUI      = UI_STYLES[Math.floor(Math.random() * UI_STYLES.length)];
    updateSelection({
      conceptId: randConcept.id,
      typoId: randTypo.id,
      uiId: randUI.id,
    });
  };

  const [activeSection, setActiveSection] = useState('color'); // color | typography | ui

  return (
    <div style={{
      display: 'flex', flexDirection: 'column',
      height: '100%', background: '#f8fafc',
      fontFamily: 'var(--font-sans, system-ui)',
    }}>
      {/* Topbar */}
      <div style={{
        flexShrink: 0,
        padding: '14px 24px',
        background: '#fff',
        borderBottom: '1px solid #e2e8f0',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        gap: 16, flexWrap: 'wrap',
      }}>
        <div>
          <h1 style={{
            fontSize: 20, fontWeight: 900, color: KC_DARK, margin: 0,
            textTransform: 'uppercase', letterSpacing: '-0.02em',
          }}>
            Style Guide
          </h1>
          <div style={{ fontSize: 12, color: '#64748b', marginTop: 2 }}>
            Konzept-basierte Stilauswahl — links wählen, rechts Live-Preview.
          </div>
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
          <button type="button" onClick={shuffle}
            style={{
              background: 'transparent', color: '#7c3aed',
              border: '1.5px solid #7c3aed', borderRadius: 8,
              padding: '8px 14px', fontSize: 12, fontWeight: 700,
              cursor: 'pointer', fontFamily: 'inherit',
            }}>
            🎲 Alles würfeln
          </button>
          {approved && (
            <span style={{
              fontSize: 11, fontWeight: 700, color: '#1D9E75', background: '#D1FAE5',
              padding: '4px 10px', borderRadius: 12, textTransform: 'uppercase',
            }}>
              ✓ Vom Kunden freigegeben
            </span>
          )}
          <button type="button" onClick={onApprove} disabled={approved}
            style={{
              background: approved ? '#cbd5e1' : KC_YELLOW,
              color: '#000', border: 'none', borderRadius: 8,
              padding: '10px 18px', fontSize: 13, fontWeight: 800,
              cursor: approved ? 'default' : 'pointer',
              textTransform: 'uppercase', letterSpacing: '0.04em',
              fontFamily: 'inherit',
            }}>
            {approved ? 'Bereits freigegeben' : 'Freigabe an Kunden senden'}
          </button>
        </div>
      </div>

      {/* Body — zwei Spalten: Auswahl links, Preview rechts */}
      <div style={{ flex: 1, display: 'flex', minHeight: 0, overflow: 'hidden' }}>
        {/* Auswahl-Panel */}
        <div style={{
          flex: '0 0 50%', minWidth: 480,
          overflowY: 'auto', padding: 24,
          borderRight: '1px solid #e2e8f0',
        }}>
          {/* Section-Tabs */}
          <div style={{ display: 'flex', gap: 4, marginBottom: 18, borderBottom: '1px solid #e2e8f0' }}>
            {[
              { id: 'color',      label: '🎨 Farbe' },
              { id: 'typography', label: '🔤 Typografie' },
              { id: 'ui',         label: '🧩 UI' },
            ].map((tab) => {
              const isActive = activeSection === tab.id;
              return (
                <button
                  key={tab.id} type="button"
                  onClick={() => setActiveSection(tab.id)}
                  style={{
                    padding: '8px 14px',
                    background: 'transparent', border: 'none',
                    borderBottom: isActive ? `2px solid ${KC_MID}` : '2px solid transparent',
                    color: isActive ? KC_DARK : '#64748b',
                    fontSize: 13, fontWeight: isActive ? 800 : 600,
                    cursor: 'pointer', fontFamily: 'inherit',
                    marginBottom: -1,
                  }}
                >
                  {tab.label}
                </button>
              );
            })}
          </div>

          {activeSection === 'color' && (
            <ColorSection
              conceptId={conceptId}
              lightDark={lightDark}
              onSelect={(id) => updateSelection({ conceptId: id })}
              onToggleLightDark={() => updateSelection({ lightDark: lightDark === 'dark' ? 'light' : 'dark' })}
              onShuffle={() => {
                const r = COLOR_CONCEPTS[Math.floor(Math.random() * COLOR_CONCEPTS.length)];
                updateSelection({ conceptId: r.id });
              }}
            />
          )}
          {activeSection === 'typography' && (
            <TypographySection
              typoId={typoId}
              onSelect={(id) => updateSelection({ typoId: id })}
              onShuffle={() => {
                const r = TYPO_PAIRINGS[Math.floor(Math.random() * TYPO_PAIRINGS.length)];
                updateSelection({ typoId: r.id });
              }}
            />
          )}
          {activeSection === 'ui' && (
            <UIStyleSection
              uiId={uiId}
              palette={palette}
              onSelect={(id) => updateSelection({ uiId: id })}
              onShuffle={() => {
                const r = UI_STYLES[Math.floor(Math.random() * UI_STYLES.length)];
                updateSelection({ uiId: r.id });
              }}
            />
          )}
        </div>

        {/* Live-Preview rechts */}
        <div style={{
          flex: 1, overflowY: 'auto',
          background: '#f1f5f9',
          padding: 24,
        }}>
          <div style={{ fontSize: 10, fontWeight: 700, color: '#64748b',
            textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8 }}>
            Live-Preview · {concept.label} · {lightDark === 'dark' ? 'Dark' : 'Light'} · {typoPairing.label} · {uiStyle.label}
          </div>
          <LivePreview palette={palette} typo={typoPairing} ui={uiStyle} />
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// ColorSection — Concept-Karten mit Light/Dark-Toggle
// ─────────────────────────────────────────────────────────────────────────────

function ColorSection({ conceptId, lightDark, onSelect, onToggleLightDark, onShuffle }) {
  return (
    <div>
      <SectionHeader title="Farb-Konzepte" onShuffle={onShuffle}>
        <ToggleSwitch
          options={[
            { id: 'light', label: '☀️ Light' },
            { id: 'dark',  label: '🌙 Dark' },
          ]}
          value={lightDark}
          onChange={onToggleLightDark}
        />
      </SectionHeader>

      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
        gap: 12,
      }}>
        {COLOR_CONCEPTS.map((c) => {
          const palette = lightDark === 'dark' ? c.dark : c.light;
          const isSelected = c.id === conceptId;
          return (
            <button
              key={c.id} type="button"
              onClick={() => onSelect(c.id)}
              style={{
                textAlign: 'left',
                background: '#fff',
                border: isSelected ? `2px solid ${KC_MID}` : '1px solid #e2e8f0',
                borderRadius: 8,
                padding: 12, cursor: 'pointer',
                boxShadow: isSelected ? `0 4px 12px ${KC_MID}33` : 'none',
                fontFamily: 'inherit',
                transition: 'border-color 0.15s, box-shadow 0.15s',
              }}
            >
              {/* Palette-Streifen */}
              <div style={{
                display: 'flex', height: 36, borderRadius: 4, overflow: 'hidden',
                marginBottom: 8, border: '1px solid #e2e8f0',
              }}>
                <div style={{ flex: 2, background: palette.bg_primary }} />
                <div style={{ flex: 1, background: palette.bg_surface }} />
                <div style={{ flex: 1, background: palette.accent_1 }} />
                <div style={{ flex: 1, background: palette.accent_2 }} />
                <div style={{ flex: 1, background: palette.accent_3 || palette.text_primary }} />
              </div>
              <div style={{
                fontSize: 12, fontWeight: 800, color: KC_DARK,
                marginBottom: 2, display: 'flex', alignItems: 'center', gap: 6,
              }}>
                {isSelected && <span style={{ color: KC_MID }}>✓</span>}
                {c.label}
              </div>
              <div style={{ fontSize: 10, color: '#64748b', lineHeight: 1.4 }}>
                {c.description}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// TypographySection — Font-Pairing-Karten
// ─────────────────────────────────────────────────────────────────────────────

function TypographySection({ typoId, onSelect, onShuffle }) {
  return (
    <div>
      <SectionHeader title="Typografie-Pairings" onShuffle={onShuffle} />
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
        gap: 12,
      }}>
        {TYPO_PAIRINGS.map((t) => {
          const isSelected = t.id === typoId;
          return (
            <button
              key={t.id} type="button"
              onClick={() => onSelect(t.id)}
              style={{
                textAlign: 'left',
                background: '#fff',
                border: isSelected ? `2px solid ${KC_MID}` : '1px solid #e2e8f0',
                borderRadius: 8,
                padding: 14, cursor: 'pointer',
                boxShadow: isSelected ? `0 4px 12px ${KC_MID}33` : 'none',
                fontFamily: 'inherit',
              }}
            >
              <div style={{
                fontFamily: t.heading, fontSize: 22, fontWeight: t.heading_weight,
                color: KC_DARK, lineHeight: 1.1, marginBottom: 4,
              }}>
                Aa
              </div>
              <div style={{
                fontFamily: t.body, fontSize: 12, color: '#475569',
                lineHeight: 1.4, marginBottom: 10,
              }}>
                Wir installieren Wärmepumpen mit Festpreis-Garantie.
              </div>
              <div style={{
                fontSize: 12, fontWeight: 800, color: KC_DARK,
                marginBottom: 2, display: 'flex', alignItems: 'center', gap: 6,
              }}>
                {isSelected && <span style={{ color: KC_MID }}>✓</span>}
                {t.label}
              </div>
              <div style={{ fontSize: 10, color: '#64748b', lineHeight: 1.4 }}>
                {t.description}
              </div>
              <div style={{
                fontSize: 9, color: '#94a3b8', marginTop: 4,
                fontFamily: 'ui-monospace, monospace',
              }}>
                {t.heading} / {t.body}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// UIStyleSection — Button + Card Style Karten
// ─────────────────────────────────────────────────────────────────────────────

function UIStyleSection({ uiId, palette, onSelect, onShuffle }) {
  return (
    <div>
      <SectionHeader title="UI-Style" onShuffle={onShuffle} />
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
        gap: 12,
      }}>
        {UI_STYLES.map((u) => {
          const isSelected = u.id === uiId;
          return (
            <button
              key={u.id} type="button"
              onClick={() => onSelect(u.id)}
              style={{
                textAlign: 'left',
                background: '#fff',
                border: isSelected ? `2px solid ${KC_MID}` : '1px solid #e2e8f0',
                borderRadius: 8,
                padding: 14, cursor: 'pointer',
                boxShadow: isSelected ? `0 4px 12px ${KC_MID}33` : 'none',
                fontFamily: 'inherit',
              }}
            >
              {/* Mini-Demo: Button + Card */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                <span style={{
                  display: 'inline-block', padding: '6px 14px',
                  background: palette.accent_1, color: palette.bg_primary,
                  borderRadius: u.button_radius,
                  fontSize: 11, fontWeight: 700,
                }}>
                  Button
                </span>
                <span style={{
                  display: 'inline-block', padding: '6px 14px',
                  background: palette.bg_primary, color: palette.accent_1,
                  border: `${u.border_width} solid ${palette.accent_1}`,
                  borderRadius: u.button_radius,
                  fontSize: 11, fontWeight: 700,
                }}>
                  Outline
                </span>
              </div>
              <div style={{
                background: palette.bg_surface,
                borderRadius: u.card_radius,
                padding: 10,
                border: `${u.border_width} solid ${palette.border}`,
                boxShadow: u.shadow,
                fontSize: 10, color: palette.text_primary, lineHeight: 1.4,
                marginBottom: 12,
              }}>
                Karten-Beispiel — Header + Description.
              </div>
              <div style={{
                fontSize: 12, fontWeight: 800, color: KC_DARK,
                marginBottom: 2, display: 'flex', alignItems: 'center', gap: 6,
              }}>
                {isSelected && <span style={{ color: KC_MID }}>✓</span>}
                {u.label}
              </div>
              <div style={{ fontSize: 10, color: '#64748b', lineHeight: 1.4 }}>
                {u.description}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// LivePreview — Sample Wireframe-Section mit aktuellen Tokens
// ─────────────────────────────────────────────────────────────────────────────

function LivePreview({ palette, typo, ui }) {
  return (
    <div style={{
      background: palette.bg_primary,
      borderRadius: 12, overflow: 'hidden',
      border: `1px solid ${palette.border}`,
      boxShadow: '0 4px 16px rgba(0,0,0,0.06)',
    }}>
      {/* Hero-Sample */}
      <div style={{
        padding: '40px 32px',
        background: palette.bg_primary,
        color: palette.text_primary,
        fontFamily: typo.body,
      }}>
        <div style={{
          fontSize: 11, color: palette.text_muted,
          fontFamily: typo.body, fontWeight: 600,
          textTransform: 'uppercase', letterSpacing: '0.06em',
          marginBottom: 8,
        }}>
          Wallbox-Installation
        </div>
        <h1 style={{
          fontFamily: typo.heading, fontWeight: typo.heading_weight,
          fontSize: 32, lineHeight: 1.15, margin: '0 0 14px',
          color: palette.text_primary,
        }}>
          Förderfähige Wallbox in 14 Tagen — fix installiert.
        </h1>
        <p style={{
          fontSize: 15, lineHeight: 1.5, color: palette.text_muted,
          margin: '0 0 22px', maxWidth: 480,
        }}>
          Wir kümmern uns um Beratung, Antrag, Installation und Anmeldung beim
          Netzbetreiber. Festpreis vorab — keine Überraschungen.
        </p>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <button type="button" style={{
            background: palette.accent_1, color: palette.bg_primary,
            border: 'none', borderRadius: ui.button_radius,
            padding: '10px 20px', fontSize: 13, fontWeight: 700,
            fontFamily: typo.body, cursor: 'pointer',
          }}>
            Festpreis anfragen
          </button>
          <button type="button" style={{
            background: 'transparent', color: palette.accent_1,
            border: `${ui.border_width} solid ${palette.accent_1}`,
            borderRadius: ui.button_radius,
            padding: '10px 20px', fontSize: 13, fontWeight: 700,
            fontFamily: typo.body, cursor: 'pointer',
          }}>
            Beratung vereinbaren
          </button>
        </div>
      </div>

      {/* Trust-Strip */}
      <div style={{
        padding: '20px 32px',
        background: palette.bg_surface,
        borderTop: `1px solid ${palette.border}`,
        display: 'flex', gap: 16, flexWrap: 'wrap', alignItems: 'center',
        fontFamily: typo.body, color: palette.text_muted,
        fontSize: 11, fontWeight: 600,
      }}>
        <span>✓ Innungsmeisterbetrieb</span>
        <span>·</span>
        <span>✓ THG-Quote inklusive</span>
        <span>·</span>
        <span>✓ Festpreis-Garantie</span>
        <span>·</span>
        <span>✓ Förderantrag inklusive</span>
      </div>

      {/* Feature-Cards-Sample */}
      <div style={{
        padding: '32px',
        background: palette.bg_primary,
        borderTop: `1px solid ${palette.border}`,
      }}>
        <h2 style={{
          fontFamily: typo.heading, fontWeight: typo.heading_weight,
          fontSize: 22, color: palette.text_primary, margin: '0 0 18px',
        }}>
          Drei Pakete, ein Festpreis
        </h2>
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: 14,
        }}>
          {[
            { title: 'Standard', desc: '11 kW, einphasig, ideal für Single-Garage' },
            { title: 'Komfort',  desc: '22 kW dreiphasig, Lastmanagement' },
            { title: 'Premium',  desc: 'PV-Integration, App-Steuerung, Förderpaket' },
          ].map((f, i) => (
            <div key={i} style={{
              background: palette.bg_surface,
              border: `${ui.border_width} solid ${palette.border}`,
              borderRadius: ui.card_radius,
              padding: 16,
              boxShadow: ui.shadow,
              fontFamily: typo.body, color: palette.text_primary,
            }}>
              <div style={{
                fontFamily: typo.heading, fontWeight: typo.heading_weight,
                fontSize: 15, color: palette.text_primary, marginBottom: 6,
              }}>
                {f.title}
              </div>
              <div style={{ fontSize: 12, color: palette.text_muted, lineHeight: 1.45 }}>
                {f.desc}
              </div>
              <div style={{
                marginTop: 12,
                display: 'inline-block',
                background: palette.accent_2,
                color: palette.bg_primary,
                padding: '3px 10px',
                borderRadius: ui.button_radius,
                fontSize: 10, fontWeight: 700,
              }}>
                Mehr erfahren →
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

function SectionHeader({ title, onShuffle, children }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      marginBottom: 14, gap: 12, flexWrap: 'wrap',
    }}>
      <div style={{ fontSize: 14, fontWeight: 800, color: KC_DARK, textTransform: 'uppercase', letterSpacing: '-0.01em' }}>
        {title}
      </div>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        {children}
        {onShuffle && (
          <button type="button" onClick={onShuffle}
            title="Konzept zufällig wechseln"
            style={{
              background: 'transparent', color: '#7c3aed',
              border: '1px solid #7c3aed', borderRadius: 6,
              padding: '4px 10px', fontSize: 11, fontWeight: 700,
              cursor: 'pointer', fontFamily: 'inherit',
            }}
          >
            🎲 Würfeln
          </button>
        )}
      </div>
    </div>
  );
}

function ToggleSwitch({ options, value, onChange }) {
  return (
    <div style={{
      display: 'inline-flex', gap: 0,
      border: '1px solid #e2e8f0', borderRadius: 6, overflow: 'hidden',
      background: '#fff',
    }}>
      {options.map((o) => {
        const isActive = value === o.id;
        return (
          <button
            key={o.id} type="button" onClick={() => onChange(o.id)}
            style={{
              padding: '5px 10px',
              background: isActive ? KC_DARK : 'transparent',
              color: isActive ? '#fff' : '#475569',
              border: 'none', cursor: 'pointer',
              fontSize: 11, fontWeight: 700, fontFamily: 'inherit',
            }}
          >
            {o.label}
          </button>
        );
      })}
    </div>
  );
}
