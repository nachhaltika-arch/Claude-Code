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
// Phase E1: Spacing-Scales — Whitespace-Konzepte
// ─────────────────────────────────────────────────────────────────────────────
//
// Jeder Scale liefert eine konsistente 8er-Token-Reihe + Container-Width
// + Section-Padding. Wirkt sich global auf gerenderte Komponenten und
// die Live-Preview aus.

const SPACING_SCALES = [
  {
    id: 'tight', label: 'Eng',
    description: 'Kompakt, B2B-Look — viele Inhalte auf engem Raum.',
    base: 4, scale: [4, 8, 12, 16, 20, 24, 32, 40],
    container: 1100, section_y: 48, gap: 12,
  },
  {
    id: 'default', label: 'Standard',
    description: 'Ausgewogen — klassisches Marketing-Site-Verhältnis.',
    base: 8, scale: [4, 8, 12, 16, 24, 32, 48, 64],
    container: 1200, section_y: 64, gap: 16,
  },
  {
    id: 'comfortable', label: 'Großzügig',
    description: 'Offen — viel Whitespace, hochwertige Markenanmutung.',
    base: 8, scale: [8, 12, 16, 24, 32, 48, 64, 96],
    container: 1280, section_y: 80, gap: 24,
  },
  {
    id: 'spacious', label: 'Editorial',
    description: 'Magazinhaft — generöse Pausen, Premium-Feel.',
    base: 8, scale: [8, 16, 24, 32, 48, 64, 96, 128],
    container: 1360, section_y: 112, gap: 32,
  },
];

// ─────────────────────────────────────────────────────────────────────────────
// Phase E1: Semantic Colors (Status) — KOMPAGNON-Brand-Standard pro Light/Dark
// ─────────────────────────────────────────────────────────────────────────────
//
// Werte aus dem KOMPAGNON-UI/UX-Guidelines-Doc (success/warn/error/info).
// Sind nicht pro Kunde editierbar — Industry-Konvention, soll konsistent
// bleiben. Light/Dark werden vom aktuellen Color-Concept-Modus getriggert.

const SEMANTIC_COLORS = {
  light: {
    success: { fg: '#00875A', bg: '#E3F6EF', border: 'rgba(0,135,90,0.2)' },
    warn:    { fg: '#B8860B', bg: '#FFFBE0', border: 'rgba(184,134,11,0.2)' },
    error:   { fg: '#C0392B', bg: '#FDECEA', border: 'rgba(192,57,43,0.2)' },
    info:    { fg: '#0C7A8E', bg: '#E0F4F8', border: 'rgba(12,122,142,0.2)' },
  },
  dark: {
    success: { fg: '#34D399', bg: 'rgba(52,211,153,0.10)',  border: 'rgba(52,211,153,0.30)' },
    warn:    { fg: '#FBBF24', bg: 'rgba(251,191,36,0.10)',  border: 'rgba(251,191,36,0.30)' },
    error:   { fg: '#F87171', bg: 'rgba(248,113,113,0.10)', border: 'rgba(248,113,113,0.30)' },
    info:    { fg: '#22D3EE', bg: 'rgba(34,211,238,0.10)',  border: 'rgba(34,211,238,0.30)' },
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// Phase E1: Button-Hierarchien — wie ausgepraegt der Primary-CTA wirkt
// ─────────────────────────────────────────────────────────────────────────────
//
// Beeinflusst den Kontrast / Gewicht der Primary- vs Secondary-Variants.
// 'standard'    → klare Hierarchie, Primary = solid bunt
// 'subtle'      → flache Hierarchie, alle Buttons schlicht
// 'prominent'   → starker Primary-Akzent, sehr auffällig

const BUTTON_HIERARCHIES = [
  {
    id: 'standard', label: 'Standard',
    description: 'Solid Primary, Outline Secondary, Ghost Tertiary.',
  },
  {
    id: 'subtle', label: 'Subtil',
    description: 'Alle Buttons schlicht — flache Hierarchie für editorielle Sites.',
  },
  {
    id: 'prominent', label: 'Prominent',
    description: 'Sehr auffälliger Primary mit Schatten — Conversion-Sites.',
  },
];

// ─────────────────────────────────────────────────────────────────────────────
// Phase E2: Form-Stile
// ─────────────────────────────────────────────────────────────────────────────
//
// label_pos: 'above' (klassisch), 'inline' (links neben Input), 'floating'
// (oben über Input, schiebt sich beim Focus). input_style: 'outlined',
// 'filled', 'underlined'.

const FORM_STYLES = [
  {
    id: 'outlined', label: 'Outlined',
    description: 'Klassisch — Border um Input, Label oberhalb. Funktioniert universell.',
    input_style: 'outlined', label_pos: 'above',
  },
  {
    id: 'filled', label: 'Filled',
    description: 'Hellgrauer Background statt Border. Modern, weicher. Material-inspiriert.',
    input_style: 'filled', label_pos: 'above',
  },
  {
    id: 'underlined', label: 'Underlined',
    description: 'Nur unterer Border. Minimal, editorialer Look. Dezent.',
    input_style: 'underlined', label_pos: 'above',
  },
  {
    id: 'floating', label: 'Floating Label',
    description: 'Label springt beim Focus nach oben. Kompakt — gut für lange Forms.',
    input_style: 'outlined', label_pos: 'floating',
  },
];

// ─────────────────────────────────────────────────────────────────────────────
// Phase E2: Card-Varianten
// ─────────────────────────────────────────────────────────────────────────────

const CARD_VARIANTS = [
  {
    id: 'flat', label: 'Flat',
    description: 'Nur Hintergrund-Tint, kein Border, kein Shadow. Sehr ruhig.',
    border_width: '0px', shadow: 'none',
  },
  {
    id: 'bordered', label: 'Bordered',
    description: '1px Border, kein Shadow. Klar abgegrenzt, sachlich.',
    border_width: '1px', shadow: 'none',
  },
  {
    id: 'elevated', label: 'Elevated',
    description: 'Schatten ohne starken Border. Schwebend, interaktiv.',
    border_width: '1px', shadow: '0 4px 14px rgba(0,0,0,0.08)',
  },
  {
    id: 'outlined_heavy', label: 'Outlined Heavy',
    description: '2px Border, kein Shadow. Brutalist, betont strukturell.',
    border_width: '2px', shadow: 'none',
  },
];

// ─────────────────────────────────────────────────────────────────────────────
// Phase E2: Badge-Stile (Status-Pills)
// ─────────────────────────────────────────────────────────────────────────────

const BADGE_STYLES = [
  {
    id: 'pill_filled', label: 'Pill Filled',
    description: 'Vollflächig gefärbt, rund. Auffällig, klassischer Status-Badge.',
    shape: 'pill', fill: 'filled',
  },
  {
    id: 'pill_outlined', label: 'Pill Outlined',
    description: 'Rund mit transparentem Background + Border. Dezent, professionell.',
    shape: 'pill', fill: 'outlined',
  },
  {
    id: 'square_filled', label: 'Square Filled',
    description: 'Kleiner Radius, gefüllt. Eckig, technisch.',
    shape: 'square', fill: 'filled',
  },
  {
    id: 'square_outlined', label: 'Square Outlined',
    description: 'Kleiner Radius, Outline. Editorial, ruhig.',
    shape: 'square', fill: 'outlined',
  },
];

// ─────────────────────────────────────────────────────────────────────────────
// Default Style-Guide & Derivation
// ─────────────────────────────────────────────────────────────────────────────

const DEFAULT_CONCEPT = COLOR_CONCEPTS[0]; // Industrial
const DEFAULT_TYPO    = TYPO_PAIRINGS[0];  // Modern Sans
const DEFAULT_UI      = UI_STYLES[0];      // Soft Cards
const DEFAULT_SPACING = SPACING_SCALES[1]; // Standard
const DEFAULT_BUTTON_HIER = BUTTON_HIERARCHIES[0]; // Standard
const DEFAULT_FORM    = FORM_STYLES[0];    // Outlined
const DEFAULT_CARD    = CARD_VARIANTS[1];  // Bordered
const DEFAULT_BADGE   = BADGE_STYLES[0];   // Pill Filled

function findColorConcept(id) {
  return COLOR_CONCEPTS.find((c) => c.id === id) || DEFAULT_CONCEPT;
}
function findTypoPairing(id) {
  return TYPO_PAIRINGS.find((t) => t.id === id) || DEFAULT_TYPO;
}
function findUIStyle(id) {
  return UI_STYLES.find((u) => u.id === id) || DEFAULT_UI;
}
function findSpacingScale(id) {
  return SPACING_SCALES.find((s) => s.id === id) || DEFAULT_SPACING;
}

// ── Token-Override-Mergers ────────────────────────────────────────────────────
//
// User kann pro Token einen Custom-Wert setzen (Color-Picker / Hex-Input).
// Override wird im styleGuide unter palette_overrides[lightDark] /
// semantic_overrides[lightDark] persistiert. Beim Lookup mergen wir
// Concept-Default + Override.

const PALETTE_TOKEN_KEYS = [
  'bg_primary', 'bg_surface',
  'text_primary', 'text_muted',
  'border',
  'accent_1', 'accent_2', 'accent_3',
];

const PALETTE_TOKEN_LABELS = {
  bg_primary:   'Background · Primary',
  bg_surface:   'Background · Surface',
  text_primary: 'Text · Primary',
  text_muted:   'Text · Muted',
  border:       'Border',
  accent_1:     'Akzent 1 (Primary)',
  accent_2:     'Akzent 2',
  accent_3:     'Akzent 3',
};

const SEMANTIC_KEYS = ['success', 'warn', 'error', 'info'];
const SEMANTIC_LABELS = {
  success: 'Erfolg / Aktiv',
  warn:    'Hinweis / Offen',
  error:   'Fehler / Blockiert',
  info:    'Info / Neutral',
};

function effectivePalette(concept, lightDark, overrides) {
  const base = lightDark === 'dark' ? concept.dark : concept.light;
  const ovr = overrides?.[lightDark] || {};
  return { ...base, ...ovr };
}

function effectiveSemantic(lightDark, overrides) {
  const base = SEMANTIC_COLORS[lightDark === 'dark' ? 'dark' : 'light'];
  const ovr = overrides?.[lightDark] || {};
  // Per-Status mergen — pro Status sind {fg, bg, border} drei separate Slots
  const out = {};
  SEMANTIC_KEYS.forEach((k) => {
    out[k] = { ...base[k], ...(ovr[k] || {}) };
  });
  return out;
}


function findButtonHierarchy(id) {
  return BUTTON_HIERARCHIES.find((b) => b.id === id) || DEFAULT_BUTTON_HIER;
}
function findFormStyle(id) {
  return FORM_STYLES.find((f) => f.id === id) || DEFAULT_FORM;
}
function findCardVariant(id) {
  return CARD_VARIANTS.find((c) => c.id === id) || DEFAULT_CARD;
}
function findBadgeStyle(id) {
  return BADGE_STYLES.find((b) => b.id === id) || DEFAULT_BADGE;
}

// Phase E1: Buttons — pro Hierarchie ein Set Variants (primary/secondary/
// tertiary/destructive). Werte aus palette + ui_style + semantic.
function deriveButtonVariants(palette, uiStyle, hierarchy, semantic) {
  if (hierarchy.id === 'subtle') {
    return {
      primary:     { bg: palette.bg_surface, fg: palette.text_primary, border: palette.border, shadow: 'none' },
      secondary:   { bg: 'transparent', fg: palette.text_primary, border: palette.border, shadow: 'none' },
      tertiary:    { bg: 'transparent', fg: palette.text_muted, border: 'transparent', shadow: 'none' },
      destructive: { bg: 'transparent', fg: semantic.error.fg, border: semantic.error.border, shadow: 'none' },
    };
  }
  if (hierarchy.id === 'prominent') {
    return {
      primary:     { bg: palette.accent_1, fg: palette.bg_primary, border: palette.accent_1, shadow: '0 4px 14px rgba(0,0,0,0.15)' },
      secondary:   { bg: palette.bg_surface, fg: palette.accent_1, border: palette.accent_1, shadow: 'none' },
      tertiary:    { bg: 'transparent', fg: palette.accent_1, border: 'transparent', shadow: 'none' },
      destructive: { bg: semantic.error.fg, fg: '#fff', border: semantic.error.fg, shadow: '0 4px 14px rgba(192,57,43,0.20)' },
    };
  }
  // 'standard'
  return {
    primary:     { bg: palette.accent_1, fg: palette.bg_primary, border: palette.accent_1, shadow: uiStyle.shadow },
    secondary:   { bg: 'transparent', fg: palette.accent_1, border: palette.accent_1, shadow: 'none' },
    tertiary:    { bg: 'transparent', fg: palette.text_primary, border: 'transparent', shadow: 'none' },
    destructive: { bg: semantic.error.fg, fg: '#fff', border: semantic.error.fg, shadow: 'none' },
  };
}

// Phase E2: Form-Tokens aus Form-Style + Palette + UI ableiten.
function deriveFormTokens(palette, uiStyle, formStyle) {
  const isDark = palette.bg_primary === palette.bg_primary && palette.text_primary && palette.text_primary[1] === 'F'; // hacky check, ersetzt unten durch explizites isDark
  return {
    style:        formStyle.input_style,    // outlined | filled | underlined
    label_pos:    formStyle.label_pos,      // above | floating
    radius:       uiStyle.button_radius,    // konsistent zu Buttons
    border_width: uiStyle.border_width,
    bg:           formStyle.input_style === 'filled' ? palette.bg_surface : 'transparent',
    border:       formStyle.input_style === 'outlined'
                    ? palette.border
                    : formStyle.input_style === 'underlined'
                      ? `0 0 1px 0 ${palette.border}`
                      : 'transparent',
    text:         palette.text_primary,
    placeholder:  palette.text_muted,
    focus_color:  palette.accent_1,
  };
}

// Phase E2: Card-Tokens.
function deriveCardTokens(palette, uiStyle, cardVariant, spacingScale) {
  return {
    background:   cardVariant.id === 'flat' ? palette.bg_surface : palette.bg_primary,
    border_width: cardVariant.border_width,
    border_color: palette.border,
    shadow:       cardVariant.shadow,
    radius:       uiStyle.card_radius,
    padding:      `${Math.round(spacingScale.base * 2)}px`,
  };
}

// Phase E2: Badge-Tokens — eine Map { status: { bg, fg, border } } anhand
// Badge-Stil + Semantic-Colors.
function deriveBadgeTokens(badgeStyle, semantic, palette) {
  const radius = badgeStyle.shape === 'pill' ? '999px' : '4px';
  const map = {};
  ['success', 'warn', 'error', 'info'].forEach((key) => {
    const c = semantic[key];
    if (badgeStyle.fill === 'filled') {
      map[key] = { bg: c.fg, fg: '#fff', border: c.fg, radius };
    } else {
      map[key] = { bg: 'transparent', fg: c.fg, border: c.fg, radius };
    }
  });
  // Neutral-Badge zusaetzlich
  if (badgeStyle.fill === 'filled') {
    map.neutral = { bg: palette.text_muted, fg: '#fff', border: palette.text_muted, radius };
  } else {
    map.neutral = { bg: 'transparent', fg: palette.text_muted, border: palette.text_muted, radius };
  }
  return { ...map, shape: badgeStyle.shape, fill: badgeStyle.fill };
}

// Aus Concept-Auswahl die Legacy-Felder ableiten (backwards-compat fuer
// DesignView, Export-Pipeline, etc., die colors.primary etc. erwarten).
// Phase E1: zusaetzlich semantic + spacing_scale + button_variants.
// Phase E2: zusaetzlich forms + card_variant + badge_variants.
function deriveLegacyTokens(
  concept, lightDark, typoPairing, uiStyle, spacingScale, buttonHierarchy,
  formStyle, cardVariant, badgeStyle,
  paletteOverrides = null, semanticOverrides = null,
) {
  // Effektive Tokens: Concept-Default + User-Override
  const palette = effectivePalette(concept, lightDark, paletteOverrides);
  const semantic = effectiveSemantic(lightDark, semanticOverrides);
  const buttonVariants = deriveButtonVariants(palette, uiStyle, buttonHierarchy, semantic);
  const forms          = deriveFormTokens(palette, uiStyle, formStyle);
  const card           = deriveCardTokens(palette, uiStyle, cardVariant, spacingScale);
  const badges         = deriveBadgeTokens(badgeStyle, semantic, palette);
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
      section: spacingScale.section_y,
      base:    spacingScale.base,
      scale:   spacingScale.scale,
      container: spacingScale.container,
      gap:     spacingScale.gap,
    },
    // Phase E1 — neue Felder, additiv
    semantic,
    button_variants: buttonVariants,
    // Phase E2 — neue Felder, additiv
    forms,
    card,
    badges,
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
  const spacingId = styleGuide?.spacing_scale_id || DEFAULT_SPACING.id;
  const btnHierId = styleGuide?.button_hierarchy_id || DEFAULT_BUTTON_HIER.id;
  const formId    = styleGuide?.form_style_id || DEFAULT_FORM.id;
  const cardId    = styleGuide?.card_variant_id || DEFAULT_CARD.id;
  const badgeId   = styleGuide?.badge_style_id || DEFAULT_BADGE.id;

  // Override-Slots: User-spezifische Token-Werte. Fallback = Concept-Default.
  const paletteOverrides  = styleGuide?.palette_overrides  || {};
  const semanticOverrides = styleGuide?.semantic_overrides || {};

  const concept       = findColorConcept(conceptId);
  const typoPairing   = findTypoPairing(typoId);
  const uiStyle       = findUIStyle(uiId);
  const spacingScale  = findSpacingScale(spacingId);
  const buttonHier    = findButtonHierarchy(btnHierId);
  const formStyle     = findFormStyle(formId);
  const cardVariant   = findCardVariant(cardId);
  const badgeStyle    = findBadgeStyle(badgeId);
  // Effektive Tokens (Concept + Override gemerged)
  const palette       = effectivePalette(concept, lightDark, paletteOverrides);
  const semantic      = effectiveSemantic(lightDark, semanticOverrides);
  const buttonVariants = deriveButtonVariants(palette, uiStyle, buttonHier, semantic);
  const forms         = deriveFormTokens(palette, uiStyle, formStyle);
  const card          = deriveCardTokens(palette, uiStyle, cardVariant, spacingScale);
  const badges        = deriveBadgeTokens(badgeStyle, semantic, palette);

  const updateSelection = (updates) => {
    const merged = {
      ...(styleGuide || {}),
      color_concept_id:      updates.conceptId  ?? conceptId,
      light_dark:            updates.lightDark  ?? lightDark,
      typography_pairing_id: updates.typoId     ?? typoId,
      ui_style_id:           updates.uiId       ?? uiId,
      spacing_scale_id:      updates.spacingId  ?? spacingId,
      button_hierarchy_id:   updates.btnHierId  ?? btnHierId,
      form_style_id:         updates.formId     ?? formId,
      card_variant_id:       updates.cardId     ?? cardId,
      badge_style_id:        updates.badgeId    ?? badgeId,
      palette_overrides:     updates.paletteOverrides  ?? paletteOverrides,
      semantic_overrides:    updates.semanticOverrides ?? semanticOverrides,
    };
    const newConcept  = findColorConcept(merged.color_concept_id);
    const newTypo     = findTypoPairing(merged.typography_pairing_id);
    const newUI       = findUIStyle(merged.ui_style_id);
    const newSpacing  = findSpacingScale(merged.spacing_scale_id);
    const newBtnHier  = findButtonHierarchy(merged.button_hierarchy_id);
    const newForm     = findFormStyle(merged.form_style_id);
    const newCard     = findCardVariant(merged.card_variant_id);
    const newBadge    = findBadgeStyle(merged.badge_style_id);
    const derived     = deriveLegacyTokens(
      newConcept, merged.light_dark, newTypo, newUI, newSpacing, newBtnHier,
      newForm, newCard, newBadge,
      merged.palette_overrides, merged.semantic_overrides,
    );
    onChange?.({ ...merged, ...derived });
  };

  // Token-Editor-Helpers — Override pro Token setzen / loeschen
  const setPaletteToken = (key, value) => {
    const lvl = lightDark;
    const next = {
      ...paletteOverrides,
      [lvl]: { ...(paletteOverrides[lvl] || {}), [key]: value },
    };
    updateSelection({ paletteOverrides: next });
  };
  const resetPaletteToken = (key) => {
    const lvl = lightDark;
    const lvlOvr = { ...(paletteOverrides[lvl] || {}) };
    delete lvlOvr[key];
    const next = { ...paletteOverrides, [lvl]: lvlOvr };
    updateSelection({ paletteOverrides: next });
  };
  const setSemanticToken = (status, slot, value) => {
    const lvl = lightDark;
    const next = {
      ...semanticOverrides,
      [lvl]: {
        ...(semanticOverrides[lvl] || {}),
        [status]: {
          ...((semanticOverrides[lvl] || {})[status] || {}),
          [slot]: value,
        },
      },
    };
    updateSelection({ semanticOverrides: next });
  };
  const resetSemanticToken = (status, slot) => {
    const lvl = lightDark;
    const lvlOvr = { ...(semanticOverrides[lvl] || {}) };
    if (lvlOvr[status]) {
      const statusOvr = { ...lvlOvr[status] };
      delete statusOvr[slot];
      if (Object.keys(statusOvr).length === 0) {
        delete lvlOvr[status];
      } else {
        lvlOvr[status] = statusOvr;
      }
    }
    const next = { ...semanticOverrides, [lvl]: lvlOvr };
    updateSelection({ semanticOverrides: next });
  };
  const resetAllOverrides = () => {
    updateSelection({ paletteOverrides: {}, semanticOverrides: {} });
  };

  const shuffle = () => {
    const rand = (arr) => arr[Math.floor(Math.random() * arr.length)];
    updateSelection({
      conceptId: rand(COLOR_CONCEPTS).id,
      typoId:    rand(TYPO_PAIRINGS).id,
      uiId:      rand(UI_STYLES).id,
      spacingId: rand(SPACING_SCALES).id,
      btnHierId: rand(BUTTON_HIERARCHIES).id,
      formId:    rand(FORM_STYLES).id,
      cardId:    rand(CARD_VARIANTS).id,
      badgeId:   rand(BADGE_STYLES).id,
    });
  };

  // Phase E1: 5 Tabs — color, typography, ui, spacing, buttons
  const [activeSection, setActiveSection] = useState('color');

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
          <div style={{ display: 'flex', gap: 4, marginBottom: 18, borderBottom: '1px solid #e2e8f0', flexWrap: 'wrap' }}>
            {[
              { id: 'color',      label: '🎨 Farbe' },
              { id: 'typography', label: '🔤 Typografie' },
              { id: 'spacing',    label: '📐 Spacing' },
              { id: 'ui',         label: '🧩 UI' },
              { id: 'buttons',    label: '🔘 Buttons' },
              { id: 'forms',      label: '📝 Forms' },
              { id: 'cards',      label: '🗂 Cards' },
              { id: 'badges',     label: '🏷 Badges' },
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
              concept={concept}
              palette={palette}
              semantic={semantic}
              paletteOverrides={paletteOverrides}
              semanticOverrides={semanticOverrides}
              onSelect={(id) => updateSelection({ conceptId: id })}
              onToggleLightDark={() => updateSelection({ lightDark: lightDark === 'dark' ? 'light' : 'dark' })}
              onShuffle={() => {
                const r = COLOR_CONCEPTS[Math.floor(Math.random() * COLOR_CONCEPTS.length)];
                updateSelection({ conceptId: r.id });
              }}
              onSetPaletteToken={setPaletteToken}
              onResetPaletteToken={resetPaletteToken}
              onSetSemanticToken={setSemanticToken}
              onResetSemanticToken={resetSemanticToken}
              onResetAll={resetAllOverrides}
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
          {activeSection === 'spacing' && (
            <SpacingSection
              spacingId={spacingId}
              palette={palette}
              onSelect={(id) => updateSelection({ spacingId: id })}
              onShuffle={() => {
                const r = SPACING_SCALES[Math.floor(Math.random() * SPACING_SCALES.length)];
                updateSelection({ spacingId: r.id });
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
          {activeSection === 'buttons' && (
            <ButtonsSection
              btnHierId={btnHierId}
              palette={palette} typo={typoPairing} ui={uiStyle}
              variants={buttonVariants}
              onSelect={(id) => updateSelection({ btnHierId: id })}
              onShuffle={() => {
                const r = BUTTON_HIERARCHIES[Math.floor(Math.random() * BUTTON_HIERARCHIES.length)];
                updateSelection({ btnHierId: r.id });
              }}
            />
          )}
          {activeSection === 'forms' && (
            <FormsSection
              formId={formId}
              palette={palette} typo={typoPairing} ui={uiStyle}
              forms={forms} semantic={semantic}
              onSelect={(id) => updateSelection({ formId: id })}
              onShuffle={() => {
                const r = FORM_STYLES[Math.floor(Math.random() * FORM_STYLES.length)];
                updateSelection({ formId: r.id });
              }}
            />
          )}
          {activeSection === 'cards' && (
            <CardsSection
              cardId={cardId}
              palette={palette} typo={typoPairing} ui={uiStyle}
              card={card} variants={buttonVariants}
              onSelect={(id) => updateSelection({ cardId: id })}
              onShuffle={() => {
                const r = CARD_VARIANTS[Math.floor(Math.random() * CARD_VARIANTS.length)];
                updateSelection({ cardId: r.id });
              }}
            />
          )}
          {activeSection === 'badges' && (
            <BadgesSection
              badgeId={badgeId}
              palette={palette} typo={typoPairing}
              badges={badges} semantic={semantic}
              onSelect={(id) => updateSelection({ badgeId: id })}
              onShuffle={() => {
                const r = BADGE_STYLES[Math.floor(Math.random() * BADGE_STYLES.length)];
                updateSelection({ badgeId: r.id });
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
            Live-Preview · {concept.label} · {lightDark === 'dark' ? 'Dark' : 'Light'} · {typoPairing.label} · {uiStyle.label} · {spacingScale.label} · {buttonHier.label} · {formStyle.label} · {cardVariant.label} · {badgeStyle.label}
          </div>
          <LivePreview
            palette={palette} typo={typoPairing} ui={uiStyle}
            spacing={spacingScale} variants={buttonVariants} semantic={semantic}
            forms={forms} card={card} badges={badges}
          />
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// ColorSection — Concept-Karten mit Light/Dark-Toggle
// ─────────────────────────────────────────────────────────────────────────────

function ColorSection({
  conceptId, lightDark,
  concept, palette, semantic,
  paletteOverrides, semanticOverrides,
  onSelect, onToggleLightDark, onShuffle,
  onSetPaletteToken, onResetPaletteToken,
  onSetSemanticToken, onResetSemanticToken,
  onResetAll,
}) {
  // Concept-Default fuer den aktuellen Light/Dark-Modus — fuer Reset/Diff
  const conceptDefaultPalette = lightDark === 'dark' ? concept.dark : concept.light;
  const semanticDefault = SEMANTIC_COLORS[lightDark === 'dark' ? 'dark' : 'light'];
  const lvlOvr = paletteOverrides?.[lightDark] || {};
  const semOvr = semanticOverrides?.[lightDark] || {};
  const hasAnyOverride =
    Object.keys(paletteOverrides?.light || {}).length +
    Object.keys(paletteOverrides?.dark  || {}).length +
    Object.keys(semanticOverrides?.light || {}).length +
    Object.keys(semanticOverrides?.dark  || {}).length > 0;

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
        marginBottom: 22,
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

      {/* Brand-Token-Editor — pro Token Color-Picker + Hex-Input + Reset */}
      <div style={{
        display: 'flex', alignItems: 'baseline', justifyContent: 'space-between',
        marginBottom: 8, gap: 8,
      }}>
        <div style={{
          fontSize: 13, fontWeight: 800, color: KC_DARK,
          textTransform: 'uppercase', letterSpacing: '-0.01em',
        }}>
          Brand-Tokens · {lightDark === 'dark' ? 'Dark' : 'Light'}
        </div>
        {hasAnyOverride && (
          <button type="button" onClick={onResetAll}
            style={{
              background: 'transparent', color: '#dc2626',
              border: '1px solid #fca5a5', borderRadius: 6,
              padding: '4px 10px', fontSize: 10, fontWeight: 700,
              cursor: 'pointer', fontFamily: 'inherit',
            }}>
            ↺ Alle Overrides verwerfen
          </button>
        )}
      </div>
      <div style={{
        fontSize: 11, color: '#64748b', marginBottom: 14, lineHeight: 1.5,
      }}>
        Konzept-Defaults oben — pro Token überschreibbar via Color-Picker oder Hex-Input.
        Override gilt nur für den aktuellen {lightDark === 'dark' ? 'Dark' : 'Light'}-Modus.
      </div>
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 10,
        marginBottom: 22,
      }}>
        {PALETTE_TOKEN_KEYS.map((key) => (
          <TokenEditor
            key={key}
            label={PALETTE_TOKEN_LABELS[key]}
            value={palette[key]}
            defaultValue={conceptDefaultPalette[key]}
            isOverridden={key in lvlOvr}
            onChange={(v) => onSetPaletteToken(key, v)}
            onReset={() => onResetPaletteToken(key)}
          />
        ))}
      </div>

      {/* Semantic-Token-Editor — pro Status × {fg, bg, border} */}
      <div style={{
        fontSize: 13, fontWeight: 800, color: KC_DARK,
        textTransform: 'uppercase', letterSpacing: '-0.01em', marginBottom: 8,
      }}>
        Semantische Status-Farben · {lightDark === 'dark' ? 'Dark' : 'Light'}
      </div>
      <div style={{
        fontSize: 11, color: '#64748b', marginBottom: 14, lineHeight: 1.5,
      }}>
        Industry-Konvention als Default — pro Status drei Slots editierbar
        (Vordergrund / Background / Border).
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {SEMANTIC_KEYS.map((status) => {
          const c = semantic[status];
          const def = semanticDefault[status];
          const ovrStatus = semOvr[status] || {};
          return (
            <div key={status} style={{
              padding: 12,
              background: c.bg,
              border: `1px solid ${c.border}`,
              borderRadius: 8,
            }}>
              <div style={{
                fontSize: 11, fontWeight: 800, color: c.fg,
                textTransform: 'uppercase', letterSpacing: '0.06em',
                marginBottom: 10,
              }}>
                {SEMANTIC_LABELS[status]}
              </div>
              <div style={{
                display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 8,
              }}>
                {['fg', 'bg', 'border'].map((slot) => (
                  <TokenEditor
                    key={slot}
                    label={slot === 'fg' ? 'Vordergrund' : slot === 'bg' ? 'Background' : 'Border'}
                    value={c[slot]}
                    defaultValue={def[slot]}
                    isOverridden={slot in ovrStatus}
                    onChange={(v) => onSetSemanticToken(status, slot, v)}
                    onReset={() => onResetSemanticToken(status, slot)}
                    compact
                  />
                ))}
              </div>
            </div>
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
// Phase E1: SpacingSection — Spacing-Scale Konzept-Karten
// ─────────────────────────────────────────────────────────────────────────────

function SpacingSection({ spacingId, palette, onSelect, onShuffle }) {
  return (
    <div>
      <SectionHeader title="Spacing-Scale" onShuffle={onShuffle} />
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
        gap: 12,
      }}>
        {SPACING_SCALES.map((s) => {
          const isSelected = s.id === spacingId;
          return (
            <button
              key={s.id} type="button"
              onClick={() => onSelect(s.id)}
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
              {/* Visualisierung der Scale: 8 unterschiedlich grosse Bloecke */}
              <div style={{
                display: 'flex', alignItems: 'flex-end', gap: 3,
                marginBottom: 10, height: 40,
              }}>
                {s.scale.map((value, idx) => (
                  <div key={idx} style={{
                    width: 6,
                    height: `${Math.min(100, (value / 128) * 100)}%`,
                    background: palette.accent_1,
                    opacity: 0.4 + (idx / s.scale.length) * 0.6,
                    borderRadius: 1,
                  }} />
                ))}
              </div>
              <div style={{
                fontSize: 12, fontWeight: 800, color: KC_DARK,
                marginBottom: 2, display: 'flex', alignItems: 'center', gap: 6,
              }}>
                {isSelected && <span style={{ color: KC_MID }}>✓</span>}
                {s.label}
              </div>
              <div style={{ fontSize: 10, color: '#64748b', lineHeight: 1.4, marginBottom: 6 }}>
                {s.description}
              </div>
              <div style={{
                fontSize: 9, color: '#94a3b8',
                fontFamily: 'ui-monospace, monospace',
              }}>
                Base {s.base}px · Container {s.container}px · Section-Y {s.section_y}px
              </div>
            </button>
          );
        })}
      </div>

      {/* Token-Tabelle */}
      <div style={{ marginTop: 22 }}>
        <div style={{
          fontSize: 13, fontWeight: 800, color: KC_DARK,
          textTransform: 'uppercase', letterSpacing: '-0.01em', marginBottom: 8,
        }}>
          Spacing-Tokens
        </div>
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(80px, 1fr))', gap: 8,
        }}>
          {findSpacingScale(spacingId).scale.map((value, idx) => (
            <div key={idx} style={{
              padding: 10, background: '#fff', border: '1px solid #e2e8f0', borderRadius: 6,
              textAlign: 'center',
            }}>
              <div style={{
                fontSize: 9, fontWeight: 700, color: '#64748b',
                textTransform: 'uppercase', letterSpacing: '0.06em',
              }}>
                token-{idx + 1}
              </div>
              <div style={{
                fontSize: 14, fontWeight: 800, color: KC_DARK,
                fontFamily: 'ui-monospace, monospace',
                marginTop: 4,
              }}>
                {value}px
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Phase E1: ButtonsSection — Button-Hierarchie + 4 Variants × 3 Sizes Demo
// ─────────────────────────────────────────────────────────────────────────────

function ButtonsSection({ btnHierId, palette, typo, ui, variants, onSelect, onShuffle }) {
  return (
    <div>
      <SectionHeader title="Button-Hierarchie" onShuffle={onShuffle} />
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))',
        gap: 12, marginBottom: 22,
      }}>
        {BUTTON_HIERARCHIES.map((h) => {
          const isSelected = h.id === btnHierId;
          // Pro Karte eine kleine Mini-Demo (3 Buttons)
          const demoVariants = deriveButtonVariants(palette, ui, h, SEMANTIC_COLORS.light);
          return (
            <button
              key={h.id} type="button"
              onClick={() => onSelect(h.id)}
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
              <div style={{ display: 'flex', gap: 6, marginBottom: 10, flexWrap: 'wrap' }}>
                <MiniButton v={demoVariants.primary} ui={ui} typo={typo}>Primary</MiniButton>
                <MiniButton v={demoVariants.secondary} ui={ui} typo={typo}>Outline</MiniButton>
                <MiniButton v={demoVariants.tertiary} ui={ui} typo={typo}>Ghost</MiniButton>
              </div>
              <div style={{
                fontSize: 12, fontWeight: 800, color: KC_DARK,
                marginBottom: 2, display: 'flex', alignItems: 'center', gap: 6,
              }}>
                {isSelected && <span style={{ color: KC_MID }}>✓</span>}
                {h.label}
              </div>
              <div style={{ fontSize: 10, color: '#64748b', lineHeight: 1.4 }}>
                {h.description}
              </div>
            </button>
          );
        })}
      </div>

      {/* Volle Variants × Sizes Matrix */}
      <div style={{
        fontSize: 13, fontWeight: 800, color: KC_DARK,
        textTransform: 'uppercase', letterSpacing: '-0.01em', marginBottom: 8,
      }}>
        4 Variants × 3 Sizes
      </div>
      <div style={{
        background: palette.bg_primary, padding: 16, borderRadius: 8,
        border: `1px solid ${palette.border}`,
      }}>
        {[
          { name: 'Primary',     v: variants.primary },
          { name: 'Secondary',   v: variants.secondary },
          { name: 'Tertiary',    v: variants.tertiary },
          { name: 'Destructive', v: variants.destructive },
        ].map((row) => (
          <div key={row.name} style={{
            display: 'flex', alignItems: 'center', gap: 14,
            padding: '10px 0',
            borderBottom: `1px solid ${palette.border}`,
          }}>
            <div style={{
              minWidth: 90,
              fontSize: 10, fontWeight: 700, color: palette.text_muted,
              textTransform: 'uppercase', letterSpacing: '0.06em',
              fontFamily: typo.body,
            }}>
              {row.name}
            </div>
            <SizedButton v={row.v} ui={ui} typo={typo} size="small">Klein</SizedButton>
            <SizedButton v={row.v} ui={ui} typo={typo} size="medium">Standard</SizedButton>
            <SizedButton v={row.v} ui={ui} typo={typo} size="large">Groß</SizedButton>
          </div>
        ))}
      </div>
    </div>
  );
}

function MiniButton({ v, ui, typo, children }) {
  return (
    <span style={{
      display: 'inline-block',
      padding: '5px 10px',
      background: v.bg, color: v.fg,
      border: `1px solid ${v.border}`,
      borderRadius: ui.button_radius,
      fontSize: 10, fontWeight: 700, fontFamily: typo.body,
      boxShadow: v.shadow,
    }}>
      {children}
    </span>
  );
}

function SizedButton({ v, ui, typo, size, children }) {
  const sizes = {
    small:  { padding: '6px 14px',  fontSize: 11 },
    medium: { padding: '9px 18px',  fontSize: 13 },
    large:  { padding: '12px 24px', fontSize: 14 },
  };
  const sz = sizes[size];
  return (
    <button type="button"
      style={{
        padding: sz.padding,
        background: v.bg, color: v.fg,
        border: `1px solid ${v.border}`,
        borderRadius: ui.button_radius,
        fontSize: sz.fontSize, fontWeight: 700, fontFamily: typo.body,
        boxShadow: v.shadow,
        cursor: 'pointer',
      }}
      onClick={(e) => e.preventDefault()}
    >
      {children}
    </button>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Phase E2: FormsSection — Form-Style-Karten + Demo-Formular
// ─────────────────────────────────────────────────────────────────────────────

function FormsSection({ formId, palette, typo, ui, forms, semantic, onSelect, onShuffle }) {
  return (
    <div>
      <SectionHeader title="Formular-Stile" onShuffle={onShuffle} />
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))',
        gap: 12, marginBottom: 22,
      }}>
        {FORM_STYLES.map((f) => {
          const isSelected = f.id === formId;
          return (
            <button
              key={f.id} type="button"
              onClick={() => onSelect(f.id)}
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
              <div style={{ marginBottom: 12 }}>
                <FormPreview style={f} palette={palette} ui={ui} typo={typo} compact />
              </div>
              <div style={{
                fontSize: 12, fontWeight: 800, color: KC_DARK,
                marginBottom: 2, display: 'flex', alignItems: 'center', gap: 6,
              }}>
                {isSelected && <span style={{ color: KC_MID }}>✓</span>}
                {f.label}
              </div>
              <div style={{ fontSize: 10, color: '#64748b', lineHeight: 1.4 }}>
                {f.description}
              </div>
            </button>
          );
        })}
      </div>

      {/* Volles Demo-Formular */}
      <div style={{
        fontSize: 13, fontWeight: 800, color: KC_DARK,
        textTransform: 'uppercase', letterSpacing: '-0.01em', marginBottom: 8,
      }}>
        Demo-Formular
      </div>
      <div style={{
        background: palette.bg_primary, padding: 18, borderRadius: 8,
        border: `1px solid ${palette.border}`,
      }}>
        <FormPreview style={findFormStyle(formId)} palette={palette} ui={ui} typo={typo} semantic={semantic} />
      </div>
    </div>
  );
}

function FormPreview({ style, palette, ui, typo, semantic, compact = false }) {
  const isFloating = style.label_pos === 'floating';
  const inputBg = style.input_style === 'filled' ? palette.bg_surface : palette.bg_primary;
  const baseInput = {
    width: '100%', boxSizing: 'border-box',
    padding: compact ? '6px 8px' : '10px 12px',
    fontSize: compact ? 11 : 13,
    fontFamily: typo.body, color: palette.text_primary,
    background: inputBg, outline: 'none',
  };
  const inputStyle = (() => {
    if (style.input_style === 'outlined') {
      return { ...baseInput, border: `1px solid ${palette.border}`, borderRadius: ui.button_radius };
    }
    if (style.input_style === 'underlined') {
      return { ...baseInput, border: 'none', borderBottom: `1px solid ${palette.border}`, borderRadius: 0, padding: compact ? '6px 0' : '10px 0' };
    }
    if (style.input_style === 'filled') {
      return { ...baseInput, border: 'none', borderRadius: ui.button_radius };
    }
    return baseInput;
  })();

  const labelStyle = {
    display: 'block', fontSize: compact ? 9 : 10,
    fontWeight: 700, color: palette.text_muted,
    textTransform: 'uppercase', letterSpacing: '0.06em',
    marginBottom: compact ? 3 : 5,
    fontFamily: typo.body,
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: compact ? 8 : 14 }}>
      <div>
        {!isFloating && <label style={labelStyle}>Name</label>}
        <div style={{ position: 'relative' }}>
          <input type="text" placeholder={isFloating ? 'Name' : (compact ? 'Max Mustermann' : 'Max Mustermann')} style={inputStyle} />
        </div>
      </div>
      {!compact && (
        <>
          <div>
            {!isFloating && <label style={labelStyle}>E-Mail</label>}
            <input type="email" placeholder={isFloating ? 'E-Mail' : 'max@example.de'} style={inputStyle} />
          </div>
          <div>
            {!isFloating && <label style={labelStyle}>Anliegen</label>}
            <textarea
              placeholder={isFloating ? 'Anliegen' : 'Kurze Beschreibung…'}
              rows={3}
              style={{ ...inputStyle, resize: 'vertical', minHeight: 60, fontFamily: typo.body }}
            />
          </div>
          {/* Error-State Beispiel */}
          <div>
            <label style={{ ...labelStyle, color: semantic?.error?.fg || '#C0392B' }}>
              Telefon * (Pflichtfeld)
            </label>
            <input type="tel" defaultValue=""
              style={{ ...inputStyle, borderColor: semantic?.error?.fg || '#C0392B' }} />
            <div style={{
              fontSize: 10, color: semantic?.error?.fg || '#C0392B',
              marginTop: 4, fontFamily: typo.body,
            }}>
              ⚠ Bitte Telefonnummer angeben
            </div>
          </div>
        </>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Phase E2: CardsSection — Card-Variant-Karten + Demo-Cards
// ─────────────────────────────────────────────────────────────────────────────

function CardsSection({ cardId, palette, typo, ui, card, variants, onSelect, onShuffle }) {
  return (
    <div>
      <SectionHeader title="Card-Varianten" onShuffle={onShuffle} />
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))',
        gap: 12, marginBottom: 22,
      }}>
        {CARD_VARIANTS.map((c) => {
          const isSelected = c.id === cardId;
          return (
            <button
              key={c.id} type="button"
              onClick={() => onSelect(c.id)}
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
              <CardPreview variant={c} palette={palette} ui={ui} typo={typo} compact />
              <div style={{
                fontSize: 12, fontWeight: 800, color: KC_DARK,
                marginTop: 10, marginBottom: 2,
                display: 'flex', alignItems: 'center', gap: 6,
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

      {/* Drei Demo-Cards in voller Groesse */}
      <div style={{
        fontSize: 13, fontWeight: 800, color: KC_DARK,
        textTransform: 'uppercase', letterSpacing: '-0.01em', marginBottom: 8,
      }}>
        Demo-Cards
      </div>
      <div style={{
        background: palette.bg_surface, padding: 18, borderRadius: 8,
        display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 14,
      }}>
        {[
          { title: 'Wärmepumpe', desc: 'Beratung + Antrag + Installation aus einer Hand.' },
          { title: 'Wallbox',    desc: 'Förderfähige Installation in 14 Tagen.' },
          { title: 'Notdienst',  desc: '24/7 — Heizung, Wasser, Strom.' },
        ].map((d, i) => (
          <CardPreview
            key={i} variant={findCardVariant(cardId)}
            palette={palette} ui={ui} typo={typo}
            title={d.title} desc={d.desc}
            primary={variants?.primary}
          />
        ))}
      </div>
    </div>
  );
}

function CardPreview({ variant, palette, ui, typo, compact = false, title, desc, primary }) {
  const cardStyle = {
    background: variant.id === 'flat' ? palette.bg_surface : palette.bg_primary,
    border: variant.border_width === '0px' ? 'none' : `${variant.border_width} solid ${palette.border}`,
    borderRadius: ui.card_radius,
    boxShadow: variant.shadow,
    padding: compact ? 10 : 16,
    fontFamily: typo.body, color: palette.text_primary,
  };

  if (compact) {
    return (
      <div style={cardStyle}>
        <div style={{
          height: 36, background: palette.bg_surface,
          borderRadius: 4, marginBottom: 6,
        }} />
        <div style={{
          fontFamily: typo.heading, fontWeight: typo.heading_weight,
          fontSize: 11, color: palette.text_primary,
        }}>
          Karten-Titel
        </div>
        <div style={{ fontSize: 9, color: palette.text_muted, marginTop: 2 }}>
          Beispieltext
        </div>
      </div>
    );
  }

  return (
    <div style={cardStyle}>
      <div style={{
        height: 80, background: palette.bg_surface,
        borderRadius: variant.id === 'flat' ? 0 : 4,
        marginBottom: 10,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: palette.text_muted, fontSize: 12,
      }}>
        Bild-Placeholder
      </div>
      <div style={{
        fontFamily: typo.heading, fontWeight: typo.heading_weight,
        fontSize: 16, color: palette.text_primary, marginBottom: 6,
      }}>
        {title}
      </div>
      <div style={{ fontSize: 12, color: palette.text_muted, lineHeight: 1.5, marginBottom: 12 }}>
        {desc}
      </div>
      {primary && (
        <button type="button" style={{
          padding: '6px 14px',
          background: primary.bg, color: primary.fg,
          border: `1px solid ${primary.border}`,
          borderRadius: ui.button_radius,
          fontSize: 11, fontWeight: 700, fontFamily: typo.body,
          cursor: 'pointer', boxShadow: primary.shadow,
        }}>
          Mehr →
        </button>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Phase E2: BadgesSection — Badge-Style-Karten + Status-Matrix
// ─────────────────────────────────────────────────────────────────────────────

function BadgesSection({ badgeId, palette, typo, badges, semantic, onSelect, onShuffle }) {
  return (
    <div>
      <SectionHeader title="Badge-Stile" onShuffle={onShuffle} />
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))',
        gap: 12, marginBottom: 22,
      }}>
        {BADGE_STYLES.map((b) => {
          const isSelected = b.id === badgeId;
          const demoBadges = deriveBadgeTokens(b, semantic, palette);
          return (
            <button
              key={b.id} type="button"
              onClick={() => onSelect(b.id)}
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
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 10 }}>
                <DemoBadge tokens={demoBadges.success} typo={typo}>Aktiv</DemoBadge>
                <DemoBadge tokens={demoBadges.warn} typo={typo}>Offen</DemoBadge>
                <DemoBadge tokens={demoBadges.error} typo={typo}>Fehler</DemoBadge>
              </div>
              <div style={{
                fontSize: 12, fontWeight: 800, color: KC_DARK,
                marginBottom: 2, display: 'flex', alignItems: 'center', gap: 6,
              }}>
                {isSelected && <span style={{ color: KC_MID }}>✓</span>}
                {b.label}
              </div>
              <div style={{ fontSize: 10, color: '#64748b', lineHeight: 1.4 }}>
                {b.description}
              </div>
            </button>
          );
        })}
      </div>

      {/* Status-Matrix: alle 5 Status × 2 Sizes */}
      <div style={{
        fontSize: 13, fontWeight: 800, color: KC_DARK,
        textTransform: 'uppercase', letterSpacing: '-0.01em', marginBottom: 8,
      }}>
        Status × Sizes
      </div>
      <div style={{
        background: palette.bg_primary, padding: 18, borderRadius: 8,
        border: `1px solid ${palette.border}`,
      }}>
        {[
          { key: 'success', label: 'Aktiv / Bewilligt' },
          { key: 'warn',    label: 'In Bearbeitung' },
          { key: 'error',   label: 'Abgelehnt' },
          { key: 'info',    label: 'Info' },
          { key: 'neutral', label: 'Neutral' },
        ].map((row) => (
          <div key={row.key} style={{
            display: 'flex', alignItems: 'center', gap: 14,
            padding: '10px 0',
            borderBottom: `1px solid ${palette.border}`,
          }}>
            <div style={{
              minWidth: 130, fontSize: 10, fontWeight: 700, color: palette.text_muted,
              textTransform: 'uppercase', letterSpacing: '0.06em', fontFamily: typo.body,
            }}>
              {row.label}
            </div>
            <DemoBadge tokens={badges[row.key]} typo={typo} size="small">Klein</DemoBadge>
            <DemoBadge tokens={badges[row.key]} typo={typo} size="default">Standard</DemoBadge>
          </div>
        ))}
      </div>
    </div>
  );
}

function DemoBadge({ tokens, typo, size = 'default', children }) {
  const sizes = {
    small:   { padding: '2px 8px',  fontSize: 9 },
    default: { padding: '3px 10px', fontSize: 10 },
  };
  const sz = sizes[size];
  return (
    <span style={{
      display: 'inline-block',
      padding: sz.padding,
      background: tokens.bg, color: tokens.fg,
      border: `1px solid ${tokens.border}`,
      borderRadius: tokens.radius,
      fontSize: sz.fontSize, fontWeight: 700, fontFamily: typo.body,
      textTransform: 'uppercase', letterSpacing: '0.06em',
    }}>
      {children}
    </span>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// TokenEditor — Color-Picker + Hex-Input + Reset-Button pro Token
// ─────────────────────────────────────────────────────────────────────────────
//
// Akzeptiert beliebige CSS-Color-Strings (#hex, rgb(), rgba()). Color-Picker
// zeigt nur den Hex-Teil; rgba() bleibt im Text-Input editierbar.

function TokenEditor({ label, value, defaultValue, isOverridden, onChange, onReset, compact = false }) {
  // Picker-Wert immer 6-stelliger Hex; rgba() wird im Input-Feld editiert
  const isHex = typeof value === 'string' && /^#[0-9a-fA-F]{6}$/.test(value);
  const pickerValue = isHex ? value : '#888888';

  return (
    <div style={{
      padding: compact ? 6 : 8,
      background: '#fff',
      border: `1px solid ${isOverridden ? '#7c3aed' : '#e2e8f0'}`,
      borderRadius: 6,
    }}>
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        marginBottom: 6, gap: 6,
      }}>
        <div style={{
          fontSize: 9, fontWeight: 700, color: '#64748b',
          textTransform: 'uppercase', letterSpacing: '0.06em',
          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
          flex: 1, minWidth: 0,
        }}>
          {label}
        </div>
        {isOverridden && (
          <button type="button" onClick={onReset}
            title="Zurueck zum Concept-Default"
            style={{
              background: 'transparent', border: 'none',
              color: '#7c3aed', cursor: 'pointer',
              fontSize: 11, padding: 0, lineHeight: 1,
            }}>
            ↺
          </button>
        )}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <input
          type="color"
          value={pickerValue}
          onChange={(e) => onChange(e.target.value)}
          style={{
            width: compact ? 28 : 32,
            height: compact ? 28 : 32,
            border: '1px solid #cbd5e1', borderRadius: 4,
            padding: 0, background: 'transparent',
            cursor: 'pointer', flexShrink: 0,
          }}
          aria-label={`${label} Farbe wählen`}
        />
        <input
          type="text"
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          placeholder={defaultValue}
          spellCheck={false}
          style={{
            flex: 1, minWidth: 0,
            padding: '5px 7px',
            border: '1px solid #e2e8f0', borderRadius: 4,
            fontSize: compact ? 10 : 11,
            fontFamily: 'ui-monospace, monospace',
            color: '#334155', outline: 'none', background: '#fff',
          }}
        />
      </div>
      {isOverridden && (
        <div style={{
          fontSize: 8, color: '#94a3b8', marginTop: 3,
          fontFamily: 'ui-monospace, monospace',
        }}>
          Default: {defaultValue}
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// LivePreview — Sample Wireframe-Section mit aktuellen Tokens
// ─────────────────────────────────────────────────────────────────────────────

function LivePreview({ palette, typo, ui, spacing, variants, semantic, forms, card, badges }) {
  // Phase E1: Spacing-Scale fließt in Padding/Gap-Werte ein.
  const spX = spacing?.scale?.[5] ?? 32;       // ~32px Standard
  const spY = spacing?.section_y ?? 64;        // Section vertical
  const gap = spacing?.gap ?? 16;
  // Variants kommen vom Parent (Button-Hierarchy + Color-Concept). Falls fehlt
  // (alte aufrufer ohne Phase-E1-Felder), Fallback auf naive Defaults.
  const primary   = variants?.primary   || { bg: palette.accent_1, fg: palette.bg_primary, border: palette.accent_1, shadow: ui.shadow };
  const secondary = variants?.secondary || { bg: 'transparent', fg: palette.accent_1, border: palette.accent_1, shadow: 'none' };

  return (
    <div style={{
      background: palette.bg_primary,
      borderRadius: 12, overflow: 'hidden',
      border: `1px solid ${palette.border}`,
      boxShadow: '0 4px 16px rgba(0,0,0,0.06)',
    }}>
      {/* Hero-Sample — Padding aus Spacing-Scale */}
      <div style={{
        padding: `${spY * 0.6}px ${spX}px`,
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
          fontSize: 32, lineHeight: 1.15, margin: `0 0 ${gap}px`,
          color: palette.text_primary,
        }}>
          Förderfähige Wallbox in 14 Tagen — fix installiert.
        </h1>
        <p style={{
          fontSize: 15, lineHeight: 1.5, color: palette.text_muted,
          margin: `0 0 ${gap * 1.5}px`, maxWidth: 480,
        }}>
          Wir kümmern uns um Beratung, Antrag, Installation und Anmeldung beim
          Netzbetreiber. Festpreis vorab — keine Überraschungen.
        </p>
        <div style={{ display: 'flex', gap: gap * 0.6, flexWrap: 'wrap' }}>
          <button type="button" style={{
            background: primary.bg, color: primary.fg,
            border: `1px solid ${primary.border}`, borderRadius: ui.button_radius,
            padding: '10px 20px', fontSize: 13, fontWeight: 700,
            fontFamily: typo.body, cursor: 'pointer', boxShadow: primary.shadow,
          }}>
            Festpreis anfragen
          </button>
          <button type="button" style={{
            background: secondary.bg, color: secondary.fg,
            border: `${ui.border_width} solid ${secondary.border}`,
            borderRadius: ui.button_radius,
            padding: '10px 20px', fontSize: 13, fontWeight: 700,
            fontFamily: typo.body, cursor: 'pointer',
          }}>
            Beratung vereinbaren
          </button>
        </div>

        {/* Phase E1: Status-Streifen mit Semantic Colors */}
        {semantic && (
          <div style={{
            display: 'flex', gap: gap * 0.5, flexWrap: 'wrap',
            marginTop: gap * 1.5,
          }}>
            {[
              { key: 'success', label: '✓ Förderung bewilligt' },
              { key: 'warn',    label: '⏱ Termin in Bearbeitung' },
              { key: 'info',    label: 'ℹ THG-Quote inklusive' },
            ].map((s) => {
              const c = semantic[s.key];
              return (
                <span key={s.key} style={{
                  padding: '4px 10px',
                  background: c.bg, color: c.fg,
                  border: `1px solid ${c.border}`,
                  borderRadius: ui.button_radius,
                  fontSize: 10, fontWeight: 700, fontFamily: typo.body,
                }}>
                  {s.label}
                </span>
              );
            })}
          </div>
        )}
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

      {/* Feature-Cards-Sample — Phase E2: Card + Badge Tokens */}
      <div style={{
        padding: `${spY * 0.5}px ${spX}px`,
        background: palette.bg_primary,
        borderTop: `1px solid ${palette.border}`,
      }}>
        <h2 style={{
          fontFamily: typo.heading, fontWeight: typo.heading_weight,
          fontSize: 22, color: palette.text_primary, margin: `0 0 ${gap}px`,
        }}>
          Drei Pakete, ein Festpreis
        </h2>
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: gap,
        }}>
          {[
            { title: 'Standard', desc: '11 kW, einphasig, ideal für Single-Garage', status: 'info',    statusLabel: 'Beliebt' },
            { title: 'Komfort',  desc: '22 kW dreiphasig, Lastmanagement',           status: 'success', statusLabel: 'Empfohlen' },
            { title: 'Premium',  desc: 'PV-Integration, App-Steuerung, Förderpaket', status: 'warn',    statusLabel: 'Limitiert' },
          ].map((f, i) => (
            <div key={i} style={{
              background: card?.background || palette.bg_surface,
              border: card?.border_width === '0px'
                ? 'none'
                : `${card?.border_width || ui.border_width} solid ${card?.border_color || palette.border}`,
              borderRadius: card?.radius || ui.card_radius,
              padding: card?.padding || '16px',
              boxShadow: card?.shadow || ui.shadow,
              fontFamily: typo.body, color: palette.text_primary,
              position: 'relative',
            }}>
              {badges?.[f.status] && (
                <span style={{
                  position: 'absolute', top: 10, right: 10,
                  padding: '2px 8px',
                  background: badges[f.status].bg, color: badges[f.status].fg,
                  border: `1px solid ${badges[f.status].border}`,
                  borderRadius: badges[f.status].radius,
                  fontSize: 9, fontWeight: 700, fontFamily: typo.body,
                  textTransform: 'uppercase', letterSpacing: '0.06em',
                }}>
                  {f.statusLabel}
                </span>
              )}
              <div style={{
                fontFamily: typo.heading, fontWeight: typo.heading_weight,
                fontSize: 15, color: palette.text_primary, marginBottom: 6,
                paddingRight: 70,
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

      {/* Phase E2: Inline-Form-Demo am Ende der Preview */}
      {forms && (
        <div style={{
          padding: `${spY * 0.5}px ${spX}px`,
          background: palette.bg_surface,
          borderTop: `1px solid ${palette.border}`,
        }}>
          <h3 style={{
            fontFamily: typo.heading, fontWeight: typo.heading_weight,
            fontSize: 18, color: palette.text_primary, margin: `0 0 ${gap}px`,
          }}>
            Kostenlose Beratung
          </h3>
          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: gap * 0.7,
          }}>
            <input
              type="text" placeholder="Name"
              style={{
                padding: '10px 12px', fontSize: 13, fontFamily: typo.body,
                color: palette.text_primary,
                background: forms.style === 'filled' ? palette.bg_primary : 'transparent',
                border: forms.style === 'underlined'
                  ? `0 0 1px 0 ${palette.border}`
                  : forms.style === 'outlined'
                    ? `1px solid ${palette.border}`
                    : 'none',
                borderBottom: forms.style === 'underlined' ? `1px solid ${palette.border}` : undefined,
                borderRadius: forms.style === 'underlined' ? 0 : ui.button_radius,
                outline: 'none',
              }}
            />
            <input
              type="email" placeholder="E-Mail"
              style={{
                padding: '10px 12px', fontSize: 13, fontFamily: typo.body,
                color: palette.text_primary,
                background: forms.style === 'filled' ? palette.bg_primary : 'transparent',
                border: forms.style === 'underlined'
                  ? `0 0 1px 0 ${palette.border}`
                  : forms.style === 'outlined'
                    ? `1px solid ${palette.border}`
                    : 'none',
                borderBottom: forms.style === 'underlined' ? `1px solid ${palette.border}` : undefined,
                borderRadius: forms.style === 'underlined' ? 0 : ui.button_radius,
                outline: 'none',
              }}
            />
            <button type="button" style={{
              background: primary.bg, color: primary.fg,
              border: `1px solid ${primary.border}`, borderRadius: ui.button_radius,
              padding: '10px 16px', fontSize: 12, fontWeight: 700,
              fontFamily: typo.body, cursor: 'pointer', boxShadow: primary.shadow,
            }}>
              Termin anfragen
            </button>
          </div>
        </div>
      )}
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
