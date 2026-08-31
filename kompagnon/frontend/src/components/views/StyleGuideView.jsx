/**
 * StyleGuideView — Relume-Style 3-Section-Layout.
 *
 * Drei Top-Level-Sections in einer einzigen Edit-Spalte: Colors, Typography,
 * UI Styling. Rechts daneben Live-Preview mit Device-Toggle. Footer haelt den
 * "Scheme shuffle"-Button fuer alles auf einmal. Pro Section gibt es einen
 * Shuffle-Pin mit Keyboard-Shortcut (C/T/U), SPACE wuerfelt das ganze Schema.
 *
 * Die kuratierten Konzepte (COLOR_CONCEPTS, TYPO_PAIRINGS, UI_STYLES, ...)
 * bleiben als Datenquelle fuer Shuffle und Defaults. Sichtbar werden sie
 * jedoch nicht mehr als Karten — der User sieht direkt die Token-Werte.
 *
 * Schema-Strategie: identisch zur bisherigen Implementierung. Backend / Export
 * / DesignView lesen weiter colors.primary etc.
 */
import { useEffect, useState } from 'react';
import { ColorsSection, DeviceToggle, LivePreview, TypographySection, UIStylingSection } from '../styleguide/styleguideTeile';
import { KC_DARK } from '../styleguide/styleguideDaten';

const KC_MID = 'var(--kc-mid)';
const KC_YELLOW = 'var(--kc-yellow)';

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

const BUTTON_HIERARCHIES = [
  { id: 'standard',  label: 'Standard',  description: 'Solid Primary, Outline Secondary, Ghost Tertiary.' },
  { id: 'subtle',    label: 'Subtil',    description: 'Alle Buttons schlicht — flache Hierarchie für editorielle Sites.' },
  { id: 'prominent', label: 'Prominent', description: 'Sehr auffälliger Primary mit Schatten — Conversion-Sites.' },
];

const FORM_STYLES = [
  { id: 'outlined',   label: 'Outlined',       description: 'Klassisch — Border um Input, Label oberhalb.',   input_style: 'outlined',   label_pos: 'above' },
  { id: 'filled',     label: 'Filled',         description: 'Hellgrauer Background statt Border. Modern.',     input_style: 'filled',     label_pos: 'above' },
  { id: 'underlined', label: 'Underlined',     description: 'Nur unterer Border. Minimal, editorial.',         input_style: 'underlined', label_pos: 'above' },
  { id: 'floating',   label: 'Floating Label', description: 'Label springt beim Focus nach oben. Kompakt.',    input_style: 'outlined',   label_pos: 'floating' },
];

const CARD_VARIANTS = [
  { id: 'flat',           label: 'Flat',           description: 'Nur Hintergrund-Tint, kein Border, kein Shadow.', border_width: '0px', shadow: 'none' },
  { id: 'bordered',       label: 'Bordered',       description: '1px Border, kein Shadow.',                         border_width: '1px', shadow: 'none' },
  { id: 'elevated',       label: 'Elevated',       description: 'Schatten ohne starken Border.',                    border_width: '1px', shadow: '0 4px 14px rgba(0,0,0,0.08)' },
  { id: 'outlined_heavy', label: 'Outlined Heavy', description: '2px Border, kein Shadow.',                         border_width: '2px', shadow: 'none' },
];

const BADGE_STYLES = [
  { id: 'pill_filled',     label: 'Pill Filled',     description: 'Vollflächig gefärbt, rund.',         shape: 'pill',   fill: 'filled' },
  { id: 'pill_outlined',   label: 'Pill Outlined',   description: 'Rund mit transparentem Background.', shape: 'pill',   fill: 'outlined' },
  { id: 'square_filled',   label: 'Square Filled',   description: 'Kleiner Radius, gefüllt.',           shape: 'square', fill: 'filled' },
  { id: 'square_outlined', label: 'Square Outlined', description: 'Kleiner Radius, Outline.',           shape: 'square', fill: 'outlined' },
];

// ─────────────────────────────────────────────────────────────────────────────
// Defaults & Lookup
// ─────────────────────────────────────────────────────────────────────────────

const DEFAULT_CONCEPT     = COLOR_CONCEPTS[0];
const DEFAULT_TYPO        = TYPO_PAIRINGS[0];
const DEFAULT_UI          = UI_STYLES[0];
const DEFAULT_SPACING     = SPACING_SCALES[1];
const DEFAULT_BUTTON_HIER = BUTTON_HIERARCHIES[0];
const DEFAULT_FORM        = FORM_STYLES[0];
const DEFAULT_CARD        = CARD_VARIANTS[1];
const DEFAULT_BADGE       = BADGE_STYLES[0];

const findColorConcept = (id) => COLOR_CONCEPTS.find((c) => c.id === id) || DEFAULT_CONCEPT;
const findTypoPairing = (id) => TYPO_PAIRINGS.find((t) => t.id === id) || DEFAULT_TYPO;
const findUIStyle = (id) => UI_STYLES.find((u) => u.id === id) || DEFAULT_UI;
const findSpacingScale = (id) => SPACING_SCALES.find((s) => s.id === id) || DEFAULT_SPACING;
const findButtonHierarchy = (id) => BUTTON_HIERARCHIES.find((b) => b.id === id) || DEFAULT_BUTTON_HIER;
const findFormStyle = (id) => FORM_STYLES.find((f) => f.id === id) || DEFAULT_FORM;
const findCardVariant = (id) => CARD_VARIANTS.find((c) => c.id === id) || DEFAULT_CARD;
const findBadgeStyle = (id) => BADGE_STYLES.find((b) => b.id === id) || DEFAULT_BADGE;

const SEMANTIC_KEYS = ['success', 'warn', 'error', 'info'];

function effectivePalette(concept, lightDark, overrides) {
  const base = lightDark === 'dark' ? concept.dark : concept.light;
  const ovr = overrides?.[lightDark] || {};
  return { ...base, ...ovr };
}

function effectiveSemantic(lightDark, overrides) {
  const base = SEMANTIC_COLORS[lightDark === 'dark' ? 'dark' : 'light'];
  const ovr = overrides?.[lightDark] || {};
  const out = {};
  SEMANTIC_KEYS.forEach((k) => { out[k] = { ...base[k], ...(ovr[k] || {}) }; });
  return out;
}

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
  return {
    primary:     { bg: palette.accent_1, fg: palette.bg_primary, border: palette.accent_1, shadow: uiStyle.shadow },
    secondary:   { bg: 'transparent', fg: palette.accent_1, border: palette.accent_1, shadow: 'none' },
    tertiary:    { bg: 'transparent', fg: palette.text_primary, border: 'transparent', shadow: 'none' },
    destructive: { bg: semantic.error.fg, fg: '#fff', border: semantic.error.fg, shadow: 'none' },
  };
}

function deriveFormTokens(palette, uiStyle, formStyle) {
  return {
    style:        formStyle.input_style,
    label_pos:    formStyle.label_pos,
    radius:       uiStyle.button_radius,
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

function deriveBadgeTokens(badgeStyle, semantic, palette) {
  const radius = badgeStyle.shape === 'pill' ? '999px' : '4px';
  const map = {};
  SEMANTIC_KEYS.forEach((key) => {
    const c = semantic[key];
    map[key] = badgeStyle.fill === 'filled'
      ? { bg: c.fg, fg: '#fff', border: c.fg, radius }
      : { bg: 'transparent', fg: c.fg, border: c.fg, radius };
  });
  map.neutral = badgeStyle.fill === 'filled'
    ? { bg: palette.text_muted, fg: '#fff', border: palette.text_muted, radius }
    : { bg: 'transparent', fg: palette.text_muted, border: palette.text_muted, radius };
  return { ...map, shape: badgeStyle.shape, fill: badgeStyle.fill };
}

function deriveLegacyTokens(
  concept, lightDark, typoPairing, uiStyle, spacingScale, buttonHierarchy,
  formStyle, cardVariant, badgeStyle,
  paletteOverrides = null, semanticOverrides = null,
) {
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
    typography: { font_family: typoPairing.body, headline_size: 32, body_size: 14 },
    buttons:    { radius: uiStyle.button_radius, style: 'solid' },
    spacing: {
      radius: uiStyle.card_radius, section: spacingScale.section_y,
      base: spacingScale.base, scale: spacingScale.scale,
      container: spacingScale.container, gap: spacingScale.gap,
    },
    semantic,
    button_variants: buttonVariants,
    forms, card, badges,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Color helpers — Hex <-> HSL, Color-Scale Generator
// ─────────────────────────────────────────────────────────────────────────────

// Cycle helper für click-to-cycle Demo-Cards
function cycleNext(arr, currentId) {
  const i = arr.findIndex((x) => x.id === currentId);
  return arr[(i + 1) % arr.length].id;
}

const rand = (arr) => arr[Math.floor(Math.random() * arr.length)];

// ─────────────────────────────────────────────────────────────────────────────
// Main Component
// ─────────────────────────────────────────────────────────────────────────────

export default function StyleGuideView({ styleGuide, onChange, onApprove, approved }) {
  const conceptId = styleGuide?.color_concept_id || DEFAULT_CONCEPT.id;
  const lightDark = styleGuide?.light_dark || 'light';
  const typoId    = styleGuide?.typography_pairing_id || DEFAULT_TYPO.id;
  const uiId      = styleGuide?.ui_style_id || DEFAULT_UI.id;
  const spacingId = styleGuide?.spacing_scale_id || DEFAULT_SPACING.id;
  const btnHierId = styleGuide?.button_hierarchy_id || DEFAULT_BUTTON_HIER.id;
  const formId    = styleGuide?.form_style_id || DEFAULT_FORM.id;
  const cardId    = styleGuide?.card_variant_id || DEFAULT_CARD.id;
  const badgeId   = styleGuide?.badge_style_id || DEFAULT_BADGE.id;
  const fontScale = styleGuide?.font_scale || 'default';

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

  const palette        = effectivePalette(concept, lightDark, paletteOverrides);
  const semantic       = effectiveSemantic(lightDark, semanticOverrides);
  const buttonVariants = deriveButtonVariants(palette, uiStyle, buttonHier, semantic);
  const forms          = deriveFormTokens(palette, uiStyle, formStyle);
  const card           = deriveCardTokens(palette, uiStyle, cardVariant, spacingScale);
  const badges         = deriveBadgeTokens(badgeStyle, semantic, palette);

  const [previewDevice, setPreviewDevice] = useState('desktop');

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
      font_scale:            updates.fontScale  ?? fontScale,
      palette_overrides:     updates.paletteOverrides  ?? paletteOverrides,
      semantic_overrides:    updates.semanticOverrides ?? semanticOverrides,
    };
    const newConcept = findColorConcept(merged.color_concept_id);
    const newTypo    = findTypoPairing(merged.typography_pairing_id);
    const newUI      = findUIStyle(merged.ui_style_id);
    const newSpacing = findSpacingScale(merged.spacing_scale_id);
    const newBtnHier = findButtonHierarchy(merged.button_hierarchy_id);
    const newForm    = findFormStyle(merged.form_style_id);
    const newCard    = findCardVariant(merged.card_variant_id);
    const newBadge   = findBadgeStyle(merged.badge_style_id);
    const derived = deriveLegacyTokens(
      newConcept, merged.light_dark, newTypo, newUI, newSpacing, newBtnHier,
      newForm, newCard, newBadge,
      merged.palette_overrides, merged.semantic_overrides,
    );
    onChange?.({ ...merged, ...derived });
  };

  const setPaletteToken = (key, value) => {
    const next = {
      ...paletteOverrides,
      [lightDark]: { ...(paletteOverrides[lightDark] || {}), [key]: value },
    };
    updateSelection({ paletteOverrides: next });
  };

  const resetAllOverrides = () => {
    updateSelection({ paletteOverrides: {}, semanticOverrides: {} });
  };

  // Section-spezifisches Shuffle
  const shuffleColors = () => {
    updateSelection({ conceptId: rand(COLOR_CONCEPTS).id, paletteOverrides: {} });
  };
  const shuffleTypo = () => {
    updateSelection({ typoId: rand(TYPO_PAIRINGS).id });
  };
  const shuffleUi = () => {
    updateSelection({
      uiId:      rand(UI_STYLES).id,
      btnHierId: rand(BUTTON_HIERARCHIES).id,
      formId:    rand(FORM_STYLES).id,
      cardId:    rand(CARD_VARIANTS).id,
      badgeId:   rand(BADGE_STYLES).id,
    });
  };
  const shuffleAll = () => {
    updateSelection({
      conceptId: rand(COLOR_CONCEPTS).id,
      typoId:    rand(TYPO_PAIRINGS).id,
      uiId:      rand(UI_STYLES).id,
      spacingId: rand(SPACING_SCALES).id,
      btnHierId: rand(BUTTON_HIERARCHIES).id,
      formId:    rand(FORM_STYLES).id,
      cardId:    rand(CARD_VARIANTS).id,
      badgeId:   rand(BADGE_STYLES).id,
      paletteOverrides: {},
    });
  };

  // Keyboard-Shortcuts: C / T / U / SPACE
  useEffect(() => {
    const handler = (e) => {
      const tag = (e.target?.tagName || '').toLowerCase();
      if (tag === 'input' || tag === 'textarea' || tag === 'select') return;
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      const k = e.key.toLowerCase();
      if (k === 'c') { shuffleColors(); e.preventDefault(); }
      else if (k === 't') { shuffleTypo(); e.preventDefault(); }
      else if (k === 'u') { shuffleUi(); e.preventDefault(); }
      else if (e.code === 'Space') { shuffleAll(); e.preventDefault(); }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conceptId, typoId, uiId, btnHierId, formId, cardId, badgeId, spacingId, lightDark]);

  return (
    <div style={{
      display: 'flex', flexDirection: 'column',
      height: '100%', background: 'var(--bg-app)',
      fontFamily: 'var(--font-sans, system-ui)',
    }}>
      {/* Topbar — minimal, Freigabe rechts */}
      <div style={{
        flexShrink: 0,
        padding: '12px 24px',
        background: '#fff',
        borderBottom: '1px solid var(--border-light)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        gap: 16, flexWrap: 'wrap',
      }}>
        <div>
          <h1 style={{
            fontSize: 18, fontWeight: 900, color: KC_DARK, margin: 0,
            textTransform: 'uppercase', letterSpacing: '-0.02em',
          }}>Style Guide</h1>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>
            Farben, Typografie, UI — links wählen, rechts Live-Preview.
          </div>
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          {approved && (
            <span style={{
              fontSize: 12, fontWeight: 700, color: '#1D9E75', background: '#D1FAE5',
              padding: '4px 10px', borderRadius: 12, textTransform: 'uppercase',
            }}>✓ Vom Kunden freigegeben</span>
          )}
          <button type="button" onClick={onApprove} disabled={approved}
            style={{
              background: approved ? 'var(--border-medium)' : KC_YELLOW,
              color: '#000', border: 'none', borderRadius: 8,
              padding: '8px 16px', fontSize: 12, fontWeight: 800,
              cursor: approved ? 'default' : 'pointer',
              textTransform: 'uppercase', letterSpacing: '0.04em',
              fontFamily: 'inherit',
            }}>
            {approved ? 'Bereits freigegeben' : 'Freigabe an Kunden'}
          </button>
        </div>
      </div>

      {/* Body — 2 Spalten: Editor links, Live-Preview rechts */}
      <div style={{ flex: 1, display: 'flex', minHeight: 0, overflow: 'hidden' }}>
        {/* Editor — Single-Column, scrollbar */}
        <div style={{
          flex: '0 0 640px',
          overflowY: 'auto', padding: '20px 24px 96px',
          background: '#fff',
          borderRight: '1px solid var(--border-light)',
        }}>
          <ColorsSection
            palette={palette}
            lightDark={lightDark}
            onTogglelightDark={() => updateSelection({ lightDark: lightDark === 'dark' ? 'light' : 'dark' })}
            onShuffle={shuffleColors}
            onSetToken={setPaletteToken}
            onResetAll={resetAllOverrides}
          />

          <TypographySection
            typoPairing={typoPairing}
            fontScale={fontScale}
            onScaleChange={(v) => updateSelection({ fontScale: v })}
            onShuffle={shuffleTypo}
          />

          <UIStylingSection
            palette={palette}
            uiStyle={uiStyle}
            cardVariant={cardVariant}
            buttonVariants={buttonVariants}
            typo={typoPairing}
            forms={forms}
            card={card}
            onCycleUi={() => updateSelection({ uiId: cycleNext(UI_STYLES, uiId) })}
            onCycleCard={() => updateSelection({ cardId: cycleNext(CARD_VARIANTS, cardId) })}
            onShuffle={shuffleUi}
          />
        </div>

        {/* Live-Preview rechts — Device-aware */}
        <div style={{
          flex: '1 1 auto', minWidth: 480,
          overflowY: 'auto',
          background: 'var(--surface)',
          padding: 20,
          display: 'flex', flexDirection: 'column',
          position: 'relative',
        }}>
          <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-secondary)',
            textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8 }}>
            Live-Preview
          </div>
          <div style={{
            flex: 1,
            display: 'flex', justifyContent: 'center',
            paddingBottom: 60,
          }}>
            <div style={{
              width: '100%',
              maxWidth: previewDevice === 'mobile' ? 390
                       : previewDevice === 'tablet' ? 820
                       : '100%',
              transition: 'max-width 0.25s ease',
            }}>
              <LivePreview
                palette={palette} typo={typoPairing} ui={uiStyle}
                spacing={spacingScale} variants={buttonVariants} semantic={semantic}
                forms={forms} card={card} badges={badges} fontScale={fontScale}
                device={previewDevice}
              />
            </div>
          </div>
          <DeviceToggle device={previewDevice} onChange={setPreviewDevice} />
        </div>
      </div>

      {/* Footer — Scheme shuffle */}
      <div style={{
        flexShrink: 0,
        background: '#fff', borderTop: '1px solid var(--border-light)',
        padding: '8px 24px',
        display: 'flex', justifyContent: 'center',
      }}>
        <button type="button" onClick={shuffleAll}
          style={{
            background: 'transparent', color: KC_MID,
            border: `1.5px solid ${KC_MID}`, borderRadius: 8,
            padding: '8px 16px', fontSize: 12, fontWeight: 700,
            cursor: 'pointer', fontFamily: 'inherit',
            display: 'flex', alignItems: 'center', gap: 10,
          }}>
          <span>🎲 Scheme shuffle</span>
          <span style={{
            background: 'var(--info-bg)', color: KC_MID,
            padding: '2px 8px', borderRadius: 4,
            fontSize: 10, fontWeight: 800, letterSpacing: '0.04em',
          }}>SPACE</span>
        </button>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// ─────────────────────────────────────────────────────────────────────────────

